# @K0NKURS_UZ_BOT — Battl/Konkurs boti

## 1. O'rnatish

```bash
pip install -r requirements.txt
```

`config.py` faylida `BOT_TOKEN`ni o'zingizning tokeningizga almashtiring
(yoki `export BOT_TOKEN="123:ABC..."` orqali bering).

```bash
python3 main.py
```

Bot polling rejimida ishga tushadi (VPS, Railway, Render — qayerda bo'lsa ham ishlayveradi).

## 2. BotFather sozlamalari (MUHIM)

1. `/setprivacy` → **Disable** qiling — aks holda bot muhokama guruhidagi
   izohlarni (kommentlarni) ko'ra olmaydi.
2. `/setjoingroups` → Enable (guruhga qo'shilishi uchun, agar kerak bo'lsa).

## 3. Kanalni ulash

1. Botni kanalingizga qo'shing va **admin** qiling (xabar yuborish/tahrirlash
   huquqi bilan).
2. Agar kanalingizga **muhokama guruhi (discussion group)** ulangan bo'lsa —
   bot avtomatik ravishda kommentlarni o'sha yerdan hisoblaydi. Muhokama
   guruhida ham botni admin qilib qo'yishni unutmang.
3. Botga `/start` bosing → **📡 Kanal biriktirish** → kanalingizdan istalgan
   postni forward qiling.

## 4. Ishlatish

- **Mening kanallarim** → kanalni tanlang → boshqaruv paneli chiqadi:
  - 🚀 Battl boshlash — yutuqlar va tugash vaqtini so'raydi, kanalga avto post qiladi
  - 🏁 Battl tugatish
  - ➕➖ Bonus ball — ishtirokchini tanlab, qo'lda ball qo'shish/ayirish
  - ⚙️ Ball tizimi sozlamalari — reaksiya/komment/stars/boost uchun necha
    ball berilishini belgilash (faqat faol battl paytida)

- Kanaldagi "Batl boshlandi" postida ✅ **Qo'shish** tugmasini bosgan har bir
  foydalanuvchi uchun alohida post yaratiladi va reaksiya, komment, Stars,
  boost sonlari **avtomatik, real vaqtda** yangilanib turadi.

- 📊 **Natijalar** tugmasi bosilganda top-o'rinlar foydalanuvchining shaxsiy
  xabariga yuboriladi (agar u botni oldin ishga tushirmagan bo'lsa — popup
  ko'rinishida ko'rsatiladi).

## 5. Texnik cheklovlar (Telegram tomonidan)

- Kanal reaksiyalari **anonim** — bot faqat *umumiy sonini* biladi, kim
  bosganini emas. Shu sababli har bir ishtirokchi postidagi reaksiya/Stars
  soni **shu alohida post** bo'yicha hisoblanadi (umumiy kanal emas).
- Komment hisoblash uchun kanalga **muhokama guruhi ulangan** bo'lishi shart
  — aks holda komment bo'limi doim 0 bo'lib qoladi.
- Boost — foydalanuvchi ismi ko'rinadigan (anonim bo'lmagan) holatda ishlaydi.

## 6. Majburiy obuna

`config.py`dagi `REQUIRED_CHANNEL` (@K0NKURS_UZ) va `REQUIRED_CHAT`
(@bepul_gifts)ga obuna bo'lmagan foydalanuvchi ✅ Qo'shish tugmasini bossa,
obuna bo'lishni so'ragan ogohlantirish chiqadi. **Bot bu ikkala kanal/chatda
ham admin bo'lishi kerak** — aks holda obunani tekshira olmaydi.
