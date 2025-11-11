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

# VLC مطلوب لتشغيل الصوت - سيتم التحقق من توفره عند الحاجة

# أنظمة الإشعار المتعددة - تعريف المتغيرات
Plyer_AVAILABLE = False
Win10Toast_AVAILABLE = False
PowerShell_AVAILABLE = False
Win32API_AVAILABLE = False
Tkinter_AVAILABLE = True  # دائماً متاح مع tkinter

# محاولة استيراد plyer
try:
    from plyer import notification
    Plyer_AVAILABLE = True
    logger.info("plyer متوفر للإشعارات")
except ImportError:
    logger.warning("plyer غير متوفر - الإشعارات معطلة")

# محاولة استيراد win10toast-persist للإشعارات المتقدمة على ويندوز
if sys.platform == "win32":
    try:
        from win10toast_persist import ToastNotifier
        Win10Toast_AVAILABLE = True
        logger.info("win10toast-persist متوفر للإشعارات على ويندوز")
    except ImportError:
        logger.warning("win10toast-persist غير متوفر - سيتم استخدام win32api fallback")
        Win10Toast_AVAILABLE = False

# محاولة استيراد win32api للإشعارات الأساسية على ويندوز
if sys.platform == "win32":
    try:
        import win32api
        import win32con
        import win32gui
        Win32API_AVAILABLE = True
        logger.info("win32api متوفر للإشعارات الأساسية على ويندوز")
    except ImportError:
        logger.warning("win32api غير متوفر")

# محاولة استيراد subprocess للإشعارات عبر PowerShell
if sys.platform == "win32":
    try:
        import subprocess
        PowerShell_AVAILABLE = True
        logger.info("PowerShell متوفر للإشعارات المتقدمة على ويندوز")
    except ImportError:
        logger.warning("subprocess غير متوفر")

# إضافة متغير التوافق مع الإصدارات السابقة بعد تعريف كل المتغيرات
NOTIFICATIONS_AVAILABLE = Plyer_AVAILABLE or Win10Toast_AVAILABLE or PowerShell_AVAILABLE or Win32API_AVAILABLE or Tkinter_AVAILABLE

