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

        # Set VLC environment variables for self-contained operation
        vlc_path = os.path.join(app_dir, 'vlc')
        vlc_plugins_path = os.path.join(vlc_path, 'plugins')

        print(f"VLC setup: app_dir={app_dir}, vlc_path={vlc_path}, plugins={vlc_plugins_path}")

        if os.path.exists(vlc_path):
            print("VLC directory exists, setting environment variables")

            # CRITICAL: Add VLC directory to PATH FIRST before any VLC imports
            current_path = os.environ.get('PATH', '')
            if vlc_path not in current_path:
                new_path = vlc_path + os.pathsep + current_path
                safe_set_env('PATH', new_path, "PATH (VLC dir first)")
                print(f"Added VLC directory to PATH: {vlc_path}")

            # Set VLC_PLUGIN_PATH to point to bundled plugins
            safe_set_env('VLC_PLUGIN_PATH', vlc_plugins_path, "VLC_PLUGIN_PATH")
            print(f"Set VLC_PLUGIN_PATH to {vlc_plugins_path}")

            # Add app directory to PATH as well for other DLLs
            if app_dir not in os.environ.get('PATH', ''):
                current_path = os.environ.get('PATH', '')
                new_path = app_dir + os.pathsep + current_path
                safe_set_env('PATH', new_path, "PATH (with app dir)")
                print(f"Added app directory to PATH: {app_dir}")

            # Set VLC_DATA_PATH if locale directory exists
            vlc_locale_path = os.path.join(vlc_path, 'locale')
            if os.path.exists(vlc_locale_path):
                safe_set_env('VLC_DATA_PATH', vlc_path, "VLC_DATA_PATH")
                print(f"Set VLC_DATA_PATH to {vlc_path}")

            # Additional VLC environment variables for better compatibility
            safe_set_env('VLC_LOCALES_PATH', vlc_locale_path, "VLC_LOCALES_PATH")
            safe_set_env('VLC_CONFIG_PATH', app_dir, "VLC_CONFIG_PATH")

            print("VLC environment variables configured for bundled operation")
        else:
            print("VLC directory does not exist - will try to use system VLC")

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
