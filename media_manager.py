# -*- coding: utf-8 -*-

"""
media_manager.py
يحتوي هذا الملف على الكلاسات المتعلقة بالإشعارات والصوت
"""

import os
import logging
import threading
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
        self.default_sounds = {'fajr': 'sounds/adhan_mekka.wma', 'normal': 'sounds/adhan_mekka.wma', 'notification': 'sounds/notification.wav'}
    
    def play_adhan(self, prayer_name: str, custom_file: str = None, volume: float = 0.7):
        """تشغيل صوت الأذان"""
        try:
            sound_file = custom_file
            if not sound_file:
                if prayer_name == 'الفجر':
                    sound_file = self.default_sounds['fajr']
                else:
                    sound_file = self.default_sounds['normal']
            
            if not os.path.exists(sound_file):
                logger.warning(f"ملف الصوت غير موجود {sound_file}")
                return False
            
            threading.Thread(target=playsound, args=(sound_file,), kwargs={'block': True}).start()
            logger.info(f"تم تشغيل أذان {prayer_name}")
            return True
            
        except Exception as e:
            logger.error(f"خطأ في تشغيل الصوت {e}")
            return False
    
    def stop_adhan(self):
        """إيقاف تشغيل الأذان"""
        logger.info("playsound لا يدعم إيقاف الصوت مباشرة")

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
