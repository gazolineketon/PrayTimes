import signal
import sys
import os

def setup_signal_handlers(app):
    """إعداد معالجات الإشارات للإغلاق النظيف"""
    
    def signal_handler(signum, frame):
        """معالج الإشارات"""
        print(f"تم استلام إشارة {signum} - إغلاق البرنامج...")
        
        # استخدام معالج الإغلاق الخاص بالتطبيق
        if app and hasattr(app, 'root') and app.root.winfo_exists():
            app.root.event_generate('<<QuitApp>>')
        else:
            # إذا لم يكن التطبيق متاحًا، قم بالخروج مباشرة
            sys.exit(0)

    # تسجيل معالجات الإشارات
    if os.name == 'nt':  # Windows
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    else:  # Unix/Linux
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGHUP, signal_handler)

if __name__ == "__main__":
    # هذا الجزء مخصص للاختبار فقط
    # في التطبيق الفعلي، يجب استدعاء setup_signal_handlers مع نسخة من التطبيق
    pass