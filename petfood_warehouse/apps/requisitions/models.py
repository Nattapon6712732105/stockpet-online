import datetime
from django.db import models
from django.utils import timezone


def generate_request_code():
    """สร้างรหัสคำร้อง REQ-{พ.ศ.}-{running_number:04d}"""
    year_be = timezone.now().year + 543
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    count = RequisitionRequest.objects.filter(created_at__gte=today_start).count() + 1
    return f'REQ-{year_be}-{count:04d}'


class RequisitionRequest(models.Model):
    """คำร้องขอเบิกสินค้า"""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'รออนุมัติ'
        APPROVED = 'APPROVED', 'อนุมัติแล้ว'
        PARTIAL = 'PARTIAL', 'อนุมัติบางส่วน'
        REJECTED = 'REJECTED', 'ปฏิเสธ'
        CANCELLED = 'CANCELLED', 'ยกเลิก'

    code = models.CharField(max_length=30, unique=True, verbose_name='รหัสคำร้อง')
    branch = models.ForeignKey(
        'accounts.Branch', on_delete=models.PROTECT, verbose_name='สาขา'
    )
    requested_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='my_requests',
        verbose_name='ผู้ยื่นคำร้อง',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING, verbose_name='สถานะ'
    )
    note = models.TextField(blank=True, verbose_name='หมายเหตุ')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่ยื่น')
    decided_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='decided_requests',
        verbose_name='ผู้ตัดสินใจ',
    )
    decided_at = models.DateTimeField(null=True, blank=True, verbose_name='วันที่ตัดสินใจ')
    reject_reason = models.TextField(blank=True, verbose_name='เหตุผลปฏิเสธ')

    class Meta:
        verbose_name = 'คำร้องขอเบิก'
        verbose_name_plural = 'คำร้องขอเบิก'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.get_status_display()})'

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = generate_request_code()
        super().save(*args, **kwargs)

    @property
    def is_pending(self):
        return self.status == self.Status.PENDING

    @property
    def status_color(self):
        return {
            'PENDING': 'info',
            'APPROVED': 'ok',
            'PARTIAL': 'warn',
            'REJECTED': 'danger',
            'CANCELLED': 'secondary',
        }.get(self.status, 'secondary')


class RequisitionItem(models.Model):
    """รายการสินค้าในคำร้อง"""
    request = models.ForeignKey(
        RequisitionRequest, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey('inventory.Product', on_delete=models.PROTECT, verbose_name='สินค้า')
    qty_requested = models.PositiveIntegerField(verbose_name='จำนวนที่ขอ')
    qty_approved = models.PositiveIntegerField(null=True, blank=True, verbose_name='จำนวนที่อนุมัติ')

    class Meta:
        verbose_name = 'รายการในคำร้อง'
        verbose_name_plural = 'รายการในคำร้อง'
        unique_together = [['request', 'product']]

    def __str__(self):
        return f'{self.request.code} / {self.product.name} x{self.qty_requested}'
