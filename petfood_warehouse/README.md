# ระบบจัดการคลังสินค้าอาหารสัตว์ · ขุขันธ์

ระบบจัดการคลังสินค้าอาหารสัตว์สำหรับ **1 คลังกลาง + 3 สาขา** พร้อมระบบเบิก-อนุมัติ-ตัดสต็อก  
ธีมแรงบันดาลใจจากอำเภอขุขันธ์ จ.ศรีสะเกษ — ปราสาทหิน, ดอกลำดวน, ผ้าไหมลายเขมร

---

## ติดตั้งและรันระบบ

### ความต้องการระบบ
- Python 3.11+
- pip

### ขั้นตอน

```bash
# 1. โคลนหรือเข้าโฟลเดอร์โปรเจกต์
cd stockpet-online/petfood_warehouse

# 2. ติดตั้ง dependencies
pip install -r ../requirements.txt

# 3. ตั้งค่า environment (คัดลอก .env.example)
cp .env.example .env
# แก้ไข .env ตามต้องการ (SECRET_KEY สำหรับ production)

# 4. สร้างฐานข้อมูล
python manage.py migrate

# 5. สร้างข้อมูลตัวอย่าง
python manage.py seed_demo

# 6. รันเซิร์ฟเวอร์
python manage.py runserver
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:8000

---

## บัญชีทดสอบ

| บัญชี | รหัสผ่าน | บทบาท |
|---|---|---|
| `admin` | `admin1234` | ผู้ดูแลระบบ |
| `req_kk01` | `pass1234` | ผู้ยื่นคำร้อง — สาขาตลาดขุขันธ์ |
| `req_kk02` | `pass1234` | ผู้ยื่นคำร้อง — สาขาห้วยเหนือ |
| `req_kk03` | `pass1234` | ผู้ยื่นคำร้อง — สาขาปรือใหญ่ |

---

## โครงสร้างโปรเจกต์

```
petfood_warehouse/
├── manage.py
├── .env / .env.example
├── config/              # settings, urls, wsgi
├── apps/
│   ├── accounts/        # User(role, branch), login/logout
│   ├── inventory/       # Product, Category, CentralStock, StockMovement
│   │   └── management/commands/seed_demo.py
│   ├── requisitions/    # Request, Item, services.py (ตรรกะอนุมัติ)
│   └── reports/         # ส่งออก CSV
├── templates/           # Django templates (ธีมขุขันธ์)
├── static/              # CSS, JS, SVG
└── tests/               # unit tests
```

---

## คุณสมบัติหลัก

### ✅ ระบบคำร้องขอเบิก
- ผู้ยื่นคำร้องส่งคำร้องได้ — เลือกสินค้า ระบุจำนวน ส่งคำร้อง
- ผู้ดูแลอนุมัติ / ปฏิเสธ / อนุมัติบางส่วน
- **ตัดสต็อกเฉพาะตอนอนุมัติเท่านั้น**
- ผู้ยื่นคำร้องยกเลิกได้ขณะสถานะ "รออนุมัติ"

### ✅ ความปลอดภัย (transaction.atomic + select_for_update)
- ป้องกันการอนุมัติซ้ำ / 2 admin กดพร้อมกัน
- สต็อกไม่ติดลบ (ใช้ PositiveIntegerField + validate)
- ตรวจสิทธิ์ฝั่ง server ทุก endpoint

### ✅ ธีมขุขันธ์
- สี: ศิลาแลง (#9C4A24), ลำดวน (#F3E3A3), น้ำเงินไหม (#1F2F4D)
- โลโก้ดอกลำดวน 5 กลีบ (inline SVG)
- แถบลายขอมใต้ header
- Responsive — ใช้งานบนมือถือได้ ปุ่ม ≥ 44px

---

## เปลี่ยนเป็น PostgreSQL (production)

แก้ไข `.env`:
```env
DATABASE_URL=postgres://user:password@localhost:5432/petfood_warehouse
```

แก้ไข `config/settings.py` ส่วน DATABASES:
```python
import dj_database_url
DATABASES = {'default': dj_database_url.config()}
```

---

## สำรองข้อมูล (SQLite)

```bash
# สำรองข้อมูล
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d)

# ส่งออก JSON fixture
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission > backup.json

# นำเข้า
python manage.py loaddata backup.json
```

---

## รันเทสต์

```bash
python manage.py test tests.test_services -v 2
```

ทดสอบครอบคลุม:
- ✅ อนุมัติแล้วสต็อกลดถูกต้อง
- ✅ สต็อกไม่พอแล้วไม่ตัด
- ✅ อนุมัติซ้ำไม่ได้
- ✅ ปฏิเสธไม่ตัดสต็อก
- ✅ อนุมัติบางส่วน
- ✅ ผู้ยื่นคำร้องไม่มีสิทธิ์อนุมัติ
- ✅ สต็อกสาขาเพิ่มขึ้นเมื่ออนุมัติ
- ✅ ยกเลิกคำร้อง PENDING ได้
- ✅ ยกเลิกคำร้องที่อนุมัติไปแล้วไม่ได้
- ✅ รับสินค้าเข้าคลังกลาง
