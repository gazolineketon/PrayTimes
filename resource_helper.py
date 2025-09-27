import os
import sys
import shutil
import tempfile
import atexit
from pathlib import Path

def get_resource_path(relative_path):
    """Gets the path to a resource, using the script directory."""
    # Always use the script directory to avoid temp folder issues
    base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

def get_app_data_dir():
    """إنشاء مجلد دائم للبيانات في APPDATA"""
    if sys.platform.startswith('win'):
        app_data = os.environ.get('APPDATA', '')
        app_dir = os.path.join(app_data, 'PrayTimes')
    else:
        home = os.path.expanduser('~')
        app_dir = os.path.join(home, '.praytimes')
    
    Path(app_dir).mkdir(parents=True, exist_ok=True)
    return app_dir

def cleanup_temp_directories():
    """تنظيف المجلدات المؤقتة القديمة لـ PyInstaller بحذر"""
    try:
        temp_dir = tempfile.gettempdir()
        import time
        current_time = time.time()

        # البحث عن مجلدات _MEI القديمة جداً فقط (أسبوع)
        for item in os.listdir(temp_dir):
            if item.startswith('_MEI') and os.path.isdir(os.path.join(temp_dir, item)):
                mei_path = os.path.join(temp_dir, item)
                try:
                    # محاولة حذف المجلد إذا كان قديماً جداً (أكثر من أسبوع)
                    folder_age = current_time - os.path.getctime(mei_path)
                    if folder_age > 604800:  # أسبوع واحد
                        # التحقق من الصلاحيات قبل المحاولة
                        try:
                            test_file = os.path.join(mei_path, 'test_write.tmp')
                            with open(test_file, 'w') as f:
                                f.write('test')
                            os.remove(test_file)
                            # إذا تمكنا من الكتابة، نحاول الحذف
                            shutil.rmtree(mei_path, ignore_errors=True)
                            if not os.path.exists(mei_path):
                                print(f"تم حذف المجلد المؤقت القديم جداً: {mei_path}")
                        except (OSError, PermissionError):
                            # لا توجد صلاحيات، نتجاهل
                            pass
                except Exception as e:
                    # تجاهل الأخطاء في التنظيف
                    pass

        # تنظيف مجلدات PrayTimes المؤقتة القديمة
        praytimes_temp = os.path.join(temp_dir, 'PrayTimes')
        if os.path.exists(praytimes_temp):
            try:
                # محاولة حذف المجلد إذا كان قديماً جداً (أكثر من يومين)
                folder_age = current_time - os.path.getctime(praytimes_temp)
                if folder_age > 172800:  # يومان
                    shutil.rmtree(praytimes_temp, ignore_errors=True)
                    print(f"تم حذف مجلد PrayTimes المؤقت القديم: {praytimes_temp}")
            except Exception as e:
                print(f"فشل في حذف مجلد PrayTimes المؤقت: {e}")
    except Exception:
        # تجاهل أي أخطاء في عملية التنظيف
        pass

def register_cleanup():
    """تسجيل دالة التنظيف لتعمل عند إغلاق البرنامج"""
    atexit.register(cleanup_temp_directories)

def extract_resources():
    """نسخ الملفات من الـ executable إلى مجلد دائم مع التحديث"""
    app_dir = get_app_data_dir()
    
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
            
            if not os.path.exists(source_path):
                print(f"لم يتم العثور على {resource_path}")
                continue

            if os.path.isdir(source_path):
                # For directories, create dest dir and copy contents file-by-file
                os.makedirs(dest_path, exist_ok=True)
                for item in os.listdir(source_path):
                    s_item = os.path.join(source_path, item)
                    d_item = os.path.join(dest_path, item)
                    if not os.path.isdir(s_item): # Ignore sub-directories for safety
                        shutil.copy2(s_item, d_item)
                extracted_paths[resource_path] = dest_path
            else:
                # For files, copy2 overwrites safely.
                shutil.copy2(source_path, dest_path)
                extracted_paths[resource_path] = dest_path
            
            print(f"تم نسخ وتحديث {resource_path} إلى {dest_path}")

        except Exception as e:
            print(f"خطأ في نسخ {resource_path}: {e}")
    
    return extracted_paths

def get_working_path(relative_path):
    """Gets the correct path for a file, whether in development or after packaging."""
    # 1. Check in the APPDATA directory first (for deployed app)
    app_dir = get_app_data_dir()
    app_path = os.path.join(app_dir, relative_path)
    if os.path.exists(app_path):
        return app_path

    # 2. Fallback to bundled/local resource path
    return get_resource_path(relative_path)

# استخدم هذه الدالة في بداية البرنامج
def initialize_resources():
    """تحضير الموارد عند بدء البرنامج"""
    print("تحضير الموارد...")
    extracted = extract_resources()
    print(f"تم تحضير {len(extracted)} مورد")
    return extracted
