# 📱 دليل شامل لالتقاط API من تطبيق Fustog على iPhone

## 🎯 المشكلة
- ✅ التصنيفات تعمل (11 تصنيف)
- ❌ المنتجات: API يرجع 200 لكن body فارغ
- ❌ الأسعار: نفس المشكلة
- 📱 التطبيق موبايل فقط (لا يوجد موقع)

**الحل:** التقاط الطلبات الحقيقية من iPhone!

---

## ⭐ الطريقة الموصى بها: mitmproxy (مجاني وقوي)

### الخطوة 1: إعداد الكمبيوتر (5 دقائق)

#### أ. تثبيت mitmproxy

```bash
# على Windows
pip install mitmproxy

# أو
pip3 install mitmproxy
```

#### ب. معرفة IP الكمبيوتر

**على Windows:**
```bash
ipconfig
```
ابحث عن **IPv4 Address** مثل: `192.168.1.100`

**على Mac:**
```bash
ifconfig | grep "inet "
```
أو: **System Preferences > Network** واضغط على WiFi

**احفظ هذا الـ IP - ستحتاجه!** 📝

#### ج. تشغيل mitmproxy

```bash
# في مجلد المشروع
cd f:\fustog\fustoog\sandbox\ingest

# تشغيل mitmweb (واجهة ويب)
mitmweb

# ستظهر رسالة:
# Web server listening at http://127.0.0.1:8081/
# Proxy server listening at http://*:8080
```

اترك النافذة مفتوحة! ✅

---

### الخطوة 2: إعداد iPhone (10 دقائق)

#### أ. الاتصال بنفس WiFi
**مهم جداً:** iPhone والكمبيوتر يجب أن يكونا على **نفس شبكة WiFi**!

#### ب. إعداد Proxy

1. **افتح Settings** ⚙️
2. **WiFi**
3. **اضغط على (i)** بجانب اسم الشبكة
4. **مرّر للأسفل إلى "HTTP Proxy"**
5. **اضغط "Manual"** (يدوي)
6. **أدخل:**
   - **Server:** `192.168.1.100` ← IP الكمبيوتر الذي حصلت عليه
   - **Port:** `8080`
   - **Authentication:** اتركه فارغاً
7. **اضغط Save** (حفظ)

✅ الآن iPhone سيمرر كل الطلبات عبر الكمبيوتر!

---

#### ج. تثبيت شهادة mitmproxy (مهم للـ HTTPS!)

**⚠️ استخدم Safari فقط - Chrome لن يعمل!**

1. **افتح Safari** على iPhone
2. **اذهب إلى:** `http://mitm.it`
   - لاحظ: `http` وليس `https`
3. **ستظهر لك صفحة mitmproxy**
4. **اضغط على أيقونة Apple 🍎**
5. **اضغط "Get mitmproxy-ca-cert.pem"**
6. **ستظهر رسالة "Profile Downloaded"**
7. **اضغط "Close"**

---

#### د. تثبيت Profile

1. **افتح Settings** ⚙️
2. **في أعلى القائمة، ستجد "Profile Downloaded"** (أو "الملف الشخصي الذي تم تنزيله")
3. **اضغط عليه**
4. **اضغط "Install"** (تثبيت)
5. **أدخل Passcode** (رمز الفتح)
6. **اضغط "Install"** مرة أخرى (أعلى اليمين)
7. **اضغط "Install"** للمرة الثالثة (في التحذير)
8. **اضغط "Done"** (تم)

---

#### هـ. تفعيل Certificate Trust (أهم خطوة!)

**⚠️ بدون هذه الخطوة، لن ترى طلبات HTTPS!**

1. **Settings** ⚙️
2. **General** (عام)
3. **About** (حول)
4. **مرّر للأسفل إلى "Certificate Trust Settings"** (إعدادات الوثوق بالشهادات)
5. **فعّل المفتاح بجانب "mitmproxy"** (سيصبح أخضر 🟢)
6. **اضغط "Continue"** في التحذير

✅ تم! الآن iPhone جاهز!

---

### الخطوة 3: استخدام تطبيق Fustog (5 دقائق)

