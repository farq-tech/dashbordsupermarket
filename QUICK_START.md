# 🚀 البدء السريع - التقاط API من iPhone

## الطريقة الأسرع (3 خطوات فقط!)

### 1️⃣ شغّل السكربت على الكمبيوتر

```powershell
# على Windows
.\scripts\start_iphone_capture.ps1

# أو يدوياً
pip install mitmproxy
mitmweb
```

### 2️⃣ اضبط iPhone

**Settings > WiFi > (i) > Proxy > Manual**
- Server: (IP الذي سيظهر في السكربت)
- Port: `8080`

**Safari > `http://mitm.it`**
- ثبّت الشهادة
- Settings > General > About > Certificate Trust > فعّل

### 3️⃣ استخدم التطبيق واحفظ

- استخدم تطبيق Fustog
- افتح `http://127.0.0.1:8081` على الكمبيوتر
- احفظ: File > Save > HAR

---

## التحليل

```bash
python scripts/analyze_har.py fustog_capture.har
```

---

## 📚 المزيد من التفاصيل

### للمبتدئين تماماً:
📖 اقرأ: **IPHONE_GUIDE.md** - دليل خطوة بخطوة مع الصور

### للمحترفين:
📖 اقرأ: **SOLUTION_GUIDE.md** - جميع الحلول والطرق

### مشاكل؟
📖 اقرأ: **IPHONE_GUIDE.md** > قسم "حل المشاكل"

---

## ⚡ الأسئلة الشائعة

**س: لا أرى طلبات؟**
✅ تأكد من Certificate Trust مفعّل على iPhone

**س: "Cannot connect"؟**
✅ تأكد من IP صحيح ومن نفس WiFi

**س: الشهادة لا تُثبّت؟**
✅ استخدم Safari فقط (ليس Chrome)

---

## 📁 الملفات المهمة

```
IPHONE_GUIDE.md              - دليل شامل للـ iPhone
scripts/start_iphone_capture.ps1  - سكربت تشغيل تلقائي
scripts/analyze_har.py       - تحليل HAR files
```

---

## 🎯 بعد الالتقاط

1. ✅ احفظ HAR file
2. ✅ حلله: `python scripts/analyze_har.py file.har`
3. ✅ انسخ Headers و Authentication
4. ✅ عدّل السكربت
5. ✅ اختبر: `python scripts/scrape_products_prices_compare.py`

---

**الوقت المتوقع:** 20-25 دقيقة  
**الصعوبة:** سهل (مع التعليمات)  
**النتيجة:** ✅ حل المشكلة نهائياً!
