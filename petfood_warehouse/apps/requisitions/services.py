"""
services.py — ตรรกะธุรกิจหลักของระบบคำร้องขอเบิกสินค้า

กฎสำคัญ:
- ตัดสต็อกคลังกลางเฉพาะตอนอนุมัติเท่านั้น
- ใช้ transaction.atomic() + select_for_update() ป้องกัน race condition
- ปฏิเสธ/ยกเลิก ห้ามแตะสต็อก
"""
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.inventory.models import CentralStock, BranchStock, StockMovement
from .models import RequisitionRequest, RequisitionItem


@transaction.atomic
def approve_request(request_id: int, admin_user, approved_map: dict) -> RequisitionRequest:
    """
    อนุมัติคำร้อง — ตัดสต็อกคลังกลาง + บวกสต็อกสาขา

    Args:
        request_id: ID ของ RequisitionRequest
        admin_user: User ที่มีสิทธิ์ ADMIN
        approved_map: dict {item_id: qty_approved}  หรือ {} เพื่ออนุมัติตามที่ขอทั้งหมด

    Returns:
        RequisitionRequest ที่อัพเดตแล้ว

    Raises:
        ValidationError: ถ้าสต็อกไม่พอ, คำร้องไม่ใช่ PENDING, หรือสิทธิ์ไม่ถูกต้อง
    """
    # ตรวจสิทธิ์
    if not admin_user.is_admin:
        raise ValidationError('เฉพาะผู้ดูแลระบบเท่านั้นที่อนุมัติได้')

    # ล็อคแถว request ก่อน
    req = RequisitionRequest.objects.select_for_update().get(pk=request_id)

    if req.status != RequisitionRequest.Status.PENDING:
        raise ValidationError(f'คำร้องนี้ถูกดำเนินการไปแล้ว (สถานะ: {req.get_status_display()})')

    items = list(req.items.select_related('product').order_by('product_id'))

    if not items:
        raise ValidationError('คำร้องนี้ไม่มีรายการสินค้า')

    # กำหนดจำนวนที่จะอนุมัติ
    approval_plan = {}
    for item in items:
        qty = approved_map.get(item.id, item.qty_requested)
        if qty is None:
            qty = item.qty_requested
        qty = int(qty)
        if qty < 0:
            raise ValidationError(f'จำนวนที่อนุมัติของ {item.product.name} ต้องไม่ติดลบ')
        if qty > item.qty_requested:
            raise ValidationError(
                f'จำนวนที่อนุมัติ ({qty}) ของ {item.product.name} '
                f'เกินจำนวนที่ขอ ({item.qty_requested})'
            )
        approval_plan[item.id] = qty

    # ล็อคแถวสต็อกทุกสินค้าในคำร้อง (เรียงตาม product_id ป้องกัน deadlock)
    product_ids = sorted(set(item.product_id for item in items))
    stocks = {
        s.product_id: s
        for s in CentralStock.objects.select_for_update().filter(product_id__in=product_ids)
    }

    # ตรวจสต็อกพอไหม
    errors = []
    for item in items:
        qty_to_issue = approval_plan[item.id]
        if qty_to_issue == 0:
            continue
        stock = stocks.get(item.product_id)
        if not stock or stock.quantity < qty_to_issue:
            current = stock.quantity if stock else 0
            errors.append(
                f'{item.product.name}: ต้องการ {qty_to_issue} {item.product.unit} '
                f'แต่คลังกลางเหลือ {current} {item.product.unit}'
            )
    if errors:
        raise ValidationError('สต็อกคลังกลางไม่เพียงพอ:\n' + '\n'.join(errors))

    # ตัดสต็อก + สร้าง StockMovement + บวก BranchStock
    total_approved = 0
    for item in items:
        qty_to_issue = approval_plan[item.id]
        item.qty_approved = qty_to_issue
        item.save(update_fields=['qty_approved'])

        if qty_to_issue == 0:
            continue

        # ตัดสต็อกคลังกลาง
        stock = stocks[item.product_id]
        stock.quantity -= qty_to_issue
        stock.save(update_fields=['quantity'])

        # บันทึก StockMovement
        StockMovement.objects.create(
            product=item.product,
            movement_type=StockMovement.MovementType.ISSUE,
            qty_change=-qty_to_issue,
            balance_after=stock.quantity,
            request=req,
            by_user=admin_user,
            note=f'อนุมัติคำร้อง {req.code} สาขา {req.branch.name}',
        )

        # บวก BranchStock
        branch_stock, _ = BranchStock.objects.get_or_create(
            branch=req.branch, product=item.product,
            defaults={'quantity': 0}
        )
        BranchStock.objects.filter(pk=branch_stock.pk).update(
            quantity=branch_stock.quantity + qty_to_issue
        )

        total_approved += qty_to_issue

    # อัพเดตสถานะคำร้อง
    total_requested = sum(item.qty_requested for item in items)
    if total_approved == 0:
        # อนุมัติ 0 ทุกรายการ → ถือว่าปฏิเสธ
        req.status = RequisitionRequest.Status.REJECTED
        req.reject_reason = 'อนุมัติจำนวน 0 ทุกรายการ'
    elif total_approved < total_requested:
        req.status = RequisitionRequest.Status.PARTIAL
    else:
        req.status = RequisitionRequest.Status.APPROVED

    req.decided_by = admin_user
    req.decided_at = timezone.now()
    req.save(update_fields=['status', 'decided_by', 'decided_at', 'reject_reason'])

    return req


