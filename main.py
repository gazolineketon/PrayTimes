# -*- coding: utf-8 -*-

"""
main.py
نقطة الدخول الرئيسية لتطبيق مواقيت الصلاة
"""

__version__ = "0.41.0"

# إعداد متغيرات البيئة لـ tkinter قبل الاستيراد
import os
import sys

if getattr(sys, 'frozen', False):
    # في حالة التطبيق المجمد، إعداد مسارات tkinter
    try:
        base_path = sys._MEIPASS
        tcl_path = os.path.join(base_path, 'tcl')
        tk_path = os.path.join(base_path, 'tk')

        if os.path.exists(tcl_path):
            os.environ['TCL_LIBRARY'] = tcl_path
        if os.path.exists(tk_path):
            os.environ['TK_LIBRARY'] = tk_path

        # إعداد TCLLIBPATH للمسارات الإضافية
        tcl_lib_path = os.path.join(base_path, 'tcl8.6')
        if os.path.exists(tcl_lib_path):
            os.environ['TCLLIBPATH'] = tcl_lib_path

    except Exception as e:
        print(f"تحذير: فشل في إعداد متغيرات البيئة لـ tkinter: {e}")

import logging
import sys
from tkinter import messagebox
import json
from resource_helper import initialize_resources, register_cleanup, cleanup_temp_directories
from config import LOG_FILE, SETTINGS_FILE, Translator, initialize_app_directories
from temp_manager import register_temp_cleanup
from main_app_ui import EnhancedPrayerTimesApp
from media_manager import NOTIFICATIONS_AVAILABLE
from prayer_logic import NTPLIB_AVAILABLE

from signal_handler import setup_signal_handlers
from file_manager import file_handler
import atexit


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
    logger = logging.getLogger(__name__)
    try:
        check_dependencies()       
        app = EnhancedPrayerTimesApp(version=__version__)
        # إعداد معالجات الإغلاق
        setup_signal_handlers(app)
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
    initialize_app_directories()
    cleanup_temp_directories()  # تنظيف المجلدات المؤقتة القديمة عند البدء
    setup_logging()
    register_cleanup()  # تسجيل دالة تنظيف المجلدات المؤقتة الأساسية
    register_temp_cleanup()  # تسجيل المدير المتقدم للمجلدات المؤقتة
    initialize_resources()
    main()
