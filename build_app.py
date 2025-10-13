
# build_app.py
# بناء التطبيق مع كل التحسينات

import os
import sys
import subprocess
import shutil
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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
        result = subprocess.run(
            [sys.executable, '-m', 'PyInstaller', 'main.spec', '--clean'],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"فشل بناء التطبيق: {result.stderr}")
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
        result = subprocess.run(
            [sys.executable, 'create_installer.py'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            logger.error(f"فشل إنشاء حزمة التثبيت: {result.stderr}")
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
