"""
Unit tests สำหรับ services.py — ตรรกะอนุมัติ/ปฏิเสธ/ยกเลิก/รับเข้า
ครอบคลุมทุกกรณีตาม Skill checklist
"""
from django.test import TestCase
from django.core.exceptions import ValidationError

from apps.accounts.models import User, Branch
from apps.inventory.models import Category, Product, CentralStock, BranchStock, StockMovement
from apps.requisitions.models import RequisitionRequest, RequisitionItem
from apps.requisitions.services import approve_request, reject_request, cancel_request, receive_stock


def _setup_base():
    """ข้อมูลพื้นฐานสำหรับทดสอบ"""
    branch = Branch.objects.create(name='สาขาทดสอบ', code='TEST')
    admin = User.objects.create_user(
        username='admin_test', password='pass', role=User.Role.ADMIN
    )
    requester = User.objects.create_user(
        username='req_test', password='pass', role=User.Role.REQUESTER, branch=branch
    )
    cat = Category.objects.create(name='อาหารสุนัข')
    product = Product.objects.create(sku='DOG-001', name='อาหารหมา A', category=cat, unit='ถุง', min_stock=5)
    stock = CentralStock.objects.create(product=product, quantity=100)
    return branch, admin, requester, product, stock


def _make_request(branch, requester, product, qty):
    req = RequisitionRequest.objects.create(
        branch=branch, requested_by=requester, note=''
    )
    item = RequisitionItem.objects.create(request=req, product=product, qty_requested=qty)
    return req, item


class ApproveRequestTest(TestCase):
    def setUp(self):
        self.branch, self.admin, self.requester, self.product, self.stock = _setup_base()

    def test_approve_full_decreases_stock_correctly(self):
        """อนุมัติแล้วสต็อกลดถูกต้อง"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=10)
        approve_request(req.id, self.admin, {})

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 90)

        req.refresh_from_db()
        self.assertEqual(req.status, RequisitionRequest.Status.APPROVED)

        mov = StockMovement.objects.filter(request=req).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.qty_change, -10)
        self.assertEqual(mov.balance_after, 90)

    def test_insufficient_stock_does_not_cut(self):
        """สต็อกไม่พอแล้วไม่ตัด"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=200)
        with self.assertRaises(ValidationError):
            approve_request(req.id, self.admin, {})

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 100)  # ไม่เปลี่ยน

        req.refresh_from_db()
        self.assertEqual(req.status, RequisitionRequest.Status.PENDING)  # ยังเป็น PENDING

    def test_double_approve_raises_error(self):
        """อนุมัติซ้ำไม่ได้"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=10)
        approve_request(req.id, self.admin, {})
        with self.assertRaises((ValidationError, RequisitionRequest.DoesNotExist)):
            approve_request(req.id, self.admin, {})

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 90)  # ตัดแค่ครั้งเดียว

    def test_reject_does_not_cut_stock(self):
        """ปฏิเสธไม่ตัดสต็อก"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=10)
        reject_request(req.id, self.admin, reason='ของหมด')

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 100)  # ไม่เปลี่ยน

        req.refresh_from_db()
        self.assertEqual(req.status, RequisitionRequest.Status.REJECTED)
        self.assertEqual(req.reject_reason, 'ของหมด')

    def test_partial_approve(self):
        """อนุมัติบางส่วน"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=10)
        approve_request(req.id, self.admin, {item.id: 5})

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 95)

        req.refresh_from_db()
        self.assertEqual(req.status, RequisitionRequest.Status.PARTIAL)

        item.refresh_from_db()
        self.assertEqual(item.qty_approved, 5)

    def test_requester_cannot_approve(self):
        """ผู้ยื่นคำร้องไม่มีสิทธิ์อนุมัติ"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=10)
        with self.assertRaises(ValidationError):
            approve_request(req.id, self.requester, {})

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 100)

    def test_branch_stock_increases_on_approve(self):
        """สต็อกสาขาเพิ่มขึ้นเมื่ออนุมัติ"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=15)
        approve_request(req.id, self.admin, {})

        bs = BranchStock.objects.get(branch=self.branch, product=self.product)
        self.assertEqual(bs.quantity, 15)

    def test_cancel_pending_request(self):
        """ผู้ยื่นคำร้องยกเลิกคำร้อง PENDING ได้"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=5)
        cancel_request(req.id, self.requester)

        req.refresh_from_db()
        self.assertEqual(req.status, RequisitionRequest.Status.CANCELLED)

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 100)  # ไม่แตะสต็อก

    def test_cancel_approved_request_raises(self):
        """ยกเลิกคำร้องที่อนุมัติไปแล้วไม่ได้"""
        req, item = _make_request(self.branch, self.requester, self.product, qty=5)
        approve_request(req.id, self.admin, {})
        with self.assertRaises(ValidationError):
            cancel_request(req.id, self.requester)

    def test_receive_stock(self):
        """รับสินค้าเข้าคลังกลาง"""
        from apps.requisitions.services import receive_stock
        receive_stock(self.product.id, 50, self.admin, note='รับของจากซัพพลายเออร์')

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 150)

        mov = StockMovement.objects.filter(
            product=self.product, movement_type=StockMovement.MovementType.RECEIVE
        ).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.qty_change, 50)
        self.assertEqual(mov.balance_after, 150)

    def test_issue_stock(self):
        """ตัดจ่ายสินค้าออกจากคลังกลาง"""
        from apps.requisitions.services import issue_stock
        issue_stock(self.product.id, 20, self.admin, note='สินค้าชำรุด')

        self.stock.refresh_from_db()
        self.assertEqual(self.stock.quantity, 80)

        mov = StockMovement.objects.filter(
            product=self.product, movement_type=StockMovement.MovementType.ISSUE
        ).first()
        self.assertIsNotNone(mov)
        self.assertEqual(mov.qty_change, -20)
        self.assertEqual(mov.balance_after, 80)

    def test_issue_stock_exceeds_available(self):
        """ตัดจ่ายสินค้าเกินสต็อกที่มีต้อง raise ValidationError"""
        from apps.requisitions.services import issue_stock
        with self.assertRaises(ValidationError):
            issue_stock(self.product.id, 500, self.admin, note='เกินสต็อก')