1. **افتح تطبيق Fustog** على iPhone
2. **أغلق التطبيق تماماً وافتحه مجدداً** (مهم!)
3. **استخدم التطبيق بشكل طبيعي:**
   - تصفح التصنيفات
   - افتح منتجات
   - شاهد الأسعار
   - أضف للسلة (إذا أمكن)
   - ابحث عن منتجات
4. **قم بجميع الإجراءات التي تريد التقاطها**

---

### الخطوة 4: مشاهدة الطلبات (على الكمبيوتر)

1. **افتح المتصفح على الكمبيوتر**
2. **اذهب إلى:** `http://127.0.0.1:8081`
3. **ستظهر واجهة mitmweb**
4. **ستشاهد جميع الطلبات من iPhone!** 🎉

**ابحث عن:**
- `api.fustog.com`
- `ProductsByCategory`
- `ItemsPrices`
- `Categories`

---

### الخطوة 5: فحص الطلبات

**انقر على أي طلب لرؤية:**

#### أ. Request (الطلب):
- **Method:** GET / POST
- **URL:** الرابط الكامل
- **Headers:** جميع الـ headers
- **Query Parameters:** المعاملات في URL
- **Body:** محتوى الطلب (JSON, Form data, إلخ)

#### ب. Response (الاستجابة):
- **Status Code:** 200, 404, 500, إلخ
- **Headers:** headers الرد
- **Body:** محتوى الرد (JSON, HTML, إلخ)

**📝 انتبه خصوصاً لـ:**
```
1. Authorization header
2. X-API-Key header
3. Bearer tokens
4. Cookies
5. Custom headers (X-*, Fustog-*, إلخ)
6. Request body format
```

---

### الخطوة 6: حفظ النتائج

#### في واجهة mitmweb:

1. **File** (أعلى اليسار)
2. **Save**
3. **اختر تنسيق:**
   - **Flow (HAR format)** ← موصى به
   - أو **Flows**
4. **احفظ باسم:** `fustog_iphone_capture.har`

---

### الخطوة 7: تحليل HAR file

```bash
# حلل الطلبات تلقائياً
python scripts/analyze_har.py fustog_iphone_capture.har
```

**سيعطيك:**
- ✅ جميع طلبات API
- ✅ Headers كاملة
- ✅ Request bodies
- ✅ Response bodies
- ✅ أوامر cURL للاختبار
- ✅ كود Python جاهز

---

## 💎 بديل احترافي: Charles Proxy

**إذا لم ينجح mitmproxy أو تريد واجهة أسهل:**

### تحميل Charles
- https://www.charlesproxy.com/download/
- نسخة تجريبية مجانية 30 يوم
- أسهل من mitmproxy للمبتدئين

### الإعداد

**نفس الخطوات تقريباً:**

1. **شغّل Charles**
2. **iPhone:**
   - Settings > WiFi > (i) > Proxy > Manual
   - Server: IP الكمبيوتر
   - Port: `8888` (Charles يستخدم 8888)
3. **ثبّت الشهادة:**
   - Safari > `http://chls.pro/ssl`
   - Install Profile
   - Certificate Trust Settings
4. **في Charles:**
   - Proxy > SSL Proxying Settings
   - Enable SSL Proxying ✅
   - Add: `*.fustog.com` port `443`
5. **استخدم التطبيق**
6. **احفظ:** File > Export Session > HAR

**مميزات Charles:**
- ✅ واجهة أجمل وأسهل
- ✅ فلترة تلقائية
- ✅ تنظيم أفضل للطلبات
- ❌ ليس مجاني (لكن تجريبي 30 يوم)

---

## 🔧 حل المشاكل الشائعة

### المشكلة 1: لا أرى أي طلبات في mitmweb

**الحل:**
```
✅ تأكد من:
1. iPhone والكمبيوتر على نفس WiFi
2. IP الكمبيوتر صحيح (استخدم ipconfig)
3. Port: 8080
4. Certificate Trust مفعّل على iPhone
5. أعد تشغيل تطبيق Fustog
```

### المشكلة 2: "Cannot connect to internet" على iPhone

**الحل:**
```
✅ تأكد من:
1. mitmweb يعمل (النافذة مفتوحة)
2. IP الكمبيوتر صحيح
3. Firewall على الكمبيوتر لا يمنع Port 8080
4. على Windows:
   Control Panel > Windows Defender Firewall
   > Allow an app > اسمح لـ Python
```

