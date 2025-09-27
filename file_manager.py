import os
import sys
import json
import atexit
from contextlib import contextmanager
from pathlib import Path

class SafeFileHandler:
    """كلاس لإدارة الملفات بطريقة آمنة"""
    
    def __init__(self):
        self.open_files = []
    
    def open(self, filename, mode='r', encoding='utf-8'):
        """فتح ملف مع التتبع"""
        try:
            file_obj = open(filename, mode, encoding=encoding)
            self.open_files.append(file_obj)
            return file_obj
        except Exception as e:
            print(f"خطأ في فتح {filename}: {e}")
            return None
    
    def close(self, file_obj):
        """إغلاق ملف مع إزالته من التتبع"""
        try:
            if file_obj in self.open_files:
                self.open_files.remove(file_obj)
            if not file_obj.closed:
                file_obj.close()
        except:
            pass

    def close_all(self):
        """إغلاق جميع الملفات"""
        for file_obj in self.open_files.copy():
            try:
                if not file_obj.closed:
                    file_obj.close()
            except:
                pass
        self.open_files.clear()

# إنشاء كائن عام لإدارة الملفات
file_handler = SafeFileHandler()

@contextmanager
def safe_open(filename, mode='r', encoding='utf-8'):
    """فتح ملف بطريقة آمنة مع ضمان الإغلاق"""
    file_obj = None
    try:
        file_obj = file_handler.open(filename, mode, encoding=encoding)
        yield file_obj
    finally:
        if file_obj:
            file_handler.close(file_obj)

def load_json_safely(filepath):
    """تحميل ملف JSON بطريقة آمنة"""
    try:
        with safe_open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"خطأ في تحميل {filepath}: {e}")
        return {}

def save_json_safely(data, filepath):
    """حفظ ملف JSON بطريقة آمنة"""
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with safe_open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطأ في حفظ {filepath}: {e}")
        return False

def read_text_file_safely(filepath):
    """قراءة ملف نصي بطريقة آمنة"""
    try:
        with safe_open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"خطأ في قراءة {filepath}: {e}")
        return ""

def cleanup_temp_files():
    """تنظيف الملفات المؤقتة"""
    file_handler.close_all()
    
    if hasattr(sys, '_MEIPASS'):
        import time
        time.sleep(0.5)

# تسجيل دالة التنظيف لتعمل عند إغلاق البرنامج
atexit.register(cleanup_temp_files)
