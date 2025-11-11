
# build_app.py
# بناء التطبيق مع كل التحسينات

import os
import sys
import subprocess
import shutil
import re
import logging

# إعداد التسجيل
sys.stdout.reconfigure(encoding='utf-8')

# إعداد سجل الجذر يدوياً
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

# إضافة handler للملف مع ترميز UTF-8
log_file = 'build.log'
file_handler = logging.FileHandler(log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

# إضافة handler للـ console
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
root_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)

# تحديد مسار مفسر بايثون الحالي (الذي يحتوي على PyInstaller)
VENV_PYTHON = sys.executable

def prepare_build():
    """تحضير بيئة البناء"""
    logger.info("تحضير بيئة البناء...")

    # تنظيف المجلدات القديمة
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                logger.info(f"تم حذف المجلد: {dir_name}")
            except Exception as e:
                logger.warning(f"فشل في حذف المجلد {dir_name}: {e}")

    # إنشاء مجلد الخطافات
    hooks_dir = os.path.join(os.getcwd(), 'hooks')
    if not os.path.exists(hooks_dir):
        os.makedirs(hooks_dir)
        logger.info(f"تم إنشاء مجلد الخطافات: {hooks_dir}")

    # ملفات الخطافات مُعدة مسبقًا في مجلد hooks
    logger.info("ملفات الخطافات جاهزة في مجلد hooks")

    return True

def get_version():
    """يقرأ رقم الإصدار من main.py"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", content)
            if match:
                version = match.group(1)
                logger.info(f"تم العثور على الإصدار: {version}")
                return version
    except Exception as e:
        logger.error(f"فشل في قراءة رقم الإصدار من main.py: {e}")
    return None

def create_version_file(version):
    """إنشاء ملف معلومات الإصدار لـ PyInstaller"""
    version_file_content = f"""
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version.replace('.', ',')}, 0),
    prodvers=({version.replace('.', ',')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040104b0',
          [StringStruct(u'CompanyName', u'PrayerTimes'),
          StringStruct(u'FileDescription', u'Prayer Times Application'),
          StringStruct(u'FileVersion', u'{version}'),
          StringStruct(u'InternalName', u'PrayTimes'),
          StringStruct(u'LegalCopyright', u'Copyright © 2025. All rights reserved.'),
          StringStruct(u'OriginalFilename', u'PrayTimes.exe'),
          StringStruct(u'ProductName', u'مواقيت الصلاة'),
          StringStruct(u'ProductVersion', u'{version}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1025, 1200])])
  ]
)
"""
    try:
        with open('version.txt', 'w', encoding='utf-8') as f:
            f.write(version_file_content)
        logger.info("تم إنشاء ملف version.txt بنجاح.")
        return 'version.txt'
    except Exception as e:
        logger.error(f"فشل في إنشاء ملف version.txt: {e}")
        return None

def build_app():
    """بناء التطبيق"""
    logger.info("بدء بناء التطبيق...")

    # إعداد متغيرات البيئة
    version = get_version()
    version_file = create_version_file(version) if version else None
    if not version_file:
        logger.error("فشل في إنشاء ملف الإصدار، لا يمكن المتابعة.")
        return False
    env = os.environ.copy()
    hooks_dir = os.path.join(os.getcwd(), 'hooks')
    env['PYINSTALLER_HOOKSPATH'] = hooks_dir

    # بناء التطبيق
    try:
        # التحقق من صحة المسارات والأوامر
        main_spec = os.path.abspath('main.spec')
        if not os.path.isfile(main_spec):
            logger.error("main.spec file not found")
            return False

        pyinstaller_args = [VENV_PYTHON, '-m', 'PyInstaller', main_spec, '--clean', '--noconfirm']
        try:
            result = subprocess.run(
                pyinstaller_args,
                env=env,
                capture_output=True,
                text=True,
                check=True  # سيتم إطلاق خطأ CalledProcessError إذا كانت قيمة رمز الإرجاع لا تساوي صفرًا
            )
            logger.info("تم بناء التطبيق بنجاح")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل بناء التطبيق: {e.stderr}")
            return False
    except Exception as e:
        logger.error(f"خطأ في بناء التطبيق: {e}")
        return False

def create_installer():
    """إنشاء حزمة التثبيت"""
    logger.info("إنشاء حزمة التثبيت...")

    try:
        # التحقق من صحة مسار البرنامج النصي للتثبيت
        installer_script = os.path.abspath('create_installer.py')
        if not os.path.isfile(installer_script):
            logger.error("create_installer.py script not found")
            return False
            
        installer_args = [sys.executable, installer_script]
        try:
            result = subprocess.run(
                installer_args,
                capture_output=True,
                text=True,
                check=True  # سيتم إطلاق خطأ CalledProcessError إذا كانت قيمة رمز الإرجاع لا تساوي صفرً
            )
            logger.info("تم إنشاء حزمة التثبيت بنجاح")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل إنشاء حزمة التثبيت: {e.stderr}")
            return False
    except Exception as e:
        logger.error(f"خطأ في إنشاء حزمة التثبيت: {e}")
        return False

def main():
    """الوظيفة الرئيسية"""
    logger.info("بدء عملية بناء التطبيق...")

    if not prepare_build():
        logger.error("فشلت عملية تحضير البناء")
        return

    if not build_app():
        logger.error("فشلت عملية بناء التطبيق")
        return

    if not create_installer():
        logger.error("فشلت عملية إنشاء حزمة التثبيت")
        return

    logger.info("اكتملت عملية بناء التطبيق بنجاح")

if __name__ == "__main__":
    main()
