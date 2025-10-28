
# build_app.py
# بناء التطبيق مع كل التحسينات

import os
import sys
import subprocess
import shutil
import logging

# إعداد التسجيل
sys.stdout.reconfigure(encoding='utf-8')

# إعداد logger الجذر يدوياً
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

    # نسخ الخطافات المخصصة
    try:
        shutil.copy('hook-glob.py', os.path.join(hooks_dir, 'hook-glob.py'))
        shutil.copy('hook-pathlib.py', os.path.join(hooks_dir, 'hook-pathlib.py'))
        logger.info("تم نسخ الخطافات المخصصة")
    except Exception as e:
        logger.error(f"خطأ في نسخ الخطافات: {e}")
        return False

    return True

def build_app():
    """بناء التطبيق"""
    logger.info("بدء بناء التطبيق...")

    # إعداد متغيرات البيئة
    env = os.environ.copy()
    hooks_dir = os.path.join(os.getcwd(), 'hooks')
    env['PYINSTALLER_HOOKSPATH'] = hooks_dir

    # بناء التطبيق
    try:
        # Validate paths and commands
        main_spec = os.path.abspath('main.spec')
        if not os.path.isfile(main_spec):
            logger.error("main.spec file not found")
            return False
            
        venv_python = r'C:\Users\Nassar_Home\.tens_env\Scripts\python.exe'
        pyinstaller_args = [venv_python, '-m', 'PyInstaller', main_spec, '--clean', '--noconfirm']
        try:
            result = subprocess.run(
                pyinstaller_args,
                env=env,
                capture_output=True,
                text=True,
                check=True  # Will raise CalledProcessError if return code != 0
            )
            logger.info("تم بناء التطبيق بنجاح")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل بناء التطبيق: {e.stderr}")
            return False

        logger.info("تم بناء التطبيق بنجاح")
        return True
    except Exception as e:
        logger.error(f"خطأ في بناء التطبيق: {e}")
        return False

def create_installer():
    """إنشاء حزمة التثبيت"""
    logger.info("إنشاء حزمة التثبيت...")

    try:
        # Validate installer script path
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
                check=True  # Will raise CalledProcessError if return code != 0
            )
            logger.info("تم إنشاء حزمة التثبيت بنجاح")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل إنشاء حزمة التثبيت: {e.stderr}")
            return False

        logger.info("تم إنشاء حزمة التثبيت بنجاح")
        return True
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
