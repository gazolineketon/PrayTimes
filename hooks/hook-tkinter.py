# hook-tkinter.py
# Hook مخصص لـ tkinter لضمان تضمين مكتبات TCL/Tk

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

def get_tcl_tk_files():
    """جمع ملفات TCL/Tk من Python المستخدم في البناء"""
    try:
        # استخدام sys.prefix بدلاً من sys.base_prefix للبيئة المستخدمة في البناء
        python_path = sys.prefix
        print(f"Python path for tkinter: {python_path}")
        
        files = []
        
        # البحث عن مجلدات TCL/Tk في المسارات المختلفة
        possible_tcl_paths = [
            os.path.join(python_path, 'Library', 'lib', 'tcl8.6'),
            os.path.join(python_path, 'tcl', 'tcl8.6'),
            os.path.join(python_path, 'Lib', 'tcl8.6'),
        ]
        
        possible_tk_paths = [
            os.path.join(python_path, 'Library', 'lib', 'tk8.6'),
            os.path.join(python_path, 'tcl', 'tk8.6'),
            os.path.join(python_path, 'Lib', 'tk8.6'),
        ]
        
        # إضافة مجلدات TCL
        tcl_added = False
        for tcl_path in possible_tcl_paths:
            if os.path.exists(tcl_path):
                files.append((tcl_path, 'tcl8.6'))
                print(f"تم إضافة مجلد TCL: {tcl_path}")
                tcl_added = True
                break
        
        if not tcl_added:
            print(f"تحذير: لم يتم العثور على TCL 8.6 في {python_path}")
        
        # إضافة مجلدات Tk
        tk_added = False
        for tk_path in possible_tk_paths:
            if os.path.exists(tk_path):
                files.append((tk_path, 'tk8.6'))
                print(f"تم إضافة مجلد Tk: {tk_path}")
                tk_added = True
                break
        
        if not tk_added:
            print(f"تحذير: لم يتم العثور على Tk 8.6 في {python_path}")
        
        # إضافة ملفات DLL الأساسية لـ TCL/Tk
        tcl_dll_paths = [
            os.path.join(python_path, 'Library', 'bin', 'tcl86.dll'),
            os.path.join(python_path, 'tcl', 'tcl8.6', 'tcl86.dll'),
        ]
        
        tk_dll_paths = [
            os.path.join(python_path, 'Library', 'bin', 'tk86.dll'),
            os.path.join(python_path, 'tcl', 'tk8.6', 'tk86.dll'),
        ]
        
        # إضافة ملف tcl86.dll
        for tcl_dll_path in tcl_dll_paths:
            if os.path.exists(tcl_dll_path):
                files.append((tcl_dll_path, '.'))
                print(f"تم إضافة TCL DLL: {tcl_dll_path}")
                break
        
        # إضافة ملف tk86.dll
        for tk_dll_path in tk_dll_paths:
            if os.path.exists(tk_dll_path):
                files.append((tk_dll_path, '.'))
                print(f"تم إضافة Tk DLL: {tk_dll_path}")
                break
        
        return files
        
    except Exception as e:
        print(f"خطأ في جمع ملفات TCL/Tk: {e}")
        return []

# جمع البيانات المطلوبة
datas = get_tcl_tk_files()

# إضافة ملفات tkinter الأساسية
try:
    import tkinter
    tkinter_dir = os.path.dirname(tkinter.__file__)
    if os.path.exists(tkinter_dir):
        datas.append((tkinter_dir, 'tkinter'))
        print(f"تم إضافة مجلد tkinter: {tkinter_dir}")
except Exception as e:
    print(f"خطأ في إضافة مجلد tkinter: {e}")

# إضافة ملفات _tkinter من مسارات متعددة
try:
    import _tkinter
    _tkinter_paths = [
        os.path.join(sys.prefix, 'DLLs', '_tkinter.pyd'),
        os.path.join(sys.prefix, '_tkinter.pyd'),
    ]
    
    for _tkinter_path in _tkinter_paths:
        if os.path.exists(_tkinter_path):
            datas.append((_tkinter_path, '.'))
            print(f"تم إضافة _tkinter.pyd: {_tkinter_path}")
            break
except Exception as e:
    print(f"خطأ في إضافة _tkinter: {e}")

print(f"تم جمع {len(datas)} ملف/مجلد لـ tkinter")
