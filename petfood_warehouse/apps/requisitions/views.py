from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q

from apps.inventory.models import Product, CentralStock, Category
from .models import RequisitionRequest, RequisitionItem
from .services import approve_request, reject_request, cancel_request


def admin_required(view_func):
    from functools import wraps

    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
def request_list(request):
    """รายการคำร้องทั้งหมด"""
    user = request.user
    qs = RequisitionRequest.objects.select_related(
        'branch', 'requested_by', 'decided_by'
    ).prefetch_related('items')

    if user.is_requester:
        if not user.branch:
            raise PermissionDenied
        qs = qs.filter(branch=user.branch)

    # กรอง
    status_filter = request.GET.get('status', '')
    branch_filter = request.GET.get('branch', '')
    q = request.GET.get('q', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if branch_filter and user.is_admin:
        qs = qs.filter(branch_id=branch_filter)
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(requested_by__username__icontains=q))

    from apps.accounts.models import Branch
    branches = Branch.objects.filter(is_active=True) if user.is_admin else []

    context = {
        'requests': qs[:100],
        'status_choices': RequisitionRequest.Status.choices,
        'status_filter': status_filter,
        'branch_filter': branch_filter,
        'branches': branches,
        'q': q,
    }
    return render(request, 'requisitions/request_list.html', context)


@login_required
def request_detail(request, pk):
    """รายละเอียดคำร้อง"""
    user = request.user
    req = get_object_or_404(
        RequisitionRequest.objects.select_related('branch', 'requested_by', 'decided_by')
        .prefetch_related('items__product', 'items__product__central_stock'),
        pk=pk
    )

    # ตรวจสิทธิ์: requester เห็นเฉพาะของสาขาตัวเอง
    if user.is_requester and req.branch_id != user.branch_id:
        raise PermissionDenied

    items_data = []
    for item in req.items.all():
        cs = getattr(item.product, 'central_stock', None)
        avail = cs.quantity if cs else 0
        is_short = avail < item.qty_requested
        suggested = min(item.qty_requested, avail)
        items_data.append({
            'item': item,
            'central_stock': cs,
            'available': avail,
            'is_short': is_short,
            'suggested': suggested,
        })

    context = {
        'req': req,
        'items_data': items_data,
    }
    return render(request, 'requisitions/request_detail.html', context)


@login_required
def create_request(request):
    """ยื่นคำร้องเบิกสินค้า (ผู้ยื่นคำร้อง)"""
    user = request.user
    if user.is_admin:
        messages.info(request, 'ผู้ดูแลระบบไม่ต้องยื่นคำร้อง')
        return redirect('home')

    if not user.branch:
        messages.error(request, 'บัญชีของคุณยังไม่ได้ผูกกับสาขา กรุณาติดต่อผู้ดูแล')
        return redirect('home')

    stocks = CentralStock.objects.select_related(
        'product', 'product__category'
    ).filter(product__is_active=True).order_by('product__category__name', 'product__name')
    categories = Category.objects.all()

    if request.method == 'POST':
        # อ่าน qty_{product_id} จาก form
        items_data = []
        for key, val in request.POST.items():
            if key.startswith('qty_') and val.strip():
                try:
                    product_id = int(key[4:])
                    qty = int(val)
                    if qty > 0:
                        items_data.append((product_id, qty))
                except (ValueError, TypeError):
                    pass

        if not items_data:
            messages.error(request, 'กรุณาระบุสินค้าและจำนวนอย่างน้อย 1 รายการ')
        else:
            note = request.POST.get('note', '')
            req = RequisitionRequest.objects.create(
                branch=user.branch,
                requested_by=user,
                note=note,
            )
            for product_id, qty in items_data:
                try:
                    product = Product.objects.get(pk=product_id, is_active=True)
                    RequisitionItem.objects.create(
                        request=req, product=product, qty_requested=qty
                    )
                except Product.DoesNotExist:
                    pass

            messages.success(request, f'ยื่นคำร้อง {req.code} เรียบร้อยแล้ว กำลังรออนุมัติ')
            return redirect('requisitions:detail', pk=req.pk)

    context = {
        'stocks': stocks,
        'categories': categories,
    }
    return render(request, 'requisitions/create_request.html', context)


@admin_required
def approve_view(request, pk):
    """อนุมัติคำร้อง (admin)"""
    req = get_object_or_404(RequisitionRequest, pk=pk)
    if req.status != 'PENDING':
        messages.warning(request, f'คำร้องนี้ไม่ใช่สถานะรออนุมัติ ({req.get_status_display()})')
        return redirect('requisitions:detail', pk=pk)

    if request.method == 'POST':
        # อ่านจำนวนที่อนุมัติ
        approved_map = {}
        for item in req.items.all():
            key = f'approved_{item.id}'
            val = request.POST.get(key)
            if val is not None:
                try:
                    approved_map[item.id] = int(val)
                except ValueError:
                    pass

        try:
            updated = approve_request(pk, request.user, approved_map)
            messages.success(request, f'อนุมัติคำร้อง {updated.code} เรียบร้อยแล้ว')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('requisitions:detail', pk=pk)

    items_with_stock = []
    for item in req.items.select_related('product', 'product__central_stock'):
        try:
            cs = item.product.central_stock
        except Exception:
            cs = None
        items_with_stock.append({'item': item, 'central_stock': cs})

    return render(request, 'requisitions/approve.html', {
        'req': req,
        'items_with_stock': items_with_stock,
    })


@admin_required
def reject_view(request, pk):
    """ปฏิเสธคำร้อง (admin)"""
    req = get_object_or_404(RequisitionRequest, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'กรุณาระบุเหตุผลในการปฏิเสธ')
        else:
            try:
                reject_request(pk, request.user, reason)
                messages.success(request, f'ปฏิเสธคำร้อง {req.code} แล้ว')
                return redirect('requisitions:detail', pk=pk)
            except ValidationError as e:
                messages.error(request, str(e))

    return render(request, 'requisitions/reject.html', {'req': req})


@login_required
def cancel_view(request, pk):
    """ยกเลิกคำร้อง"""
    user = request.user
    req = get_object_or_404(RequisitionRequest, pk=pk)

    # ตรวจสิทธิ์
    if user.is_requester and req.branch_id != user.branch_id:
        raise PermissionDenied

    if request.method == 'POST':
        try:
            cancel_request(pk, user)
            messages.success(request, f'ยกเลิกคำร้อง {req.code} แล้ว')
        except ValidationError as e:
            messages.error(request, str(e))
        return redirect('requisitions:list')

    return render(request, 'requisitions/cancel_confirm.html', {'req': req})