@transaction.atomic
def reject_request(request_id: int, admin_user, reason: str = '') -> RequisitionRequest:
    """
    ปฏิเสธคำร้อง — ไม่แตะสต็อกเลย
    """
    if not admin_user.is_admin:
        raise ValidationError('เฉพาะผู้ดูแลระบบเท่านั้นที่ปฏิเสธได้')

    req = RequisitionRequest.objects.select_for_update().get(pk=request_id)
    if req.status != RequisitionRequest.Status.PENDING:
        raise ValidationError(f'คำร้องนี้ถูกดำเนินการไปแล้ว (สถานะ: {req.get_status_display()})')

    req.status = RequisitionRequest.Status.REJECTED
    req.reject_reason = reason
    req.decided_by = admin_user
    req.decided_at = timezone.now()
    req.save(update_fields=['status', 'reject_reason', 'decided_by', 'decided_at'])

    return req


@transaction.atomic
def cancel_request(request_id: int, requester_user) -> RequisitionRequest:
    """
    ผู้ยื่นคำร้องยกเลิกคำร้องของตัวเอง (เฉพาะ PENDING)
    """
    req = RequisitionRequest.objects.select_for_update().get(pk=request_id)

    if req.requested_by_id != requester_user.id and not requester_user.is_admin:
        raise ValidationError('คุณไม่มีสิทธิ์ยกเลิกคำร้องนี้')

    if req.status != RequisitionRequest.Status.PENDING:
        raise ValidationError('ยกเลิกได้เฉพาะคำร้องที่สถานะ "รออนุมัติ" เท่านั้น')

    req.status = RequisitionRequest.Status.CANCELLED
    req.decided_at = timezone.now()
    req.save(update_fields=['status', 'decided_at'])

    return req


@transaction.atomic
def receive_stock(product_id: int, quantity: int, admin_user, note: str = '') -> CentralStock:
    """
    รับสินค้าเข้าคลังกลาง
    """
    if not admin_user.is_admin:
        raise ValidationError('เฉพาะผู้ดูแลระบบเท่านั้นที่รับสินค้าเข้าได้')
    if quantity <= 0:
        raise ValidationError('จำนวนที่รับต้องมากกว่า 0')

    stock = CentralStock.objects.select_for_update().get(product_id=product_id)
    stock.quantity += quantity
    stock.save(update_fields=['quantity'])

    StockMovement.objects.create(
        product=stock.product,
        movement_type=StockMovement.MovementType.RECEIVE,
        qty_change=+quantity,
        balance_after=stock.quantity,
        request=None,
        by_user=admin_user,
        note=note or f'รับสินค้าเข้าคลังกลาง',
    )

    return stock


@transaction.atomic
def issue_stock(product_id: int, quantity: int, admin_user, note: str = '') -> CentralStock:
    """
    ตัดจ่ายสินค้าออกจากคลังกลางโดยตรง (เช่น สินค้าชำรุด, เสียหาย, เบิกใช้ภายใน)
    """
    if not admin_user.is_admin:
        raise ValidationError('เฉพาะผู้ดูแลระบบเท่านั้นที่ตัดจ่ายสินค้าได้')
    if quantity <= 0:
        raise ValidationError('จำนวนที่ตัดต้องมากกว่า 0')

    stock = CentralStock.objects.select_for_update().get(product_id=product_id)
    if stock.quantity < quantity:
        raise ValidationError(f'สต็อกไม่เพียงพอ (มีอยู่ {stock.quantity} {stock.product.unit})')

    stock.quantity -= quantity
    stock.save(update_fields=['quantity'])

    StockMovement.objects.create(
        product=stock.product,
        movement_type=StockMovement.MovementType.ISSUE,
        qty_change=-quantity,
        balance_after=stock.quantity,
        request=None,
        by_user=admin_user,
        note=note or 'ตัดจ่ายสินค้าออกจากคลังกลาง',
    )

    return stock
