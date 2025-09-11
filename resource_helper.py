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

def initialize_resources():
    """
    تحضير الموارد عند بدء البرنامج. يجب استدعاؤها مرة واحدة عند بدء التشغيل.
    """
    logger.info("Initializing and verifying resources...")
    extract_resources()
    logger.info("Resource initialization complete.")

# --- Debugging Functions ---
def debug_resource_paths():
    """طباعة مسارات التصحيح"""
    print("--- Debug Resource Paths ---")
    print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
    print(f"os.path.abspath('.'): {os.path.abspath('.')}")
    print(f"get_app_data_dir(): {get_app_data_dir()}")
    print(f"Sounds folder path: {get_sounds_dir()}")
    print("--------------------------")

def list_available_files(subdirectory):
    """عرض الملفات المتاحة في مجلد فرعي للتصحيح"""
    path_to_check = get_working_path(subdirectory)
    print(f"--- Listing files in '{path_to_check}' ---")
    
    if os.path.exists(path_to_check) and os.path.isdir(path_to_check):
        try:
            files = os.listdir(path_to_check)
            if files:
                for f in files:
                    print(f"  - {f}")
            else:
                print("  (No files found)")
        except Exception as e:
            print(f"  Error listing files: {e}")
    else:
        print("  (Directory does not exist)")
    print("------------------------------------")
