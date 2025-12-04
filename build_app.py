
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

def update_version_in_main(new_version):
    """تحديث رقم الإصدار في main.py"""
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # استبدال رقم الإصدار
        updated_content = re.sub(
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            content
        )
        
        with open('main.py', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"تم تحديث رقم الإصدار في main.py إلى {new_version}")
        return True
    except Exception as e:
        logger.error(f"فشل في تحديث main.py: {e}")
        return False

def update_version_in_readme(new_version):
    """تحديث رقم الإصدار في README.md"""
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # استبدال رقم الإصدار في badge
        updated_content = re.sub(
            r'Version-\d+\.\d+\.\d+',
            f'Version-{new_version}',
            content
        )
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        logger.info(f"تم تحديث رقم الإصدار في README.md إلى {new_version}")
        return True
    except Exception as e:
        logger.error(f"فشل في تحديث README.md: {e}")
        return False

def update_version_auto():
    """
    تحديث رقم الإصدار تلقائياً بناءً على عدد الـ commits في git
    مطابق تماماً لمنطق update_version.py
    """
    try:
        # الحصول على عدد الـ commits
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).strip().decode('utf-8')
        new_version = f"0.{commit_count}.0"
        logger.info(f"تم حساب الإصدار الجديد بناءً على git commits: {new_version}")
        
        # تحديث main.py
        if update_version_in_main(new_version):
            logger.info("✅ تم تحديث main.py")
        
        # تحديث README.md
        if update_version_in_readme(new_version):
            logger.info("✅ تم تحديث README.md")
            
        return new_version
        
    except subprocess.CalledProcessError:
        logger.warning("⚠️ تحذير: هذا المجلد ليس مستودع git أو لا يوجد commits. لن يتم تحديث الإصدار تلقائياً.")
        return get_version()
    except Exception as e:
        logger.error(f"❌ خطأ في التحديث التلقائي للإصدار: {e}")
        return get_version()


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

def find_tk_tcl_dirs():
    """البحث عن مجلدات tk8.6 و tcl8.6 في المسارات المحتملة"""
    possible_paths = [
        # Anaconda paths
        r'C:\Users\Nassar_Home\anaconda3\Library\lib',
        os.path.join(sys.base_prefix, 'Library', 'lib'),
        # Standard Python paths
        os.path.join(sys.base_prefix, 'tcl'),
        os.path.join(sys.base_prefix, 'Lib'),
    ]
    
    tk_dir = None
    tcl_dir = None
    
    for base_path in possible_paths:
        if not tk_dir:
            candidate_tk = os.path.join(base_path, 'tk8.6')
            if os.path.exists(candidate_tk):
                tk_dir = candidate_tk
                logger.info(f"تم العثور على tk8.6 في: {tk_dir}")
        
        if not tcl_dir:
            candidate_tcl = os.path.join(base_path, 'tcl8.6')
            if os.path.exists(candidate_tcl):
                tcl_dir = candidate_tcl
                logger.info(f"تم العثور على tcl8.6 في: {tcl_dir}")
        
        if tk_dir and tcl_dir:
            break
    
    return tk_dir, tcl_dir

def fix_tk_tcl_version():
    """إصلاح تعارض إصدارات Tk/Tcl"""
    try:
        # البحث عن مجلدات tk/tcl
        source_tk, source_tcl = find_tk_tcl_dirs()
        
        # التحقق من وجود المصادر
        if not source_tk:
            logger.error("لم يتم العثور على مجلد tk8.6 في أي من المسارات المحتملة")
            return False
        
        if not source_tcl:
            logger.error("لم يتم العثور على مجلد tcl8.6 في أي من المسارات المحتملة")
            return False
        
        # مجلد البرنامج المبني
        dist_dir = os.path.join(os.getcwd(), 'dist', 'Praytimes', '_internal')
        dest_tk = os.path.join(dist_dir, 'tk8.6')
        dest_tcl = os.path.join(dist_dir, 'tcl8.6')
        
        if not os.path.exists(dist_dir):
            logger.error(f"مجلد البرنامج المبني غير موجود: {dist_dir}")
            return False
        
        # إزالة المجلدات القديمة إذا كانت موجودة
        if os.path.exists(dest_tk):
            logger.info(f"إزالة مجلد tk8.6 القديم: {dest_tk}")
            shutil.rmtree(dest_tk)
        
        if os.path.exists(dest_tcl):
            logger.info(f"إزالة مجلد tcl8.6 القديم: {dest_tcl}")
            shutil.rmtree(dest_tcl)
        
        # نسخ المجلدات الجديدة
        logger.info(f"نسخ tk8.6 من {source_tk} إلى {dest_tk}")
        shutil.copytree(source_tk, dest_tk)
        
        logger.info(f"نسخ tcl8.6 من {source_tcl} إلى {dest_tcl}")
        shutil.copytree(source_tcl, dest_tcl)
        
        # التحقق من النسخ
        tk_tcl_file = os.path.join(dest_tk, 'tk.tcl')
        if os.path.exists(tk_tcl_file):
            # قراءة الإصدار من الملف
            with open(tk_tcl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if 'package require -exact Tk' in line:
                        logger.info(f"إصدار Tk في الملف المنسوخ: {line.strip()}")
                        break
        
        # نسخ ملفات DLL من Anaconda
        dll_source_paths = [
            r'C:\Users\Nassar_Home\anaconda3\Library\bin',
            os.path.join(sys.base_prefix, 'Library', 'bin'),
            os.path.join(sys.base_prefix, 'DLLs'),
        ]
        
        dll_files = ['tcl86t.dll', 'tk86t.dll']
        dll_copied = 0
        
        for dll_file in dll_files:
            for dll_source_dir in dll_source_paths:
                source_dll = os.path.join(dll_source_dir, dll_file)
                if os.path.exists(source_dll):
                    dest_dll = os.path.join(dist_dir, dll_file)
                    logger.info(f"نسخ {dll_file} من {source_dll}")
                    shutil.copy2(source_dll, dest_dll)
                    dll_copied += 1
                    break
        
        if dll_copied > 0:
            logger.info(f"تم نسخ {dll_copied} ملفات DLL")
        
        logger.info("✅ تم إصلاح إصدارات Tk/Tcl بنجاح")
        return True
        
    except Exception as e:
        logger.error(f"خطأ أثناء إصلاح إصدارات Tk/Tcl: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """الوظيفة الرئيسية"""
    logger.info("بدء عملية بناء التطبيق...")

    # تحديث رقم الإصدار تلقائياً
    version = update_version_auto()
    
    if not prepare_build():
        logger.error("فشلت عملية تحضير البناء")
        return

    if not build_app():
        logger.error("فشلت عملية بناء التطبيق")
        return
    
    # إصلاح تعارض إصدارات Tk/Tcl
    # logger.info("إصلاح إصدارات Tk/Tcl...")
    # if not fix_tk_tcl_version():
    #     logger.warning("تحذير: فشل إصلاح إصدارات Tk/Tcl")
    logger.info("تم تخطي إصلاح Tk/Tcl اليدوي (غير مطلوب مع وضع onefile)")
    
    if not create_installer():
        logger.error("فشلت عملية إنشاء حزمة التثبيت")
        return

    logger.info("اكتملت عملية بناء التطبيق بنجاح")

if __name__ == "__main__":
    main()
