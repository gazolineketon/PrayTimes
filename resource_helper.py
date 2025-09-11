import os
import sys
import shutil
from pathlib import Path

def get_resource_path(relative_path):
    """الحصول على مسار الملفات المدمجة في PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_app_data_dir():
    """إنشاء مجلد دائم للبيانات في APPDATA"""
    if sys.platform.startswith('win'):
        app_data = os.environ.get('APPDATA', '')
        app_dir = os.path.join(app_data, 'Praytimes')
    else:
        home = os.path.expanduser('~')
        app_dir = os.path.join(home, '.praytimes')
    
    Path(app_dir).mkdir(parents=True, exist_ok=True)
    return app_dir

def extract_resources():
    """نسخ الملفات من الـ executable إلى مجلد دائم"""
    app_dir = get_app_data_dir()
    
    # قائمة الملفات والمجلدات للنسخ
    resources_to_extract = [
        ('sounds', 'sounds'),
        ('world_cities', 'world_cities'),
        ('countries.json', 'countries.json'),
        ('pray_logo.png', 'pray_logo.png'),
        ('pray_times.ico', 'pray_times.ico')
    ]
    
    extracted_paths = {}
    
    for resource_path, dest_name in resources_to_extract:
        try:
            source_path = get_resource_path(resource_path)
            dest_path = os.path.join(app_dir, dest_name)
            
            if os.path.exists(source_path):
                if os.path.isdir(source_path):
                    # نسخ مجلد كامل
                    if not os.path.exists(dest_path):
                        shutil.copytree(source_path, dest_path)
                    extracted_paths[resource_path] = dest_path
                else:
                    # نسخ ملف واحد
                    if not os.path.exists(dest_path):
                        shutil.copy2(source_path, dest_path)
                    extracted_paths[resource_path] = dest_path
                
                print(f"تم نسخ {resource_path} إلى {dest_path}")
            else:
                print(f"لم يتم العثور على {resource_path}")
                
        except Exception as e:
            print(f"خطأ في نسخ {resource_path}: {e}")
    
    return extracted_paths

def get_working_path(relative_path):
    """الحصول على المسار الصحيح للملف سواء في التطوير أو بعد التجميع"""
    # أولاً جرب المسار العادي (في وضع التطوير)
    if os.path.exists(relative_path):
        return relative_path
    
    # ثم جرب في مجلد البيانات
    app_dir = get_app_data_dir()
    app_path = os.path.join(app_dir, relative_path)
    if os.path.exists(app_path):
        return app_path
    
    # أخيراً جرب في الـ resource المدمج
    resource_path = get_resource_path(relative_path)
    if os.path.exists(resource_path):
        return resource_path
    
    # إذا لم نجد شيء، أعد المسار من مجلد البيانات
    return app_path

# استخدم هذه الدالة في بداية البرنامج
def initialize_resources():
    """تحضير الموارد عند بدء البرنامج"""
    print("تحضير الموارد...")
    extracted = extract_resources()
    print(f"تم تحضير {len(extracted)} مورد")
    return extracted

def debug_resource_paths():
    """طباعة مسارات التصحيح"""
    print("--- Debug Resource Paths ---")
    print(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'Not set')}")
    print(f"os.path.abspath('.'): {os.path.abspath('.')}")
    print(f"get_app_data_dir(): {get_app_data_dir()}")
    print("--------------------------")

def list_available_files(subdirectory):
    """عرض الملفات المتاحة في مجلد فرعي للتصحيح"""
    print(f"--- Available files in '{subdirectory}' ---")
    
    # المسار في وضع التطوير
    dev_path = os.path.join(os.path.abspath("."), subdirectory)
    if os.path.exists(dev_path):
        print(f"Dev path: {dev_path}")
        try:
            for f in os.listdir(dev_path):
                print(f"  - {f}")
        except Exception as e:
            print(f"  Error listing files: {e}")

    # المسار في مجلد البيانات
    app_data_path = os.path.join(get_app_data_dir(), subdirectory)
    if os.path.exists(app_data_path):
        print(f"App data path: {app_data_path}")
        try:
            for f in os.listdir(app_data_path):
                print(f"  - {f}")
        except Exception as e:
            print(f"  Error listing files: {e}")

    # المسار المدمج
    try:
        base_path = sys._MEIPASS
        resource_path = os.path.join(base_path, subdirectory)
        if os.path.exists(resource_path):
            print(f"Resource path (_MEIPASS): {resource_path}")
            try:
                for f in os.listdir(resource_path):
                    print(f"  - {f}")
            except Exception as e:
                print(f"  Error listing files: {e}")
    except Exception:
        pass
    print("------------------------------------")