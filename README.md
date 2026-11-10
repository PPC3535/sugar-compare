# Sugar Seasonal Compare

เว็บแอปเทียบราคาฟิวเจอร์สน้ำตาลวันเดียวกันของแต่ละปี (ปี 2024–2027)

- White Sugar #5 (ICE London): SWH, SWK, SWQ — USD/ตัน
- Raw Sugar #11 (ICE US): SBH, SBK, SBN — US¢/ปอนด์

ข้อมูลราคาปิดรายวันจาก Barchart ถึง 9 พ.ย. 2026 (ไฟล์ดิบอยู่ที่ `data/sugar_daily.csv`)
หน้าเว็บเป็นไฟล์เดียว `index.html` ไม่ต้อง build

## อัปเดตข้อมูล

- อัตโนมัติ: GitHub Actions (`.github/workflows/update-data.yml`) รัน `scripts/update_data.py` ทุกคืนวันทำการ 20:15 UTC (03:15 น. เวลาไทย)
- กดเอง: ปุ่ม “อัปเดตข้อมูล” บนหน้าเว็บจะเปิดหน้า workflow → กด **Run workflow** → หน้าเว็บจะโหลดข้อมูลใหม่ให้เองเมื่อเสร็จ (ราว 2–4 นาที)
- หน้าเว็บโหลด `data/data.json` ตอนเปิด ถ้าโหลดไม่ได้จะใช้ข้อมูลที่ฝังไว้ใน `index.html`
- สัญญาที่ดึงไม่สำเร็จจะคงข้อมูลเดิมไว้ ไม่ลบทิ้ง
