# -*- coding: utf-8 -*-

"""
main.py
نقطة الدخول الرئيسية لتطبيق مواقيت الصلاة
"""

__version__ = "0.52.0"

# إعداد متغيرات البيئة لـ tkinter قبل الاستيراد
import os
import sys
import logging

if getattr(sys, 'frozen', False):
    # في حالة التطبيق المجمد، إعداد مسارات TCL/TK المجمعة
    try:
        base_path = sys._MEIPASS
        print(f"التطبيق المجمد يعمل من: {base_path}")

        # إعداد مسارات TCL/TK المجمعة
        tcl86_path = os.path.join(base_path, 'tcl8.6')
        tk86_path = os.path.join(base_path, 'tk8.6')

        if os.path.exists(tcl86_path):
            os.environ['TCL_LIBRARY'] = tcl86_path
            print(f"تم إعداد TCL_LIBRARY: {tcl86_path}")
        else:
            print("لم يتم العثور على TCL 8.6 المجمع")

        if os.path.exists(tk86_path):
            os.environ['TK_LIBRARY'] = tk86_path
            print(f"تم إعداد TK_LIBRARY: {tk86_path}")
        else:
            print("لم يتم العثور على TK 8.6 المجمع")

    except Exception as e:
        print(f"تحذير: خطأ في إعداد البيئة المجمدة: {e}")
        # لا نخرج من البرنامج، فقط نستمر

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

class FlushingFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


def setup_logging():
    """إعداد التسجيل للتطبيق"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except (TypeError, AttributeError):
        pass

    # إعداد logger الجذر يدوياً
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # إضافة handler للملف
    file_handler = FlushingFileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # إضافة handler للـ console فقط في الوضع غير المجمد
    if not getattr(sys, 'frozen', False):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root_logger.addHandler(stream_handler)

def check_dependencies():
    """فحص التبعيات الاختيارية وإظهار تحذيرات"""
    import sys  # تأكيد توفر sys في هذه الدالة
    missing_features = []

    if not NOTIFICATIONS_AVAILABLE:
        missing_features.append("الإشعارات (plyer)")

    if not NTPLIB_AVAILABLE:
        missing_features.append("مزامنة الوقت (ntplib)")

    # فحص إضافي للتطبيقات المجمدة
    if getattr(sys, 'frozen', False):
        try:
            # التحقق من إمكانية الوصول للمجلد المؤقت
            if hasattr(sys, '_MEIPASS') and not os.path.exists(sys._MEIPASS):
                missing_features.append("الوصول للمجلد المؤقت (_MEIPASS)")
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"تحذير PyInstaller: {e}")

    if missing_features:
        logger = logging.getLogger(__name__)
        logger.warning(f"الميزات المعطلة {', '.join(missing_features)}")
        return False

    return True

def main():
    """الدالة الرئيسية"""
    import sys  # تأكيد توفر sys في هذه الدالة
    logger = logging.getLogger(__name__)
    try:
        # فحص وتنظيف أي مجلدات _MEI سابقة قبل بدء التطبيق
        if getattr(sys, 'frozen', False):
            try:
                from temp_manager import temp_manager
                logger.info("فحص المجلدات المؤقتة السابقة...")
                temp_manager.safe_cleanup_recent_mei(max_age=600)  # 10 دقائق
            except Exception as e:
                logger.warning(f"فشل في فحص المجلدات المؤقتة: {e}")

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

        # محاولة عرض رسالة خطأ باستخدام tkinter، مع fallback للـ console
        try:
            messagebox.showerror(_("fatal_error"), f'{_("fatal_app_error")} \n{e}')
        except Exception as tk_error:
            # Fallback للـ console إذا فشل tkinter
            print(f"\n{'='*50}")
            print("خطأ فادح في التطبيق!")
            print(f"الخطأ: {e}")
            print(f"خطأ tkinter: {tk_error}")
            print("\nيرجى التحقق من:")
            print("1. تثبيت Python بشكل صحيح")
            print("2. وجود ملفات tkinter")
            print("3. صلاحيات الكتابة في مجلد temp")
            print("4. إعادة بناء التطبيق باستخدام: pyinstaller main.spec --clean")
            print(f"{'='*50}\n")

            # محاولة انتظار المستخدم فقط إذا كان هناك console متاح
            try:
                if hasattr(sys, 'stdin') and sys.stdin.isatty():
                    input("اضغط Enter للخروج...")
                else:
                    # في حالة عدم وجود console، انتظار قصير ثم خروج
                    import time
                    time.sleep(5)
            except:
                # إذا فشل أي شيء، انتظار قصير ثم خروج
                import time
                time.sleep(2)

if __name__ == "__main__":
    initialize_app_directories()
    setup_logging()
    cleanup_temp_directories()  # تنظيف المجلدات المؤقتة القديمة عند البدء
    register_cleanup()  # تسجيل دالة تنظيف المجلدات المؤقتة الأساسية
    register_temp_cleanup()  # تسجيل المدير المتقدم للمجلدات المؤقتة
    initialize_resources()
    main()
