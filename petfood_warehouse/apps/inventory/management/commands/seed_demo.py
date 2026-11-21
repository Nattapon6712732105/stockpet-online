"""
seed_demo — สร้างข้อมูลตัวอย่างสำหรับทดสอบระบบ

usage: python manage.py seed_demo
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'สร้างข้อมูลตัวอย่าง: 3 สาขา, 4 หมวด, 20 สินค้า, ผู้ดูแล 1 คน, ผู้ยื่นคำร้อง 3 คน'

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.accounts.models import User, Branch
        from apps.inventory.models import Category, Product, CentralStock

        self.stdout.write('🌱 กำลังสร้างข้อมูลตัวอย่าง...')

        # สาขา
        branches_data = [
            ('สาขาตลาดขุขันธ์', 'KK-01'),
            ('สาขาห้วยเหนือ', 'KK-02'),
            ('สาขาปรือใหญ่', 'KK-03'),
        ]
        branches = []
        for name, code in branches_data:
            b, _ = Branch.objects.get_or_create(code=code, defaults={'name': name})
            branches.append(b)
            self.stdout.write(f'  ✅ สาขา: {name}')

        # หมวดหมู่
        cats_data = ['อาหารสุนัข', 'อาหารแมว', 'อาหารเสริมสัตว์', 'อุปกรณ์สัตว์เลี้ยง']
        cats = {}
        for cat_name in cats_data:
            c, _ = Category.objects.get_or_create(name=cat_name)
            cats[cat_name] = c

        # สินค้า
        products_data = [
            # (sku, name, category, unit, min_stock, qty)
            ('DOG-001', 'Royal Canin Medium Adult 15kg', 'อาหารสุนัข', 'ถุง', 10, 50),
            ('DOG-002', 'Pedigree Adult Beef 8kg', 'อาหารสุนัข', 'ถุง', 15, 80),
            ('DOG-003', 'SmartHeart Gold Puppy 1.5kg', 'อาหารสุนัข', 'ถุง', 20, 60),
            ('DOG-004', 'Hills Science Diet Adult 7.5kg', 'อาหารสุนัข', 'ถุง', 8, 30),
            ('DOG-005', 'Pro Plan Adult 10kg', 'อาหารสุนัข', 'ถุง', 10, 40),
            ('CAT-001', 'Royal Canin Indoor Adult 10kg', 'อาหารแมว', 'ถุง', 10, 45),
            ('CAT-002', 'Whiskas Adult Tuna 1.1kg', 'อาหารแมว', 'ถุง', 20, 100),
            ('CAT-003', 'Felix Adult Salmon 1.5kg', 'อาหารแมว', 'ถุง', 15, 70),
            ('CAT-004', 'Pro Plan Cat Sterilised 10kg', 'อาหารแมว', 'ถุง', 8, 25),
            ('CAT-005', 'Me-O Adult Tuna 7kg', 'อาหารแมว', 'ถุง', 12, 55),
            ('SUP-001', 'VitaPet Multivitamin Dog 100เม็ด', 'อาหารเสริมสัตว์', 'กระปุก', 5, 20),
            ('SUP-002', 'Nutraceutics Omega-3 Dog 60caps', 'อาหารเสริมสัตว์', 'กระปุก', 5, 15),
            ('SUP-003', 'Arthrex Plus 500mg 60เม็ด', 'อาหารเสริมสัตว์', 'กระปุก', 3, 8),
            ('SUP-004', 'BioTop Cat Hairball 50g', 'อาหารเสริมสัตว์', 'หลอด', 8, 30),
            ('ACC-001', 'สายจูงสุนัขไนลอน M', 'อุปกรณ์สัตว์เลี้ยง', 'เส้น', 10, 40),
            ('ACC-002', 'ชามข้าวสแตนเลส 16cm', 'อุปกรณ์สัตว์เลี้ยง', 'ใบ', 15, 60),
            ('ACC-003', 'กรงเหล็กพับได้ M', 'อุปกรณ์สัตว์เลี้ยง', 'กรง', 3, 10),
            ('ACC-004', 'แชมพูสุนัข 500ml', 'อุปกรณ์สัตว์เลี้ยง', 'ขวด', 10, 35),
            ('ACC-005', 'ทรายแมว Ultra Clump 10L', 'อุปกรณ์สัตว์เลี้ยง', 'ถุง', 20, 5),  # ใกล้หมด
            ('ACC-006', 'ที่นอนสุนัขผ้าฝ้าย L', 'อุปกรณ์สัตว์เลี้ยง', 'ชิ้น', 5, 0),  # หมด
        ]

        for sku, name, cat_name, unit, min_stock, qty in products_data:
            cat = cats[cat_name]
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={'name': name, 'category': cat, 'unit': unit, 'min_stock': min_stock}
            )
            stock, _ = CentralStock.objects.get_or_create(
                product=product, defaults={'quantity': qty}
            )
            if created:
                self.stdout.write(f'  📦 สินค้า: {name} (คงเหลือ {qty})')

        # ผู้ดูแลระบบ
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'ผู้ดูแล',
                'last_name': 'ระบบ',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin1234')
            admin.save()
            self.stdout.write('  👤 ผู้ดูแล: admin / admin1234')

        # ผู้ยื่นคำร้องสาขาละ 1 คน
        requester_data = [
            ('req_kk01', 'สมชาย', 'ใจดี', branches[0]),
            ('req_kk02', 'สมหญิง', 'มีสุข', branches[1]),
            ('req_kk03', 'สมศรี', 'ร่มเย็น', branches[2]),
        ]
        for username, first, last, branch in requester_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first,
                    'last_name': last,
                    'role': User.Role.REQUESTER,
                    'branch': branch,
                }
            )
            if created:
                user.set_password('pass1234')
                user.save()
                self.stdout.write(f'  👤 ผู้ยื่น: {username} / pass1234 ({branch.name})')

        self.stdout.write(self.style.SUCCESS(
            '\n✅ สร้างข้อมูลตัวอย่างเสร็จแล้ว!\n'
            '\nบัญชีทดสอบ:\n'
            '  admin     / admin1234  (ผู้ดูแล)\n'
            '  req_kk01  / pass1234   (สาขาตลาดขุขันธ์)\n'
            '  req_kk02  / pass1234   (สาขาห้วยเหนือ)\n'
            '  req_kk03  / pass1234   (สาขาปรือใหญ่)\n'
        ))
