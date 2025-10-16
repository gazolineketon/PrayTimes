import json

# قراءة الملف الحالي
with open('c:\\Temp\\PrayTimes\\Countries&Cities\\Egypt.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# الترجمات الجديدة
new_translations = [
    {"english_name": "Al Manşūrah", "arabic_name": "المنصورة"},
    {"english_name": "Al Minyā", "arabic_name": "المنيا"},
    {"english_name": "Arish", "arabic_name": "العريش"},
    {"english_name": "Asyūţ", "arabic_name": "أسيوط"},
    {"english_name": "Banī Suwayf", "arabic_name": "بني سويف"},
    {"english_name": "Disūq", "arabic_name": "دسوق"}
]

# إضافة الترجمات الجديدة
data.extend(new_translations)

# كتابة الملف مرة أخرى
with open('c:\\Temp\\PrayTimes\\Countries&Cities\\Egypt.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("تم إضافة الترجمات بنجاح!")