# runtime_hook.py
# خطاف تشغيل محسن لـ PyInstaller مع معالجة أخطاء أفضل

import sys
import os
import logging

# Setup file logging for debugging
debug_file = r'C:\Temp\PrayTimes\hook_debug.txt'
try:
    with open(debug_file, 'w') as f:
        f.write("Hook started\n")
except:
    pass

def log_debug(msg):
    try:
        with open(debug_file, 'a') as f:
            f.write(f"{msg}\n")
    except:
        pass
    print(msg)

def safe_add_path(path, description):
    """إضافة مسار بأمان إلى sys.path مع معالجة الأخطاء"""
    try:
        if os.path.exists(path) and path not in sys.path:
            sys.path.insert(0, path)
            log_debug(f"Added {description} to sys.path: {path}")
        else:
            log_debug(f"{description} path not found or already in sys.path: {path}")
    except Exception as e:
        log_debug(f"Failed to add {description} to sys.path: {e}")

def safe_set_env(key, value, description):
    """تعيين متغير البيئة بأمان مع معالجة الأخطاء"""
    try:
        os.environ[key] = value
        log_debug(f"Set {description}: {key}={value}")
    except Exception as e:
        log_debug(f"Failed to set {description}: {e}")

if hasattr(sys, '_MEIPASS'):
    try:
        app_dir = sys._MEIPASS
        log_debug(f"PyInstaller app directory: {app_dir}")

        # Ensure the app directory exists and is accessible
        if not os.path.exists(app_dir):
            log_debug(f"PyInstaller app directory does not exist: {app_dir}")
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
        # PyInstaller's collect_all may put files in _tcl_data instead of tcl8.6
        tcl_paths_to_check = [
            os.path.join(app_dir, '_tcl_data'),  # collect_all location
            os.path.join(app_dir, 'tcl8.6'),     # traditional location
            os.path.join(app_dir, 'tcl')
        ]
        
        tk_paths_to_check = [
            os.path.join(app_dir, '_tk_data'),   # collect_all location
            os.path.join(app_dir, 'tk8.6'),      # traditional location
            os.path.join(app_dir, 'tk')
        ]
        
        tcl_path = None
        for path in tcl_paths_to_check:
            if os.path.exists(path):
                tcl_path = path
                log_debug(f"Found TCL at: {tcl_path}")
                break
        
        tk_path = None
        for path in tk_paths_to_check:
            if os.path.exists(path):
                tk_path = path
                log_debug(f"Found TK at: {tk_path}")
                break

        if tcl_path and os.path.exists(tcl_path):
            safe_set_env('TCL_LIBRARY', tcl_path, "TCL_LIBRARY")
            # Debug: Recursive list
            log_debug(f"Listing {tcl_path}:")
            for root, dirs, files in os.walk(tcl_path):
                for file in files:
                    log_debug(os.path.join(root, file))
        else:
            log_debug(f"TCL path not found in any of: {tcl_paths_to_check}")

        if tk_path and os.path.exists(tk_path):
            safe_set_env('TK_LIBRARY', tk_path, "TK_LIBRARY")
        else:
            log_debug(f"TK path not found in any of: {tk_paths_to_check}")

        # Set VLC environment variables for self-contained operation
        vlc_path = os.path.join(app_dir, 'vlc')
        vlc_plugins_path = os.path.join(vlc_path, 'plugins')

        log_debug(f"VLC setup: app_dir={app_dir}, vlc_path={vlc_path}, plugins={vlc_plugins_path}")

        if os.path.exists(vlc_path):
            log_debug("VLC directory exists, setting environment variables")

            # CRITICAL: Add VLC directory to PATH FIRST before any VLC imports
            current_path = os.environ.get('PATH', '')
            if vlc_path not in current_path:
                new_path = vlc_path + os.pathsep + current_path
                safe_set_env('PATH', new_path, "PATH (VLC dir first)")
                log_debug(f"Added VLC directory to PATH: {vlc_path}")

            # Set VLC_PLUGIN_PATH to point to bundled plugins
            safe_set_env('VLC_PLUGIN_PATH', vlc_plugins_path, "VLC_PLUGIN_PATH")
            log_debug(f"Set VLC_PLUGIN_PATH to {vlc_plugins_path}")

            # Add app directory to PATH as well for other DLLs
            if app_dir not in os.environ.get('PATH', ''):
                current_path = os.environ.get('PATH', '')
                new_path = app_dir + os.pathsep + current_path
                safe_set_env('PATH', new_path, "PATH (with app dir)")
                log_debug(f"Added app directory to PATH: {app_dir}")

            # Set VLC_DATA_PATH if locale directory exists
            vlc_locale_path = os.path.join(vlc_path, 'locale')
            if os.path.exists(vlc_locale_path):
                safe_set_env('VLC_DATA_PATH', vlc_path, "VLC_DATA_PATH")
                log_debug(f"Set VLC_DATA_PATH to {vlc_path}")

            # Additional VLC environment variables for better compatibility
            safe_set_env('VLC_LOCALES_PATH', vlc_locale_path, "VLC_LOCALES_PATH")
            safe_set_env('VLC_CONFIG_PATH', app_dir, "VLC_CONFIG_PATH")

            log_debug("VLC environment variables configured for bundled operation")
        else:
            log_debug("VLC directory does not exist - will try to use system VLC")

        log_debug("Runtime hook initialization completed successfully")

    except Exception as e:
        log_debug(f"Critical error in runtime hook: {e}")
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
                log_debug(f"الوصول إلى _MEIPASS ناجح: {app_dir}")
            except (OSError, PermissionError, IOError) as lock_error:
                log_debug(f"قفل محتمل في _MEIPASS: {app_dir}. خطأ: {lock_error}")
                log_debug("اقتراح: قم بتنظيف يدوي لمجلدات _MEI في %TEMP% لإصلاح مشاكل إعادة التشغيل")
        else:
            log_debug(f"_MEIPASS غير موجود: {app_dir}. قد يفشل تشغيل المفسر المضمن")
