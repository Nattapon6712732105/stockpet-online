from django.db import models


class Category(models.Model):
    """หมวดหมู่สินค้า"""
    name = models.CharField(max_length=100, verbose_name='ชื่อหมวด')

    class Meta:
        verbose_name = 'หมวดหมู่'
        verbose_name_plural = 'หมวดหมู่'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """สินค้า (ตารางกลางใช้ร่วมทุกสาขา)"""
    sku = models.CharField(max_length=50, unique=True, verbose_name='รหัสสินค้า')
    name = models.CharField(max_length=200, verbose_name='ชื่อสินค้า')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name='หมวด')
    unit = models.CharField(max_length=30, verbose_name='หน่วยนับ', help_text='เช่น กระสอบ, ถุง, ชิ้น')
    image = models.ImageField(upload_to='products/', null=True, blank=True, verbose_name='รูปสินค้า')
    min_stock = models.PositiveIntegerField(default=0, verbose_name='จุดสั่งซื้อ (ใกล้หมด)')
    is_active = models.BooleanField(default=True, verbose_name='ใช้งาน')

    class Meta:
        verbose_name = 'สินค้า'
        verbose_name_plural = 'สินค้า'
        ordering = ['category', 'name']

    def __str__(self):
        return f'[{self.sku}] {self.name}'


class CentralStock(models.Model):
    """สต็อกคลังกลาง (1 แถวต่อ 1 สินค้า)"""
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='central_stock')
    quantity = models.PositiveIntegerField(default=0, verbose_name='คงเหลือ')

    class Meta:
        verbose_name = 'สต็อกคลังกลาง'
        verbose_name_plural = 'สต็อกคลังกลาง'

    def __str__(self):
        return f'{self.product.name}: {self.quantity} {self.product.unit}'

    @property
    def status(self):
        """สถานะสต็อก: OK / WARN / EMPTY"""
        if self.quantity == 0:
            return 'EMPTY'
        if self.quantity <= self.product.min_stock:
            return 'WARN'
        return 'OK'

    @property
    def status_display(self):
        return {'OK': 'ปกติ', 'WARN': 'ใกล้หมด', 'EMPTY': 'หมด'}.get(self.status, '')


class BranchStock(models.Model):
    """สต็อกสาขา (เพิ่มเมื่ออนุมัติคำร้อง)"""
    branch = models.ForeignKey('accounts.Branch', on_delete=models.CASCADE, verbose_name='สาขา')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='สินค้า')
    quantity = models.PositiveIntegerField(default=0, verbose_name='คงเหลือ')

    class Meta:
        verbose_name = 'สต็อกสาขา'
        verbose_name_plural = 'สต็อกสาขา'
        unique_together = [['branch', 'product']]

    def __str__(self):
        return f'{self.branch} / {self.product.name}: {self.quantity}'


class StockMovement(models.Model):
    """ประวัติการเคลื่อนไหวสต็อกคลังกลาง"""

    class MovementType(models.TextChoices):
        RECEIVE = 'RECEIVE', 'รับเข้า'
        ISSUE = 'ISSUE', 'เบิกออก'
        ADJUST = 'ADJUST', 'ปรับปรุง'

    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='สินค้า')
    movement_type = models.CharField(
        max_length=10, choices=MovementType.choices, verbose_name='ประเภท'
    )
    qty_change = models.IntegerField(verbose_name='จำนวนเปลี่ยนแปลง (+/-)')
    balance_after = models.PositiveIntegerField(verbose_name='คงเหลือหลังทำรายการ')
    request = models.ForeignKey(
        'requisitions.RequisitionRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='อ้างอิงคำร้อง',
    )
    by_user = models.ForeignKey(
        'accounts.User', on_delete=models.PROTECT, verbose_name='ทำโดย'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='วันที่')
    note = models.TextField(blank=True, verbose_name='หมายเหตุ')

    class Meta:
        verbose_name = 'ประวัติสต็อก'
        verbose_name_plural = 'ประวัติสต็อก'
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.qty_change >= 0 else ''
        return f'{self.get_movement_type_display()} {self.product.name} {sign}{self.qty_change}'
