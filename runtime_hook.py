# runtime_hook.py
# خطاف تشغيل محسن لـ PyInstaller مع معالجة أخطاء أفضل

import sys
import os
import logging

# Set up basic logging for the hook
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def safe_add_path(path, description):
    """إضافة مسار بأمان إلى sys.path مع معالجة الأخطاء"""
    try:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            logging.debug(f"Added {description} to sys.path: {path}")
        else:
            logging.debug(f"{description} path not found or already in sys.path: {path}")
    except Exception as e:
        logging.warning(f"Failed to add {description} to sys.path: {e}")

def safe_set_env(key, value, description):
    """تعيين متغير البيئة بأمان مع معالجة الأخطاء"""
    try:
        os.environ[key] = value
        logging.debug(f"Set {description}: {key}={value}")
    except Exception as e:
        logging.warning(f"Failed to set {description}: {e}")

if hasattr(sys, '_MEIPASS'):
    try:
        app_dir = sys._MEIPASS
        logging.info(f"PyInstaller app directory: {app_dir}")

        # Ensure the app directory exists and is accessible
        if not os.path.exists(app_dir):
            logging.error(f"PyInstaller app directory does not exist: {app_dir}")
            sys.exit(1)

        # Add bundled PIL path to sys.path
        pil_path = os.path.join(app_dir, 'PIL')
        safe_add_path(pil_path, "PIL")

        # Add bundled setuptools path to sys.path (if it exists)
        setuptools_path = os.path.join(app_dir, 'setuptools')
        safe_add_path(setuptools_path, "setuptools")

        # Set environment variables for PIL
        safe_set_env('PILLOW_ROOT', pil_path, "PILLOW_ROOT")

        # Ensure TCL/TK paths are set correctly for tkinter
        tcl_path = os.path.join(app_dir, 'tcl8.6')
        tk_path = os.path.join(app_dir, 'tk8.6')

        if os.path.exists(tcl_path):
            safe_set_env('TCL_LIBRARY', tcl_path, "TCL_LIBRARY")

        if os.path.exists(tk_path):
            safe_set_env('TK_LIBRARY', tk_path, "TK_LIBRARY")

        logging.info("Runtime hook initialization completed successfully")

    except Exception as e:
        logging.error(f"Critical error in runtime hook: {e}")
        # Don't exit here as it might prevent the app from starting
        # Just log the error and continue

    # فحص نهائي للوصول إلى _MEIPASS وتحذير من القفل
    if hasattr(sys, '_MEIPASS'):
        app_dir = sys._MEIPASS
        if os.path.exists(app_dir):
            try:
                # محاولة الوصول للتحقق من القفل
                test_file = os.path.join(app_dir, 'test_access.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                logging.debug(f"الوصول إلى _MEIPASS ناجح: {app_dir}")
            except (OSError, PermissionError, IOError) as lock_error:
                logging.warning(f"قفل محتمل في _MEIPASS: {app_dir}. خطأ: {lock_error}")
                logging.info("اقتراح: قم بتنظيف يدوي لمجلدات _MEI في %TEMP% لإصلاح مشاكل إعادة التشغيل")
        else:
            logging.error(f"_MEIPASS غير موجود: {app_dir}. قد يفشل تشغيل المفسر المضمن")