### المشكلة 3: أرى HTTP لكن لا أرى HTTPS

**الحل:**
```
✅ تأكد من:
1. تثبيت الشهادة (Profile Downloaded)
2. تفعيل Certificate Trust Settings ← أهم شيء!
   Settings > General > About > Certificate Trust
3. إعادة تشغيل iPhone
4. إعادة تشغيل التطبيق
```

### المشكلة 4: الشهادة لا تُثبّت

**الحل:**
```
✅ تأكد من:
1. استخدام Safari فقط (ليس Chrome!)
2. http://mitm.it (وليس https)
3. الـ Proxy مضبوط بشكل صحيح
4. إعادة تشغيل iPhone والمحاولة مجدداً
```

### المشكلة 5: mitmweb لا يفتح على 127.0.0.1:8081

**الحل:**
```bash
# جرب port مختلف
mitmweb --web-port 8082

# أو شغّل بدون واجهة ويب
mitmproxy

# أو استخدم mitmdump للحفظ المباشر
mitmdump -w fustog_capture.flow
```

---

## ✅ قائمة التحقق السريعة

**قبل البدء:**
- [ ] iPhone والكمبيوتر على نفس WiFi
- [ ] تثبيت mitmproxy على الكمبيوتر
- [ ] معرفة IP الكمبيوتر

**على iPhone:**
- [ ] WiFi > (i) > Proxy > Manual
- [ ] Server: IP الكمبيوتر
- [ ] Port: 8080
- [ ] Safari > http://mitm.it > Install Profile
- [ ] Settings > Profile Downloaded > Install
- [ ] Settings > General > About > Certificate Trust > فعّل

**الاستخدام:**
- [ ] mitmweb يعمل
- [ ] http://127.0.0.1:8081 يفتح
- [ ] إعادة تشغيل تطبيق Fustog
- [ ] استخدام التطبيق
- [ ] مشاهدة الطلبات
- [ ] حفظ HAR file

**بعد الانتهاء:**
- [ ] تعطيل Proxy من iPhone
- [ ] حذف Profile (إذا أردت)
- [ ] تحليل HAR file

---

## 🎓 ماذا بعد؟

بعد التقاط الطلبات:

### 1. حلل HAR file
```bash
python scripts/analyze_har.py fustog_iphone_capture.har
```

### 2. انظر إلى النتائج
- Headers المطلوبة
- Authentication method
- Request format
- Parameters

### 3. عدّل السكربت
```python
# أضف Headers من الطلب الحقيقي
headers = {
    'Authorization': 'Bearer TOKEN_FROM_CAPTURE',
    'X-API-Key': 'KEY_FROM_CAPTURE',
    # ... إلخ
}
```

### 4. اختبر
```bash
python scripts/scrape_products_prices_compare.py
```

---

## 📞 دعم إضافي

**إذا واجهت مشاكل:**

1. **راجع هذا الدليل خطوة بخطوة**
2. **تأكد من جميع الخطوات**
3. **جرب Charles Proxy كبديل**
4. **تأكد من Certificate Trust مفعّل**

**موارد مفيدة:**
- [mitmproxy Docs](https://docs.mitmproxy.org/)
- [Charles iOS Setup](https://www.charlesproxy.com/documentation/using-charles/ssl-certificates/)

---

## 🎯 الخلاصة

### الطريقة:
1. ✅ شغّل mitmproxy على الكمبيوتر
2. ✅ اضبط Proxy على iPhone
3. ✅ ثبّت الشهادة
4. ✅ فعّل Certificate Trust
5. ✅ استخدم التطبيق
6. ✅ احفظ HAR file
7. ✅ حلل النتائج
8. ✅ عدّل السكربت

### الوقت المتوقع:
- **الإعداد:** 15 دقيقة (أول مرة)
- **الالتقاط:** 5 دقائق
- **التحليل:** 5 دقائق
- **المجموع:** ~25 دقيقة

### النتيجة:
✅ ستحصل على الطلبات الحقيقية بالضبط
✅ Headers كاملة
✅ Authentication method
✅ Request format الصحيح
✅ حل المشكلة نهائياً! 🎉

---

**آخر تحديث:** 26 يناير 2026  
**الحالة:** ✅ جاهز للاستخدام