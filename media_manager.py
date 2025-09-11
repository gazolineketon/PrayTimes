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
from resource_helper import get_working_path

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
        self.player = None
    

    def play_sound(self, sound_file: str, volume: float = 0.7):
        """تشغيل ملف صوتي باستخدام مكتبة vlc مع التحكم الكامل"""
        try:
            import vlc
            if self.player:
                self.stop_sound()

            # إذا لم يكن المسار مطلقاً، افترض أنه نسبي لمجلد المشروع
            if not os.path.isabs(sound_file):
                sound_path = get_working_path(sound_file)
            else:
                sound_path = sound_file

            if not os.path.exists(sound_path):
                logger.warning(f"ملف الصوت غير موجود {sound_path}")
                # محاولة تشغيل الصوت الافتراضي كحل بديل
                default_notification = get_working_path('sounds/notification.wav')
                if os.path.exists(default_notification):
                    sound_path = default_notification
                else:
                    # عرض الملفات المتاحة للتصحيح
                    try:
                        from resource_helper import list_available_files
                        list_available_files("sounds")
                    except ImportError:
                        pass # تجاهل إذا لم تكن متوفرة
                    return False

            self.player = vlc.MediaPlayer(sound_path)
            self.player.audio_set_volume(int(volume * 100))
            self.player.play()
            logger.info(f"تم تشغيل الصوت {sound_path}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تشغيل الصوت عبر vlc: {e}")
            return False
    
    def stop_sound(self):
        """إيقاف تشغيل الصوت عبر vlc"""
        if self.player:
            self.player.stop()
            self.player = None
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
