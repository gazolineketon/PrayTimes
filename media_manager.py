# -*- coding: utf-8 -*-

"""
media_manager.py
يحتوي هذا الملف على الكلاسات المتعلقة بالإشعارات والصوت
"""

import os
import logging
import sys
import threading
import time
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

# أنظمة الإشعار المتعددة
Plyer_AVAILABLE = False
Win10Toast_AVAILABLE = False
Tkinter_AVAILABLE = True  # دائماً متاح مع tkinter

# محاولة استيراد plyer
try:
    from plyer import notification
    Plyer_AVAILABLE = True
    logger.info("plyer متوفر للإشعارات")
except ImportError:
    logger.warning("plyer غير متوفر - الإشعارات معطلة")
    # بعد تعريف Plyer_AVAILABLE
    Plyer_AVAILABLE = False

# إضافة متغير التوافق مع الإصدارات السابقة
NOTIFICATIONS_AVAILABLE = Plyer_AVAILABLE

# محاولة استيراد win10toast-persist للإشعارات المتقدمة على ويندوز
if sys.platform == "win32":
    try:
        from win10toast_persist import ToastNotifier
        Win10Toast_AVAILABLE = True
        logger.info("win10toast-persist متوفر للإشعارات على ويندوز")
    except ImportError:
        logger.warning("win10toast-persist غير متوفر - سيتم استخدام tkinter fallback")
        Win10Toast_AVAILABLE = False

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
                    return False

            self.player = vlc.MediaPlayer(sound_path)
            self.player.audio_set_volume(int(volume * 100))
            self.player.play()
            logger.info(f"تم تشغيل الصوت {sound_path}")
            return True
        except Exception as e:
            logger.error(f"خطأ في تشغيل الصوت عبر vlc {e}")
            return False
    
    def stop_sound(self):
        """إيقاف تشغيل الصوت عبر vlc"""
        if self.player:
            self.player.stop()
            self.player = None
            logger.info("تم إيقاف الصوت")

class NotificationManager:
    """مدير الإشعارات مع دعم متعدد المنصات"""
    
    def __init__(self, settings: Settings, translator: Translator):
        self.settings = settings
        self._ = translator.get
        self.toaster = None
        
        # تهيئة win10toast-persist إذا كان متاحاً
        if Win10Toast_AVAILABLE:
            try:
                self.toaster = ToastNotifier()
                logger.info("تم تهيئة ToastNotifier لنظام ويندوز")
            except Exception as e:
                logger.error(f"خطأ في تهيئة ToastNotifier {e}")
                self.toaster = None
    
    def send_notification(self, title: str, message: str, timeout: int = 10):
        """إرسال إشعار باستخدام أفضل نظام متاح"""
        if not self.settings.notifications_enabled:
            return
        
        # محاولة استخدام plyer أولاً
        if Plyer_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=timeout,
                    app_name=self._("prayer_times")
                )
                logger.info(f"تم إرسال إشعار عبر plyer {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر plyer {e}")
        
        # محاولة استخدام win10toast-persist على ويندوز
        if Win10Toast_AVAILABLE and self.toaster:
            try:
                self.toaster.show_toast(
                    title,
                    message,
                    duration=timeout,
                    threaded=True
                )
                logger.info(f"تم إرسال إشعار عبر win10toast: {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر win10toast: {e}")
        
        # استخدام tkinter كحل بديل
        if Tkinter_AVAILABLE:
            try:
                self._show_tkinter_notification(title, message, timeout)
                logger.info(f"تم إرسال إشعار عبر tkinter: {title}")
                return
            except Exception as e:
                logger.error(f"فشل إرسال إشعار عبر tkinter: {e}")
    
    def _show_tkinter_notification(self, title: str, message: str, timeout: int = 10):
        """إظهار إشعار بسيط باستخدام tkinter"""
        import tkinter as tk
        from tkinter import messagebox
        
        # إنشاء نافذة منبثقة بسيطة
        def show_popup():
            root = tk.Tk()
            root.withdraw()  # إخفاء النافذة الرئيسية
            messagebox.showinfo(title, message)
            root.destroy()
        
        # تشغيل النافذة في خيط منفصل لتجنب تجميد الواجهة
        thread = threading.Thread(target=show_popup)
        thread.daemon = True
        thread.start()
    
    def is_any_notification_available(self):
        """التحقق من توافر أي نظام إشعار"""
        return Plyer_AVAILABLE or Win10Toast_AVAILABLE or Tkinter_AVAILABLE