class AdhanPlayer:
    """مشغل أصوات الأذان"""
    def __init__(self):
        self.player = None
        import atexit
        atexit.register(self.stop_sound)

        # إعداد VLC للعمل بشكل مستقل
        self._setup_vlc_paths()

    def _setup_vlc_paths(self):
        """إعداد مسارات VLC للعمل بشكل مستقل"""
        try:
            import os
            import sys

            # الحصول على مجلد التطبيق (يعمل مع PyInstaller والتشغيل العادي)
            if hasattr(sys, '_MEIPASS'):
                # التطبيق مبني بـ PyInstaller
                app_dir = sys._MEIPASS
            else:
                # تشغيل عادي من مجلد المشروع
                app_dir = os.path.dirname(os.path.abspath(__file__))

            # البحث عن مجلد VLC في مجلد التطبيق
            vlc_dir = None
            possible_vlc_dirs = [
                os.path.join(app_dir, 'vlc'),  # الأولوية الأولى - مجلد VLC المجمع
                os.path.join(app_dir, 'lib', 'vlc'),
                os.path.join(app_dir, 'VLC'),
                os.path.join(app_dir, 'plugins'),
            ]

            for dir_path in possible_vlc_dirs:
                logger.info(f"البحث عن VLC في: {dir_path}")
                if os.path.exists(dir_path):
                    vlc_dir = dir_path
                    logger.info(f"تم العثور على مجلد VLC: {vlc_dir}")
                    break

            if vlc_dir:
                # إضافة مجلد VLC إلى PATH على ويندوز
                if sys.platform == "win32":
                    current_path = os.environ.get('PATH', '')
                    if vlc_dir not in current_path:
                        os.environ['PATH'] = vlc_dir + os.pathsep + current_path
                        logger.info(f"تم إضافة مجلد VLC إلى PATH: {vlc_dir}")

                # تعيين VLC_PLUGIN_PATH إلى مجلد plugins
                plugins_dir = os.path.join(vlc_dir, 'plugins')
                if os.path.exists(plugins_dir):
                    os.environ['VLC_PLUGIN_PATH'] = plugins_dir
                    logger.info(f"تم تعيين VLC_PLUGIN_PATH: {plugins_dir}")
                else:
                    logger.warning(f"لم يتم العثور على مجلد plugins في: {plugins_dir}")

                # تعيين VLC_DATA_PATH إذا كان موجوداً
                vlc_data_dir = os.path.join(vlc_dir, 'data')
                if os.path.exists(vlc_data_dir):
                    os.environ['VLC_DATA_PATH'] = vlc_data_dir
                    logger.info(f"تم تعيين VLC_DATA_PATH: {vlc_data_dir}")
                else:
                    # جرب locale كبديل
                    locale_dir = os.path.join(vlc_dir, 'locale')
                    if os.path.exists(locale_dir):
                        os.environ['VLC_DATA_PATH'] = vlc_dir
                        logger.info(f"تم تعيين VLC_DATA_PATH إلى مجلد VLC: {vlc_dir}")
            else:
                logger.warning("لم يتم العثور على مجلد VLC في التطبيق - سيتم استخدام VLC النظامي. لجعل التطبيق مستقلاً، تأكد من بناء التطبيق باستخدام PyInstaller مع تضمين مكتبات VLC")

        except Exception as e:
            logger.warning(f"خطأ في إعداد مسارات VLC: {e}")

    def play_sound(self, sound_file: str, volume: float = 0.7):
        """تشغيل ملف صوتي باستخدام VLC مع fallback للنظام"""
        logger.info(f"محاولة تشغيل الصوت عبر VLC: {sound_file}")

        # إذا لم يكن المسار مطلقاً، افترض أنه نسبي لمجلد المشروع
        if not os.path.isabs(sound_file):
            sound_path = get_working_path(sound_file)
            logger.info(f"تحويل المسار النسبي إلى: {sound_path}")
        else:
            sound_path = sound_file

        if not os.path.exists(sound_path):
            logger.warning(f"ملف الصوت غير موجود {sound_path}")
            # محاولة تشغيل الصوت الافتراضي كحل بديل
            default_notification = get_working_path('sounds/notification.wav')
            logger.info(f"محاولة استخدام الصوت الافتراضي: {default_notification}")
            if os.path.exists(default_notification):
                sound_path = default_notification
                logger.info(f"استخدام الصوت الافتراضي: {sound_path}")
            else:
                logger.error("الصوت الافتراضي غير موجود أيضاً")
                return False

        logger.info(f"مسار الصوت النهائي: {sound_path}, موجود: {os.path.exists(sound_path)}")

        # محاولة استخدام VLC أولاً
        vlc_success = self._play_sound_vlc(sound_path, volume)
        if vlc_success:
            return True

        # Fallback: استخدام نظام الصوت البديل
        logger.warning("فشل VLC، محاولة استخدام نظام صوت بديل")
        return self._play_sound_fallback(sound_path, volume)

    def _play_sound_vlc(self, sound_path: str, volume: float = 0.7):
        """تشغيل الصوت باستخدام VLC"""
        try:
            import vlc
            logger.info("تهيئة مشغل VLC")
            if self.player and self.player.is_playing():
                self.stop_sound()

            # محاولة إنشاء instance من VLC بطرق مختلفة
            instance = None

            # المحاولة الأولى: مع إعدادات أساسية
            try:
                vlc_args = ['--no-video', '--quiet']
                plugin_path = os.environ.get('VLC_PLUGIN_PATH')
                if plugin_path:
                    vlc_args.extend(['--plugin-path', plugin_path])
                    logger.info(f"استخدام VLC_PLUGIN_PATH: {plugin_path}")
                instance = vlc.Instance(vlc_args)
                if instance:
                    logger.info("تم إنشاء instance VLC بنجاح مع الإعدادات الأساسية")
            except Exception as e:
                logger.warning(f"فشل إنشاء instance VLC مع الإعدادات الأساسية: {e}")

            # المحاولة الثانية: بدون plugin-path إذا فشلت الأولى
            if not instance:
                try:
                    logger.info("محاولة إنشاء instance VLC بدون plugin-path")
                    instance = vlc.Instance(['--no-video', '--quiet'])
                    if instance:
                        logger.info("تم إنشاء instance VLC بنجاح بدون plugin-path")
                except Exception as e:
                    logger.warning(f"فشل إنشاء instance VLC بدون plugin-path: {e}")

            # المحاولة الثالثة: instance فارغ إذا فشلت الكل
            if not instance:
                try:
                    logger.info("محاولة إنشاء instance VLC فارغ")
                    instance = vlc.Instance()
                    if instance:
                        logger.info("تم إنشاء instance VLC فارغ بنجاح")
                except Exception as e:
                    logger.error(f"فشل إنشاء instance VLC فارغ: {e}")

            if instance is None:
                logger.error("فشل في إنشاء instance VLC - سيتم استخدام نظام صوت بديل")
                return False

            self.player = instance.media_player_new()

            if self.player is None:
                logger.error("فشل في إنشاء media player VLC")
                return False

            media = instance.media_new(sound_path)
            self.player.set_media(media)
            self.player.audio_set_volume(int(volume * 100))
            self.player.play()
            logger.info(f"تم تشغيل الصوت عبر VLC: {sound_path}")
            return True
        except Exception as e:
            logger.error(f"فشل تشغيل الصوت عبر VLC: {e}")
            return False

    def _play_sound_fallback(self, sound_path: str, volume: float = 0.7):
        """نظام صوت بديل باستخدام winsound أو playsound"""
        try:
            # محاولة استخدام winsound أولاً (متوفر على ويندوز)
            if sys.platform == "win32":
                try:
                    import winsound
                    logger.info("استخدام winsound كبديل للصوت")
                    # winsound يدعم WAV فقط، تحويل إلى نسبة مئوية
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    logger.info(f"تم تشغيل الصوت عبر winsound: {sound_path}")
                    return True
                except Exception as e:
                    logger.warning(f"فشل winsound: {e}")

            # محاولة استخدام playsound كبديل أخير
            try:
                from playsound import playsound
                logger.info("استخدام playsound كبديل للصوت")
                playsound(sound_path, block=False)
                logger.info(f"تم تشغيل الصوت عبر playsound: {sound_path}")
                return True
            except ImportError:
                logger.warning("playsound غير متوفر")
            except Exception as e:
                logger.warning(f"فشل playsound: {e}")

            logger.error("فشل جميع أنظمة الصوت المتاحة")
            return False

        except Exception as e:
            logger.error(f"خطأ في نظام الصوت البديل: {e}")
            return False
    
    def stop_sound(self):
        """إيقاف تشغيل الصوت عبر VLC"""
        if self.player:
            try:
                self.player.stop()
                self.player.release()
                self.player = None
                logger.info("تم إيقاف الصوت عبر VLC")
            except Exception as e:
                logger.warning(f"خطأ في إيقاف الصوت عبر VLC: {e}")
                self.player = None

    def set_end_callback(self, callback):
        """تعيين callback ليتم استدعاؤه عند انتهاء الصوت عبر VLC"""
        if self.player:
            try:
                import vlc
                def on_end(event):
                    callback()
                self.player.event_manager().event_attach(vlc.EventType.MediaPlayerEndReached, on_end)
                logger.info("تم تعيين callback لنهاية الصوت عبر VLC")
            except Exception as e:
                logger.error(f"خطأ في تعيين callback لنهاية الصوت عبر VLC: {e}")
        else:
            logger.warning("لا يمكن تعيين callback - مشغل VLC غير مهيأ")

