# Sugar Seasonal Compare

เว็บแอปเทียบราคาฟิวเจอร์สน้ำตาลวันเดียวกันของแต่ละปี (ปี 2024–2027)

- White Sugar #5 (ICE London): SWH, SWK, SWQ — USD/ตัน
- Raw Sugar #11 (ICE US): SBH, SBK, SBN — US¢/ปอนด์

ข้อมูลราคาปิดรายวันจาก Barchart ถึง 9 พ.ย. 2026 (ไฟล์ดิบอยู่ที่ `data/sugar_daily.csv`)
หน้าเว็บเป็นไฟล์เดียว `index.html` ไม่ต้อง build

## อัปเดตข้อมูล

Barchart บล็อกการดึงจากเซิร์ฟเวอร์ (GitHub, Google) จึงให้ Claude ดึงผ่าน Chrome บนเครื่องผู้ใช้

- งานตั้งเวลาใน Claude ชื่อ “Sugar Compare: อัปเดตราคา” รันราว 05:43 น. (เวลาไทย) วันอังคาร–เสาร์ หรือกด **Run now** ที่ claude.ai/code/routines (ปุ่ม “อัปเดตข้อมูล” บนเว็บพาไปหน้านี้)
- ขั้นตอน: `scripts/merge_update.py active` → รัน `scripts/chrome_fetch.js` ในแท็บ barchart.com → `scripts/merge_update.py merge` → push ไฟล์ `data/` ไปที่ branch `claude/data`
- หน้าเว็บโหลด `data/data.json` จาก branch `claude/data` (ผ่าน raw.githubusercontent.com) ก่อน แล้วค่อยใช้สำเนาใน `main` เป็นสำรอง
- Mac ต้องเปิดอยู่และ Chrome มีส่วนขยาย Claude เชื่อมต่ออยู่ตอนงานรัน
