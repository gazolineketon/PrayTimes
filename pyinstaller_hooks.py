
# pyinstaller_hooks.py
# إعداد خطافات PyInstaller المخصصة

import os
import sys

# إنشاء مجلد الخطافات إذا لم يكن موجودًا
hooks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hooks')
if not os.path.exists(hooks_dir):
    os.makedirs(hooks_dir)

# نسخ الخطافات المخصصة إلى مجلد الخطافات
import shutil
try:
    shutil.copy('hook-glob.py', os.path.join(hooks_dir, 'hook-glob.py'))
    shutil.copy('hook-pathlib.py', os.path.join(hooks_dir, 'hook-pathlib.py'))
    print(f"تم نسخ الخطافات المخصصة إلى: {hooks_dir}")
except Exception as e:
    print(f"خطأ في نسخ الخطافات: {e}")

# إضافة مسار الخطافات إلى متغيرات البيئة
if hooks_dir not in os.environ.get('PYINSTALLER_HOOKSPATH', ''):
    os.environ['PYINSTALLER_HOOKSPATH'] = hooks_dir
    print(f"تم إضافة مسار الخطافات: {hooks_dir}")
