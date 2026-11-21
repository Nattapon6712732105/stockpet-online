# ระบบจัดการคลังสินค้าอาหารสัตว์ · ขุขันธ์ (Khukhan Petfood Warehouse)

ระบบจัดการคลังสินค้าอาหารสัตว์สำหรับ **1 คลังกลาง + 3 สาขา** พร้อมระบบเบิก-อนุมัติ-ตัดสต็อก  
ธีมแรงบันดาลใจจากอำเภอขุขันธ์ จ.ศรีสะเกษ — ปราสาทหิน, ดอกลำดวน, ผ้าไหมลายเขมร

---

## 🚀 การ Deploy บน Vercel

โปรเจกต์นี้ได้รับการตั้งค่าไฟล์คอนฟิกสำหรับ Vercel เรียบร้อยแล้ว (`vercel.json`, `build_files.sh`, `whitenoise`):

### ข้อสำคัญสำหรับ Vercel (Serverless):
- Vercel เป็น Serverless Function ซึ่งระบบไฟล์จะเป็น **Read-Only** (ไม่สามารถเขียนไฟล์ SQLite ได้ถาวร)
- สำหรับ Production บน Vercel ต้องเชื่อมต่อกับ Database ภายนอกที่เป็น PostgreSQL (เช่น **Neon Database**, **Supabase**, หรือ **Vercel Postgres**) ฟรีและเปิดใช้งานได้ทันที

### ขั้นตอนการ Deploy:
1. Push โค้ดนี้ขึ้น **GitHub**
2. ไปที่ [Vercel Dashboard](https://vercel.com/new) -> กด **Import Git Repository**
3. ที่หน้า Configure Project:
   - **Framework Preset**: Other
   - **Root Directory**: `./` (ไม่ต้องเปลี่ยน)
4. ตั้งค่า **Environment Variables** ใน Vercel:
   - `SECRET_KEY`: `<ใส่ Secret Key>`
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `.vercel.app`
   - `DATABASE_URL`: `postgres://user:password@host:port/database` *(URL จาก Neon หรือ Supabase)*
5. กด **Deploy**

---

## 💻 การติดตั้งและรันในเครื่อง (Local)

```bash
# 1. ติดตั้ง dependencies
pip install -r requirements.txt

# 2. ตั้งค่า environment
cp petfood_warehouse/.env.example petfood_warehouse/.env

# 3. สร้างฐานข้อมูล
cd petfood_warehouse
python manage.py migrate

# 4. สร้างข้อมูลตัวอย่าง (3 สาขา, 20 สินค้า, ผู้ใช้ 4 คน)
python manage.py seed_demo

# 5. รันเซิร์ฟเวอร์
python manage.py runserver
```

เปิดเบราว์เซอร์ที่ http://127.0.0.1:8000

---

## 👥 บัญชีทดสอบ (Demo Users)

| บัญชี | รหัสผ่าน | บทบาท |
|---|---|---|
| `admin` | `admin1234` | ผู้ดูแลระบบ (จัดการสต็อกคลังกลาง, อนุมัติ/ปฏิเสธคำร้อง) |
| `req_kk01` | `pass1234` | ผู้ยื่นคำร้อง — สาขาตลาดขุขันธ์ |
| `req_kk02` | `pass1234` | ผู้ยื่นคำร้อง — สาขาห้วยเหนือ |
| `req_kk03` | `pass1234` | ผู้ยื่นคำร้อง — สาขาปรือใหญ่ |

---

## 🧪 การทดสอบ (Unit Tests)

```bash
cd petfood_warehouse
python manage.py test tests.test_services -v 2
```
