# -*- coding: utf-8 -*- 

"""
main.py
نقطة الدخول الرئيسية لتطبيق مواقيت الصلاة
"""

__version__ = "0.17.0"

import logging
import sys
from tkinter import messagebox
import json

from config import LOG_FILE, SETTINGS_FILE, Translator
from main_app_ui import EnhancedPrayerTimesApp
from media_manager import NOTIFICATIONS_AVAILABLE
from prayer_logic import NTPLIB_AVAILABLE

def setup_logging():
    """إعداد التسجيل للتطبيق"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (TypeError, AttributeError):
        pass

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - - %(name)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def check_dependencies():
    """فحص التبعيات الاختيارية وإظهار تحذيرات"""
    missing_features = []
    
    if not NOTIFICATIONS_AVAILABLE:
        missing_features.append("الإشعارات (plyer)")
    
    if not NTPLIB_AVAILABLE:
        missing_features.append("مزامنة الوقت (ntplib)")
    
    if missing_features:
        logger = logging.getLogger(__name__)
        logger.warning(f"الميزات المعطلة {', '.join(missing_features)}")
        return False
    
    return True

def main():
    """الدالة الرئيسية"""
    setup_logging()
    logger = logging.getLogger(__name__)
    try:
        check_dependencies()       
        app = EnhancedPrayerTimesApp()
        app.run()
        
    except Exception as e:
        lang = "ar"
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                settings_data = json.load(f)
                lang = settings_data.get("language", "ar")
        except Exception:
            pass
            
        translator = Translator(lang)
        _ = translator.get
        logger.critical(f"خطأ فادح في التطبيق {e}", exc_info=True)
        messagebox.showerror(_("fatal_error"), f'{_("fatal_app_error")} \n{e}')

if __name__ == "__main__":
    main()
