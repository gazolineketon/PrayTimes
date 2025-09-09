# -*- coding: utf-8 -*-

"""
media_manager.py
يحتوي هذا الملف على الكلاسات المتعلقة بالإشعارات والصوت
"""

import os
import logging
import multiprocessing
from config import Translator
from settings_manager import Settings

logger = logging.getLogger(__name__)

# محاولة استيراد المكتبات الاختيارية
try:
    from playsound import playsound
except ImportError:
    logger.warning("playsound غير متوفر - تشغيل الصوت معطل")
    def playsound(sound, block=True):
        pass

try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False
    logger.warning("plyer غير متوفر - الإشعارات معطلة")

class AdhanPlayer:
    """مشغل أصوات الأذان"""
    def __init__(self):
        self.process = None
    
    def play_sound(self, sound_file: str, volume: float = 0.7):
        """تشغيل ملف صوتي"""
        try:
            if self.process and self.process.is_alive():
                self.stop_sound()

            if not os.path.exists(sound_file):
                logger.warning(f"ملف الصوت غير موجود {sound_file}")
                # استخدام ملف صوت افتراضي إذا لم يتم العثور على الملف المحدد
                default_notification = 'sounds/notification.wav'
                if os.path.exists(default_notification):
                    sound_file = default_notification
                else:
                    return False

            self.process = multiprocessing.Process(target=playsound, args=(sound_file,), kwargs={'block': True})
            self.process.start()
            logger.info(f"تم تشغيل الصوت {sound_file}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تشغيل الصوت {e}")
            return False
    
    def stop_sound(self):
        """إيقاف تشغيل الصوت"""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process = None
            logger.info("تم إيقاف الصوت")

class NotificationManager:
    """مدير الإشعارات"""    
    def __init__(self, settings: Settings, translator: Translator):
        self.settings = settings
        self.is_available = NOTIFICATIONS_AVAILABLE
        self._ = translator.get
    
    def send_notification(self, title: str, message: str, timeout: int = 10):
        """إرسال إشعار"""
        if not self.is_available or not self.settings.notifications_enabled:
            return
        
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=timeout,
                app_name=self._("prayer_times")
            )
            logger.info(f"تم إرسال إشعار {title}")
        except Exception as e:
            logger.error(f"خطأ في إرسال الإشعار {e}")
