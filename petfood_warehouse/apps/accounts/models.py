from django.contrib.auth.models import AbstractUser
from django.db import models


class Branch(models.Model):
    """สาขาของร้าน"""
    name = models.CharField(max_length=100, verbose_name='ชื่อสาขา')
    code = models.CharField(max_length=20, unique=True, verbose_name='รหัสสาขา')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')

    class Meta:
        verbose_name = 'สาขา'
        verbose_name_plural = 'สาขา'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.name}'


class User(AbstractUser):
    """ผู้ใช้งานระบบ"""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'ผู้ดูแลระบบ'
        REQUESTER = 'REQUESTER', 'ผู้ยื่นคำร้อง'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.REQUESTER,
        verbose_name='บทบาท',
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='สาขา',
        help_text='สาขาที่ผูกกับผู้ยื่นคำร้อง (admin ไม่ต้องระบุ)',
    )

    class Meta:
        verbose_name = 'ผู้ใช้งาน'
        verbose_name_plural = 'ผู้ใช้งาน'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_requester(self):
        return self.role == self.Role.REQUESTER
