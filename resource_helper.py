import os
import sys
import shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_app_data_dir():
    """إنشاء مجلد دائم للبيانات في APPDATA أو home"""
    app_name = "PrayTimes"
    if sys.platform.startswith('win'):
        app_data_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
    else:
        app_data_dir = os.path.expanduser('~')
    
    app_dir = os.path.join(app_data_dir, app_name)
    Path(app_dir).mkdir(parents=True, exist_ok=True)
    return app_dir

def get_resource_path(relative_path):
    """الحصول على مسار الملفات المدمجة في PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def extract_resources():
    """
    نسخ الملفات من الـ executable (أو مجلد التطوير) إلى مجلد دائم.
    هذا يضمن أن الملفات قابلة للكتابة والوصول إليها دائمًا.
    """
    app_dir = get_app_data_dir()
    
    resources_to_extract = [
        ('sounds', 'sounds'),
        ('world_cities', 'world_cities'),
        ('countries.json', 'countries.json'),
        ('pray_logo.png', 'pray_logo.png'),
        ('pray_times.ico', 'pray_times.ico')
    ]
    
    for resource_path, dest_name in resources_to_extract:
        source_path = get_resource_path(resource_path)
        dest_path = os.path.join(app_dir, dest_name)
        
        try:
            if not os.path.exists(source_path):
                logger.warning(f"Resource not found at source: {source_path}")
                continue

            # للمجلدات، انسخ إذا لم يكن موجودًا أو قم بتحديثه إذا لزم الأمر
            if os.path.isdir(source_path):
                if not os.path.exists(dest_path):
                    shutil.copytree(source_path, dest_path)
                    logger.info(f"Copied directory {resource_path} to {dest_path}")
            # للملفات، انسخ إذا لم يكن موجودًا أو إذا كان المصدر أحدث
            else:
                if not os.path.exists(dest_path) or os.path.getmtime(source_path) > os.path.getmtime(dest_path):
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"Copied file {resource_path} to {dest_path}")

        except Exception as e:
            logger.error(f"Failed to copy resource {resource_path}: {e}", exc_info=True)

def get_working_path(relative_path):
    """
    الحصول على المسار الصحيح للملف من مجلد بيانات التطبيق.
    هذا هو المصدر الموثوق للملفات بعد استخراجها.
    """
    app_dir = get_app_data_dir()
    return os.path.join(app_dir, relative_path)

def get_sounds_dir():
    """الحصول على المسار إلى مجلد الأصوات في مجلد بيانات التطبيق"""
    return get_working_path('sounds')

def set_tcl_tk_env_vars():
    """
    تعيين متغيرات البيئة لـ TCL و TK إذا كان التطبيق مجمداً.
    هذا يضمن أن Tkinter يمكنه العثور على مكتباته.
    """
    if getattr(sys, 'frozen', False):
        # المسار إلى مجلد _MEIPASS الذي أنشأه PyInstaller
        base_path = sys._MEIPASS
        
        # تحديد مسارات مكتبات Tcl و Tk
        tcl_library_path = os.path.join(base_path, '_tcl_data', 'tcl8.6')
        tk_library_path = os.path.join(base_path, '_tcl_data', 'tk8.6')
        
        # تعيين متغيرات البيئة
        if os.path.isdir(tcl_library_path):
            os.environ['TCL_LIBRARY'] = tcl_library_path
            logger.info(f"TCL_LIBRARY set to: {tcl_library_path}")

        if os.path.isdir(tk_library_path):
            os.environ['TK_LIBRARY'] = tk_library_path
            logger.info(f"TK_LIBRARY set to: {tk_library_path}")

def initialize_resources():
    """
    تحضير الموارد عند بدء البرنامج. يجب استدعاؤها مرة واحدة عند بدء التشغيل.
    """
    set_tcl_tk_env_vars()
    logger.info("Initializing and verifying resources...")
    extract_resources()
    logger.info("Resource initialization complete.")


