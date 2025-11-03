import winreg
import os
import sys
import logging

logger = logging.getLogger(__name__)

def ensure_app_in_registry():
    """
    Add the application to Windows Registry to ensure notification permissions
    """
    try:
        # Get the full path to the executable
        if getattr(sys, 'frozen', False):
            app_path = sys.executable
        else:
            app_path = os.path.abspath(__file__)
            
        app_name = "مواقيت الصلاة"
        
        # Registry key for notifications
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        
        try:
            # Try to create/open the key
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f"{key_path}\\{app_name}")
            
            # Set notification permissions
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ShowInActionCenter", 0, winreg.REG_DWORD, 1)
            
            winreg.CloseKey(key)
            logger.info("تم تسجيل التطبيق في سجل النظام للإشعارات")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تسجيل الإشعارات: {e}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إعداد الإشعارات: {e}")
        return False