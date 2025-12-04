# create_portable_installer.py
# إنشاء حزمة محمولة احترافية

import os
import zipfile
import shutil

def create_portable_installer():
    """إنشاء حزمة ZIP محمولة مع ملفات التعليمات"""
    
    print("إنشاء حزمة التثبيت المحمولة...")
    
    # المسارات
    dist_folder = os.path.join("dist", "Praytimes")
    zip_filename = "PrayTimes_Setup.zip"
    readme_file = "README_Install.txt"
    
    # التحقق من وجود المجلد
    if not os.path.exists(dist_folder):
        print(f"خطأ: المجلد {dist_folder} غير موجود!")
        return False
    
    # إنشاء ملف التعليمات
    readme_content = """===========================================
    برنامج مواقيت الصلاة - Prayer Times
===========================================

مرحباً بك في برنامج مواقيت الصلاة!

📁 محتويات الحزمة:
------------------
- Praytimes.exe : الملف التنفيذي الرئيسي
- _internal/ : مجلد المكتبات المطلوبة (لا تحذفه!)

💻 متطلبات التشغيل:
------------------
- نظام Windows 10 أو أحدث
- لا يوجد! البرنامج مستقل تماماً ولا يحتاج Python أو أي برامج إضافية

🚀 التثبيت:
-----------
1. فك ضغط الملف إلى أي مجلد (مثل: C:\\Program Files\\PrayTimes)
2. شغّل Praytimes.exe
3. استمتع!

📌 لإنشاء اختصار على سطح المكتب:
---------------------------------
1. انقر بالزر الأيمن على Praytimes.exe
2. اختر "إرسال إلى" -> "سطح المكتب (إنشاء اختصار)"

⚠️ ملاحظة مهمة:
---------------
- احتفظ بمجلد "_internal" بجانب Praytimes.exe دائماً
- لا تنقل الملف التنفيذي بمفرده

📞 الدعم:
---------
للمساعدة أو الإبلاغ عن مشاكل، تواصل معنا

===========================================
    جميع الحقوق محفوظة © 2025
===========================================
"""
    
    # حفظ ملف التعليمات
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"تم إنشاء {readme_file}")
    
    # إنشاء ملف ZIP
    print(f"ضغط الملفات إلى {zip_filename}...")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # إضافة ملف التعليمات
        zipf.write(readme_file, os.path.join("PrayTimes", readme_file))
        
        # إضافة جميع ملفات البرنامج
        for root, dirs, files in os.walk(dist_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join("PrayTimes", os.path.relpath(file_path, dist_folder))
                zipf.write(file_path, arcname)
                print(f"  إضافة: {arcname}")
    
    print(f"\n✅ تم إنشاء الحزمة بنجاح: {zip_filename}")
    print(f"📦 الحجم: {os.path.getsize(zip_filename) / (1024*1024):.2f} MB")
    
    # حذف ملف التعليمات المؤقت
    os.remove(readme_file)
    
    return True

if __name__ == "__main__":
    create_portable_installer()
