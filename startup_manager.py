# -*- coding: utf-8 -*-

"""
startup_manager.py
يحتوي هذا الملف على وظائف للتعامل مع تشغيل البرنامج مع بدء تشغيل ويندوز
"""

import sys
import os
import logging

logger = logging.getLogger(__name__)

def get_executable_path():
    """الحصول على مسار الملف التنفيذي للبرنامج"""
    if getattr(sys, 'frozen', False):
        # في حالة التطبيق المجمد (exe)
        return sys.executable
    else:
        # في حالة تشغيل البرنامج من Python
        return os.path.abspath(sys.argv[0])

def is_startup_enabled():
    """
    فحص ما إذا كان البرنامج مضافاً لبدء التشغيل
    Returns:
        bool: True إذا كان البرنامج في بدء التشغيل، False خلاف ذلك
    """
    if sys.platform != 'win32':
        logger.warning("وظيفة التشغيل مع بدء التشغيل متاحة لويندوز فقط")
        return False
    
    try:
        import winreg
        
        # فتح مفتاح السجل لبدء التشغيل
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "PrayTimes"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, app_name)
            winreg.CloseKey(key)
            
            # التحقق من أن المسار يطابق المسار الحالي
            current_path = get_executable_path()
            return value.strip('"') == current_path
            
        except FileNotFoundError:
            # المفتاح غير موجود
            return False
            
    except Exception as e:
        logger.error(f"خطأ في فحص حالة التشغيل التلقائي: {e}")
        return False

def enable_startup():
    """
    إضافة البرنامج إلى بدء تشغيل ويندوز
    Returns:
        bool: True إذا نجحت العملية، False خلاف ذلك
    """
    if sys.platform != 'win32':
        logger.warning("وظيفة التشغيل مع بدء التشغيل متاحة لويندوز فقط")
        return False
    
    try:
        import winreg
        
        # فتح مفتاح السجل لبدء التشغيل
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "PrayTimes"
        exe_path = get_executable_path()
        
        # إضافة علامات اقتباس حول المسار إذا كان يحتوي على مسافات
        if ' ' in exe_path:
            exe_path = f'"{exe_path}"'
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            
            logger.info(f"تم تفعيل التشغيل التلقائي: {exe_path}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في كتابة مفتاح السجل: {e}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في تفعيل التشغيل التلقائي: {e}")
        return False

def disable_startup():
    """
    إزالة البرنامج من بدء تشغيل ويندوز
    Returns:
        bool: True إذا نجحت العملية، False خلاف ذلك
    """
    if sys.platform != 'win32':
        logger.warning("وظيفة التشغيل مع بدء التشغيل متاحة لويندوز فقط")
        return False
    
    try:
        import winreg
        
        # فتح مفتاح السجل لبدء التشغيل
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "PrayTimes"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, app_name)
            winreg.CloseKey(key)
            
            logger.info("تم إيقاف التشغيل التلقائي")
            return True
            
        except FileNotFoundError:
            # المفتاح غير موجود، لا حاجة لفعل شيء
            logger.info("التشغيل التلقائي غير مفعل مسبقاً")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في حذف مفتاح السجل: {e}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إيقاف التشغيل التلقائي: {e}")
        return False

def toggle_startup(enable):
    """
    تبديل حالة التشغيل مع بدء التشغيل
    Args:
        enable (bool): True لتفعيل، False لإيقاف
    Returns:
        bool: True إذا نجحت العملية، False خلاف ذلك
    """
    if enable:
        return enable_startup()
    else:
        return disable_startup()