class NotificationManager:
    """مدير الإشعارات مع دعم متعدد المنصات"""
    
    def __init__(self, settings: Settings, translator: Translator):
        self.settings = settings
        self._ = translator.get
        self.toaster = None
        
        # تأكد من تسجيل التطبيق للإشعارات في ويندوز
        if sys.platform == "win32":
            try:
                from check_notifications import ensure_app_in_registry
                ensure_app_in_registry()
            except Exception as e:
                logger.warning(f"فشل في تسجيل التطبيق للإشعارات: {e}")
        
        # تهيئة win10toast-persist إذا كان متاحاً
        if Win10Toast_AVAILABLE:
            try:
                self.toaster = ToastNotifier()
                logger.info("تم تهيئة ToastNotifier لنظام ويندوز")
            except Exception as e:
                logger.error(f"خطأ في تهيئة ToastNotifier {e}")
                self.toaster = None
    
    def send_notification(self, title: str, message: str, timeout: int = 180):
        """إرسال إشعار باستخدام أفضل نظام متاح"""
        if not self.settings.notifications_enabled:
            logger.warning("Notifications are disabled in settings")
            return

        # Get icon path
        try:
            icon_path = get_working_path("pray_times.ico")
            if not os.path.exists(icon_path):
                icon_path = None
        except:
            icon_path = None

        # محاولة استخدام win10toast-persist على ويندوز كأولوية أولى
        if Win10Toast_AVAILABLE and self.toaster:
            try:
                self.toaster.show_toast(
                    title,
                    message,
                    icon_path=icon_path,
                    duration=timeout,
                    threaded=True
                )
                logger.info(f"تم إرسال إشعار عبر win10toast: {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر win10toast: {e}")

        # محاولة استخدام PowerShell لإشعارات ويندوز الحديثة
        if PowerShell_AVAILABLE and sys.platform == "win32":
            try:
                self._show_powershell_notification(title, message, timeout)
                logger.info(f"تم إرسال إشعار عبر PowerShell: {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر PowerShell: {e}")

        # محاولة استخدام plyer
        if Plyer_AVAILABLE:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_icon=icon_path,
                    timeout=timeout,
                    app_name="مواقيت الصلاة"
                )
                logger.info(f"تم إرسال إشعار عبر plyer {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر plyer {e}")

        # محاولة استخدام win32api لإشعارات ويندوز الأساسية
        if Win32API_AVAILABLE and sys.platform == "win32":
            try:
                self._show_windows_notification(title, message, timeout)
                logger.info(f"تم إرسال إشعار عبر win32api: {title}")
                return
            except Exception as e:
                logger.warning(f"فشل إرسال إشعار عبر win32api: {e}")

        # استخدام tkinter كحل بديل أخير
        if Tkinter_AVAILABLE:
            try:
                self._show_tkinter_notification(title, message, timeout)
                logger.info(f"تم إرسال إشعار عبر tkinter: {title}")
                return
            except Exception as e:
                logger.error(f"فشل إرسال إشعار عبر tkinter: {e}")
                
        logger.error("فشل إرسال الإشعار عبر جميع الأنظمة المتاحة")
    
    def _show_windows_notification(self, title: str, message: str, timeout: int = 10):
        """إظهار إشعار ويندوز باستخدام win32api - طريقة مبسطة"""
        try:
            def show_notification():
                try:
                    # استخدام MessageBox مع flags تجعلها تبدو كإشعار نظام
                    full_message = f"{title}\n\n{message}"

                    # استخدام MB_SYSTEMMODAL | MB_ICONINFORMATION | MB_OK لتبدو كإشعار
                    result = win32api.MessageBox(
                        None,  # لا نافذة أب
                        full_message,
                        "مواقيت الصلاة",
                        win32con.MB_SYSTEMMODAL | win32con.MB_ICONINFORMATION | win32con.MB_OK | win32con.MB_SETFOREGROUND
                    )

                    logger.info("تم إظهار إشعار ويندوز باستخدام MessageBox")

                except Exception as e:
                    logger.error(f"خطأ في إنشاء إشعار ويندوز: {e}")
                    # fallback to tkinter
                    self._show_tkinter_notification(title, message, timeout)

            # تشغيل الإشعار في خيط منفصل
            notification_thread = threading.Thread(target=show_notification)
            notification_thread.daemon = True
            notification_thread.start()

        except Exception as e:
            logger.error(f"فشل في إعداد إشعار ويندوز: {e}")
            # fallback to tkinter
            self._show_tkinter_notification(title, message, timeout)

    def _notification_window_proc(self, hwnd, msg, wparam, lparam):
        """معالج رسائل النافذة للإشعارات"""
        if msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _show_powershell_notification(self, title: str, message: str, timeout: int = 180):
        """إظهار إشعار ويندوز باستخدام PowerShell - إشعارات Action Center"""
        try:
            def show_notification():
                try:
                    # الحصول على مسار الأيقونة
                    icon_path = get_working_path("pray_times.ico")

                    # استخدام أمر PowerShell محسن لإظهار إشعار مع أيقونة البرنامج
                    ps_command = f'''
Add-Type -AssemblyName System.Windows.Forms
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$app = "مواقيت الصلاة"
$template = @"
<toast>
    <visual>
        <binding template='ToastGeneric'>
            <text>$app</text>
            <text>{message}</text>
        </binding>
    </visual>
</toast>
"@

# محاولة استخدام الإشعارات الحديثة أولاً
try {{
    $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
    $xml.LoadXml($template)
    $toast = New-Object Windows.UI.Notifications.ToastNotification $xml
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($app).Show($toast)
}} catch {{
    # إذا فشلت الإشعارات الحديثة، استخدم NotifyIcon كبديل
    [System.Windows.Forms.Application]::EnableVisualStyles()
    $notification = New-Object System.Windows.Forms.NotifyIcon
    $notification.Icon = [System.Drawing.SystemIcons]::Information
    $notification.BalloonTipTitle = $app
    $notification.BalloonTipText = "{message}"
    $notification.BalloonTipIcon = "Info"
    $notification.Visible = $true

    try {{
        if (Test-Path "{icon_path}") {{
            $notification.Icon = [System.Drawing.Icon]::ExtractAssociatedIcon("{icon_path}")
        }}
    }} catch {{
        # استخدام الأيقونة الافتراضية في حالة الفشل
    }}

    # تشغيل البالون مرتين لضمان الظهور
    $notification.ShowBalloonTip(10000)
    Start-Sleep -Milliseconds 500
    $notification.ShowBalloonTip(10000)
    Start-Sleep -Seconds 10
    $notification.Dispose()
}}
'''

                    # تشغيل PowerShell مع السكريبت بدون إظهار النافذة
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE

                    result = subprocess.run(
                        ["powershell", "-Command", ps_command],
                        capture_output=True,
                        text=True,
                        timeout=30,
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                    )

                    if result.returncode == 0:
                        logger.info("تم إظهار إشعار ويندوز عبر PowerShell بنجاح")
                    else:
                        logger.warning(f"فشل PowerShell: {result.stderr}")
                        # fallback
                        self._show_tkinter_notification(title, message, timeout)

                except subprocess.TimeoutExpired:
                    logger.warning("انتهت مهلة PowerShell")
                    self._show_tkinter_notification(title, message, timeout)
                except Exception as e:
                    logger.error(f"خطأ في PowerShell notification: {e}")
                    # fallback
                    self._show_tkinter_notification(title, message, timeout)

            # تشغيل الإشعار في خيط منفصل
            notification_thread = threading.Thread(target=show_notification)
            notification_thread.daemon = True
            notification_thread.start()

        except Exception as e:
            logger.error(f"فشل في إعداد إشعار PowerShell: {e}")
            # fallback to tkinter
            self._show_tkinter_notification(title, message, timeout)

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
        return Plyer_AVAILABLE or Win10Toast_AVAILABLE or PowerShell_AVAILABLE or Win32API_AVAILABLE or Tkinter_AVAILABLE
