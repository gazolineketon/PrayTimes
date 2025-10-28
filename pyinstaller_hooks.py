
# pyinstaller_hooks.py
# إعداد خطافات PyInstaller المخصصة

import os
import sys

# إنشاء مجلد الخطافات إذا لم يكن موجودًا
hooks_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hooks')
if not os.path.exists(hooks_dir):
    os.makedirs(hooks_dir)

# ملفات الخطافات مُعدة مسبقًا في مجلد الخطافات
print("ملفات الخطافات جاهزة في مجلد hooks")

# إضافة مسار الخطافات إلى متغيرات البيئة
if hooks_dir not in os.environ.get('PYINSTALLER_HOOKSPATH', ''):
    os.environ['PYINSTALLER_HOOKSPATH'] = hooks_dir
    print(f"تم إضافة مسار الخطافات: {hooks_dir}")
