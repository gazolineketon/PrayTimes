# -*- coding: utf-8 -*-

"""
main_app_ui.py
يحتوي هذا الملف على الواجهة الرسومية الرئيسية
"""

import tkinter as tk
from tkinter import ttk, messagebox
import requests
from datetime import datetime, timedelta
import time
import re
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

# التسجيل
logger = logging.getLogger(__name__)
# تأجيل استيراد pystray و PIL حتى يتم استخدامهما فعلياً
PYSTRAY_AVAILABLE = False
TrayIcon = None
TrayMenu = None
TrayMenuItem = None
PIL_Image = None
PIL_ImageDraw = None

def _import_pystray_and_pil():
    """استيراد pystray و PIL عند الحاجة"""
    global PYSTRAY_AVAILABLE, TrayIcon, TrayMenu, TrayMenuItem, PIL_Image, PIL_ImageDraw
    if not PYSTRAY_AVAILABLE:
        try:
            from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
            from PIL import Image, ImageDraw
            PIL_Image = Image
            PIL_ImageDraw = ImageDraw
            PYSTRAY_AVAILABLE = True
        except ImportError:
            PYSTRAY_AVAILABLE = False
            logger.warning("pystray or Pillow is not available - tray icon functionality is disabled")
    return PYSTRAY_AVAILABLE

from config import Translator
from settings_manager import Settings
from data_manager import CacheManager, get_countries, get_cities
from prayer_logic import TimeSync
from media_manager import AdhanPlayer, NotificationManager, NOTIFICATIONS_AVAILABLE
from ui_components import SettingsDialog
from qibla_ui import QiblaWidget
from resource_helper import get_working_path
from cleanup_hook import cleanup_pyinstaller

logger = logging.getLogger(__name__)

class EnhancedPrayerTimesApp:
    """تطبيق مواقيت الصلاة"""
    def __init__(self, version):
        self.root = tk.Tk()
        self.version = version        
        
        # تهيئة المكونات
        self.settings = Settings()
        self.translator = Translator(self.settings.language)
        self._ = self.translator.get
        
        self.root.title(self._("prayer_times"))
        try:
            self.root.iconbitmap(get_working_path("pray_times.ico"))
        except tk.TclError:
            logger.warning("لم يتم العثور على pray_times.ico، الاستمرار بدون أيقونة")
        self.root.geometry("850x1000")

        self.cache_manager = CacheManager()
        self.adhan_player = AdhanPlayer()
        self.notification_manager = NotificationManager(self.settings, self.translator)
        
        self.cache_manager.cleanup_old_cache()
        
        self.setup_modern_theme()
        
        self.prayer_data = {}
        self.cities = []
        self.countries = []
        self.current_city = ""
        self.current_country = ""
        self.is_online = True
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.last_notification_time = {}
        self.running = True
        
        self.setup_ui()
        self.load_initial_data()
        self.start_auto_update()
        self.sync_time_on_startup()
        self.tray_icon = None
        self.tray_thread = None
        # محاولة استيراد pystray وإعداد أيقونة الشريط
        _import_pystray_and_pil()
        if PYSTRAY_AVAILABLE:
            self.setup_tray_icon()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.bind('<Unmap>', self.minimize_to_tray)
        self.root.bind('<<QuitApp>>', lambda e: self.quit_application())
        
    def sync_time_on_startup(self):
        """مزامنة الوقت عند بدء التطبيق"""
        def sync_task():
            try:
                synced_time = TimeSync.sync_time()
                if self.root.winfo_exists():
                    self.root.after(0, lambda: self.update_time_display_realtime())
            except Exception as e:
                logger.error(f"خطأ في مزامنة الوقت {e}")
        
        self.executor.submit(sync_task)
          
    def setup_modern_theme(self):
        """إعداد السمة الحديثة"""
        if self.settings.theme == "dark":
            self.colors = {'bg_primary': '#1e1e1e', 'bg_secondary': '#2d2d2d', 'bg_accent': '#0078d4', 'bg_card': '#2d2d2d', 'text_primary': '#ffffff', 'text_secondary': '#b3b3b3', 'text_accent': '#ffffff', 'border': '#404040', 'success': '#10b981', 'warning': '#f59e0b', 'error': '#ef4444', 'shadow': '#00000030'}
        else:
            self.colors = {'bg_primary': '#f3f3f3', 'bg_secondary': '#ffffff', 'bg_accent': '#0078d4', 'bg_card': '#ffffff', 'text_primary': '#323130', 'text_secondary': '#605e5c', 'text_accent': '#ffffff', 'border': '#d1d1d1', 'success': '#107c10', 'warning': '#ff8c00', 'error': '#d13438', 'shadow': '#00000010'}
        
        self.root.configure(bg=self.colors['bg_primary'])
        
        style = ttk.Style()
        style.theme_use('vista')
        
        style.configure('Modern.TCombobox', fieldbackground=self.colors['bg_card'], borderwidth=1, relief='solid', bordercolor=self.colors['border'])
    
    def create_card_frame(self, parent, **kwargs):
        """إنشاء إطار على شكل كارد"""
        frame = tk.Frame(parent, bg=self.colors['bg_card'], relief='flat', bd=1, highlightbackground=self.colors['border'], highlightthickness=1, **kwargs)
        return frame
    
    def setup_ui(self):
        """إعداد واجهة المستخدم مع دعم التمرير"""
        self.destroy_scroll_area()
        self.container = tk.Frame(self.root)
        self.container.pack(fill='both', expand=True)

        self.scrollbar = ttk.Scrollbar(self.container, orient='vertical')
        self.scrollbar.pack(side='right', fill='y')

        self.canvas = tk.Canvas(self.container, bg=self.colors['bg_primary'], highlightthickness=0, yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar.config(command=self.canvas.yview)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg_primary'])
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')

        self.scrollable_frame.bind('<Configure>', self.on_frame_configure)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
        self.root.bind('<MouseWheel>', self._on_mousewheel)
        self.root.bind('<Button-4>', self._on_button_4)
        self.root.bind('<Button-5>', self._on_button_5)

        main_container = tk.Frame(self.scrollable_frame, bg=self.colors['bg_primary'])
        main_container.pack(fill='x', expand=True, padx=20, pady=20)
        
        self.setup_header(main_container)
                
        self.calendar_card = self.create_card_frame(main_container)
        self.calendar_card.pack(fill='x', pady=(0, 10))
        self.setup_calendar_ui()
        
        self.prayers_card = self.create_card_frame(main_container)
        self.prayers_card.pack(fill='x', pady=(0, 10))
        self.setup_prayers_table()
        
        self.setup_enhanced_status_bar(main_container)
    
    

    def setup_header(self, parent):
        """إعداد الشريط العلوي"""
        header_card = self.create_card_frame(parent)
        header_card.pack(fill='x', pady=(0, 10))
        
        header_container = tk.Frame(header_card, bg=self.colors['bg_card'], pady=10)
        header_container.pack(fill='x')
        
        title_label = tk.Label(header_container, text=self._("app_title"), font=('Segoe UI', 18, 'bold'), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        title_label.pack(side='right', fill='x', expand=True)
        
        controls_frame = tk.Frame(header_container, bg=self.colors['bg_card'])
        controls_frame.pack(side='left')
        
        settings_btn = tk.Button(controls_frame, text=self._("settings"), font=('Segoe UI', 11), bg=self.colors['bg_accent'], fg=self.colors['text_accent'], relief='flat', padx=10, pady=8, cursor='hand2', command=self.open_settings)
        settings_btn.pack(side='left', padx=(10, 10))
        
        refresh_btn = tk.Button(controls_frame, text=self._("update"), font=('Segoe UI', 11), bg=self.colors['success'], fg=self.colors['text_accent'], relief='flat', padx=10, pady=8, cursor='hand2', command=self.manual_refresh)
        refresh_btn.pack(side='left')
    
    def setup_time_sync_card(self, parent):
        """إعداد كارد الوقت المتزامن"""
        time_card = self.create_card_frame(parent)
        time_card.pack(fill='x', pady=(0, 10))
        
        time_container = tk.Frame(time_card, bg=self.colors['bg_card'], pady=10)
        time_container.pack(fill='x')
        
        current_time = datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%Y-%m-%d")
        
        self.current_time_label = tk.Label(time_container, text=self._("current_time_label", time_str=time_str), font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        self.current_time_label.pack()
        
        self.time_sync_label = tk.Label(time_container, text=self._("date_label", date_str=date_str), font=('Segoe UI', 12), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.time_sync_label.pack()
    
    def setup_calendar_ui(self):
        """إعداد واجهة التقويم"""
        calendar_container = tk.Frame(self.calendar_card, bg=self.colors['bg_card'], pady=5)
        calendar_container.pack(fill='x')
                
        dates_container = tk.Frame(calendar_container, bg=self.colors['bg_card'])
        dates_container.pack()
        
        gregorian_frame = tk.Frame(dates_container, bg=self.colors['bg_card'])
        gregorian_frame.pack(pady=(0, 5))
                
        greg_boxes_frame = tk.Frame(gregorian_frame, bg=self.colors['bg_card'])
        greg_boxes_frame.pack(side='right')
        
        self.greg_day_frame = self.create_date_box(greg_boxes_frame, self.colors['bg_accent'], 50, 35)
        self.greg_day_frame.pack(side='right', padx=2)
        self.greg_day_label = tk.Label(self.greg_day_frame, font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_accent'], fg=self.colors['text_accent'])
        self.greg_day_label.pack(expand=True)        
        
        self.greg_month_frame = self.create_date_box(greg_boxes_frame, self.colors['bg_accent'], 120, 35)
        self.greg_month_frame.pack(side='right', padx=2)
        self.greg_month_label = tk.Label(self.greg_month_frame, font=('Segoe UI', 12, 'bold'), bg=self.colors['bg_accent'], fg=self.colors['text_accent'])
        self.greg_month_label.pack(expand=True)
        
        self.greg_year_frame = self.create_date_box(greg_boxes_frame, self.colors['bg_accent'], 70, 35)
        self.greg_year_frame.pack(side='right', padx=2)
        self.greg_year_label = tk.Label(self.greg_year_frame, font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_accent'], fg=self.colors['text_accent'])
        self.greg_year_label.pack(expand=True)
        
        hijri_frame = tk.Frame(dates_container, bg=self.colors['bg_card'])
        hijri_frame.pack()
                        
        hijri_boxes_frame = tk.Frame(hijri_frame, bg=self.colors['bg_card'])
        hijri_boxes_frame.pack(side='right')
        
        self.hijri_day_frame = self.create_date_box(hijri_boxes_frame, self.colors['warning'], 50, 35)
        self.hijri_day_frame.pack(side='right', padx=2)
        self.hijri_day_label = tk.Label(self.hijri_day_frame, font=('Segoe UI', 14, 'bold'), bg=self.colors['warning'], fg=self.colors['text_accent'])
        self.hijri_day_label.pack(expand=True)

        self.hijri_month_frame = self.create_date_box(hijri_boxes_frame, self.colors['warning'], 120, 35)
        self.hijri_month_frame.pack(side='right', padx=2)
        self.hijri_month_label = tk.Label(self.hijri_month_frame, font=('Segoe UI', 12, 'bold'), bg=self.colors['warning'], fg=self.colors['text_accent'])
        self.hijri_month_label.pack(expand=True)
    
        self.hijri_year_frame = self.create_date_box(hijri_boxes_frame, self.colors['warning'], 70, 35)
        self.hijri_year_frame.pack(side='right', padx=2)
        self.hijri_year_label = tk.Label(self.hijri_year_frame, font=('Segoe UI', 14, 'bold'), bg=self.colors['warning'], fg=self.colors['text_accent'])
        self.hijri_year_label.pack(expand=True)
        
    def create_date_box(self, parent, bg_color, width, height):
        """إنشاء صندوق تاريخ"""
        frame = tk.Frame(parent, bg=bg_color, width=width, height=height, relief='flat', bd=0)
        frame.pack_propagate(False)
        
        border_frame = tk.Frame(frame, bg=bg_color)
        border_frame.pack(fill='both', expand=True, padx=1, pady=1)
        
        return frame
    
    
    def setup_prayers_table(self):
        """إعداد جدول الصلوات"""
        prayers_container = tk.Frame(self.prayers_card, bg=self.colors['bg_card'], pady=15)
        prayers_container.pack(fill='both', expand=True)
        
        self.prayers_title = tk.Label(prayers_container, text=self._("prayer_times_table_title"), font=('Segoe UI', 16, 'bold'), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        self.prayers_title.pack(pady=(0, 15))
        
        self.table_container = tk.Frame(prayers_container, bg=self.colors['bg_card'])
        self.table_container.pack(expand=True, padx=10)
        
        self.loading_label = tk.Label(self.table_container, text=self._("loading_prayer_times"), font=('Segoe UI', 14), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.loading_label.pack(expand=True)
        
        self.countdown_frame = tk.Frame(prayers_container, bg=self.colors['bg_card'])
        self.countdown_frame.pack(fill='x', pady=(15, 0))
        
        countdown_card = self.create_card_frame(self.countdown_frame)
        countdown_card.pack(fill='x')
        
        countdown_container = tk.Frame(countdown_card, bg=self.colors['bg_card'], pady=10)
        countdown_container.pack(fill='x')
        
        self.countdown_label = tk.Label(countdown_container, text="", font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_card'], fg=self.colors['error'])
        self.countdown_label.pack()
    
    def setup_enhanced_status_bar(self, parent):
        """إعداد شريط الحالة"""
        status_card = self.create_card_frame(parent)
        status_card.pack(fill='x')
        
        status_container = tk.Frame(status_card, bg=self.colors['bg_card'], pady=5)
        status_container.pack(fill='x')
        
        left_frame = tk.Frame(status_container, bg=self.colors['bg_card'])
        left_frame.pack(side='left', padx=15)
        
        self.status_indicator = tk.Label(left_frame, text="●", font=('Segoe UI', 12, 'bold'), bg=self.colors['bg_card'], fg=self.colors['success'])
        self.status_indicator.pack(side='left')
        
        self.connection_status = tk.Label(left_frame, text=self._("connected"), font=('Segoe UI', 10), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.connection_status.pack(side='left')
        
        right_frame = tk.Frame(status_container, bg=self.colors['bg_card'])
        right_frame.pack(side='right', padx=15)
        
        version_label = tk.Label(right_frame, text=f'{self._("version")} {self.version}', font=('Segoe UI', 10), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        version_label.pack(side='right')
        
        if NOTIFICATIONS_AVAILABLE and self.settings.notifications_enabled:
            notification_indicator = tk.Label(right_frame, text="🔔", font=('Segoe UI', 10), bg=self.colors['bg_card'], fg=self.colors['success'])
            notification_indicator.pack(side='right')

        self.last_update_label = tk.Label(status_container, text="", font=('Segoe UI', 10), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.last_update_label.pack(fill='x', expand=True)
    
    def load_initial_data(self):
        """تحميل البيانات الأولية"""
        def task():
            self.countries = get_countries()
            if self.settings.selected_country and self.settings.selected_city:
                self.cities = get_cities(self.settings.selected_country)
                self.fetch_and_display_times(self.settings.selected_city, self.settings.selected_country)
            else:
                self.root.after(0, lambda: self.show_error(self._("please_select_city_country")))

        self.executor.submit(task)
    
    def fetch_and_display_times(self, city: str, country: str):
        """جلب وعرض مواقيت الصلاة"""
        self.show_loading()
        
        def api_task():
            try:
                cached_data = self.cache_manager.load_data(city, country)
                if cached_data:
                    city_data = self.parse_api_data(city, cached_data)
                    self.root.after(0, lambda: self.display_prayer_times(city_data))
                    logger.info(f"تم استخدام البيانات المؤقتة لـ {city}")
                    return
                
                url = f"http://api.aladhan.com/v1/timingsByCity"
                params = {'city': city, 'country': country, 'method': self.settings.calculation_method}
                
                response = self.robust_api_call(url, params)
                
                if response and response.get('code') == 200:
                    api_data = response['data']
                    city_data = self.parse_api_data(city, api_data)
                    
                    self.cache_manager.save_data(city, country, api_data)
                    
                    self.root.after(0, lambda: self.display_prayer_times(city_data))
                    self.root.after(0, lambda: self.update_last_update_time())
                else:
                    error_msg = response.get('data', self._("failed_to_fetch_data")) if response else self._("no_server_response")
                    self.root.after(0, lambda: self.show_error(error_msg))
                
            except Exception as e:
                logger.error(f"خطأ في جلب البيانات {e}")
                self.root.after(0, lambda: self.show_error(self._("connection_error", e=str(e))))
            finally:
                self.root.after(0, self.hide_loading)
        
        self.executor.submit(api_task)
    
    # تخزين مؤقت للاستجابات السابقة لتحسين الأداء
    _api_response_cache = {}
    _MAX_CACHE_SIZE = 20
    
    def robust_api_call(self, url: str, params: dict, retries: int = 3, cache_ttl: int = 3600):
        """
        استدعاء API مع إعادة المحاولة وتحسين معالجة الأخطاء وتخزين مؤقت ذكي
        :param url: عنوان URL للـ API
        :param params: معاملات الطلب
        :param retries: عدد محاولات إعادة المحاولة
        :param cache_ttl: مدة صلاحية التخزين المؤقت بالثواني (الافتراضي: ساعة واحدة)
        :return: استجابة API كـ JSON أو None في حالة الفشل
        """
        # إنشاء مفتاح للتخزين المؤقت
        cache_key = f"{url}:{str(sorted(params.items()))}"
        current_time = time.time()
        
        # التحقق من التخزين المؤقت
        if cache_key in self._api_response_cache:
            cached_data, timestamp = self._api_response_cache[cache_key]
            if current_time - timestamp < cache_ttl:
                logger.debug(f"استخدام استجابة مخزنة مؤقتًا لـ {url}")
                return cached_data
        
        # استراتيجية التأخير التدريجي
        backoff_strategy = [1, 2, 5, 10, 20]  # بالثواني
        last_exception = None
        error_details = []
        
        # محاولات الاتصال مع إعادة المحاولة
        for attempt in range(retries):
            try:
                # استخدام مهلة أقصر للمحاولات اللاحقة لتسريع فشل الاتصال
                timeout = max(3, 10 - attempt * 2)
                
                logger.info(f"إرسال طلب {url} (المحاولة {attempt+1}/{retries}، مهلة={timeout}ث)")
                
                response = requests.get(url, params=params, timeout=timeout)
                response.raise_for_status()  # إثارة استثناء للرموز 4xx/5xx
                
                json_response = response.json()
                
                # التحقق من صحة البيانات (يمكن أن تختلف حسب API المستخدم)
                if not json_response or not isinstance(json_response, dict):
                    raise ValueError("استجابة API غير صالحة")
                
                # تخزين النتيجة الناجحة في التخزين المؤقت
                self._api_response_cache[cache_key] = (json_response, current_time)
                
                # إزالة العناصر القديمة من التخزين المؤقت إذا تجاوز الحجم المسموح به
                if len(self._api_response_cache) > self._MAX_CACHE_SIZE:
                    oldest_key = min(self._api_response_cache.keys(), 
                                     key=lambda k: self._api_response_cache[k][1])
                    del self._api_response_cache[oldest_key]
                
                return json_response
                
            except requests.exceptions.Timeout as e:
                error_msg = f"انتهت مهلة الاتصال: {str(e)}"
                last_exception = e
                error_details.append(error_msg)
                logger.warning(f"انتهت مهلة اتصال API (المحاولة {attempt+1}/{retries}): {error_msg}")
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"خطأ في الاتصال: {str(e)}"
                last_exception = e
                error_details.append(error_msg)
                logger.warning(f"خطأ في اتصال API (المحاولة {attempt+1}/{retries}): {error_msg}")
                
            except requests.exceptions.HTTPError as e:
                error_msg = f"خطأ HTTP {e.response.status_code}: {str(e)}"
                last_exception = e
                error_details.append(error_msg)
                logger.warning(f"خطأ HTTP في API (المحاولة {attempt+1}/{retries}): {error_msg}")
                
                # لا داعي لإعادة المحاولة مع بعض أخطاء HTTP
                if hasattr(e, 'response') and e.response.status_code in [400, 401, 403, 404]:
                    break
                    
            except Exception as e:
                error_msg = f"خطأ غير متوقع: {str(e)}"
                last_exception = e
                error_details.append(error_msg)
                logger.warning(f"خطأ غير متوقع في API (المحاولة {attempt+1}/{retries}): {error_msg}")
            
            # الانتظار قبل إعادة المحاولة باستخدام استراتيجية التأخير التدريجي
            if attempt < retries - 1:
                backoff_time = backoff_strategy[min(attempt, len(backoff_strategy)-1)]
                logger.info(f"انتظار {backoff_time} ثوانٍ قبل إعادة المحاولة")
                time.sleep(backoff_time)
        
        # إرجاع بيانات مخزنة مؤقتًا قديمة إذا كانت متوفرة (في حالة عدم الاتصال)
        if cache_key in self._api_response_cache:
            logger.warning("استخدام بيانات مخزنة سابقًا منتهية الصلاحية (وضع عدم الاتصال)")
            return self._api_response_cache[cache_key][0]
        
        # تسجيل الخطأ النهائي
        error_summary = "; ".join(error_details)
        logger.error(f"فشلت جميع محاولات الاتصال بـ API: {error_summary}")
        
        if last_exception:
            raise last_exception
            
        return None
    
    
    
    def parse_api_data(self, city: str, data: dict):
        """تحليل البيانات من API"""
        timings = data['timings']
        
        def format_time(time_24: str) -> tuple:
            """تنسيق الوقت مع معالجة أفضل للأخطاء"""
            try:
                time_clean = time_24.split(' ')[0]
                dt_object = datetime.strptime(time_clean, "%H:%M")
                time_12 = dt_object.strftime("%I:%M").lstrip('0')
                if not time_12.startswith('1'):
                    time_12 = time_12.lstrip('0')
                
                if self.settings.language == 'ar':
                    period = "ص" if dt_object.hour < 12 else "م"
                else:
                    period = "AM" if dt_object.hour < 12 else "PM"
                
                return time_12, period, f"{time_12} {period}"
            except Exception as e:
                logger.error(f"خطأ في تنسيق الوقت {time_24} {e}")
                return "00:00", "ص" if self.settings.language == 'ar' else 'AM', "00:00 ص" if self.settings.language == 'ar' else '00:00 AM'
        
        prayer_names = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha']
        api_names = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
        
        prayers = {}
        for prayer, api_name in zip(prayer_names, api_names):
            prayers[prayer] = format_time(timings[api_name])
        
        hijri_month_key = 'ar' if self.settings.language == 'ar' else 'en'
        self.prayer_data[city] = {
            'gregorian_date': data['date']['gregorian']['date'],
            'hijri_date': f"{data['date']['hijri']['day']} {data['date']['hijri']['month'][hijri_month_key]} {data['date']['hijri']['year']}",
            'timezone': data.get('meta', {}).get('timezone', ''),
            'method': data.get('meta', {}).get('method', {}).get('name', ''),
            'latitude': data.get('meta', {}).get('latitude', 0),
            'longitude': data.get('meta', {}).get('longitude', 0)
        }
        
        for name, (time_val, period_val, orig_val) in prayers.items():
            self.prayer_data[city][f'{name}_time'] = time_val
            self.prayer_data[city][f'{name}_period'] = period_val
            self.prayer_data[city][f'{name}_orig'] = orig_val
        return self.prayer_data[city]
    
    def display_prayer_times(self, city_data):
        """عرض مواقيت الصلاة للمدينة المحددة"""
        self.current_city = self.settings.selected_city
        self.current_country = self.settings.selected_country
        
        city_name = self.current_city
        country_name = self.current_country

        if self.settings.language == 'ar':
            # بحث عن الاسم العربي للبلد
            if self.countries:
                for eng, ara in self.countries:
                    if eng == country_name:
                        country_name = ara
                        break
            # بحث عن الاسم العربي للمدينة
            if hasattr(self, 'cities') and self.cities:
                for eng, ara in self.cities:
                    if eng == city_name:
                        city_name = ara
                        break
        
        # عنوان الجدول مواقيت الصلاة لمدينة
        title = f"{self._('prayer_times_for_city')} {city_name}"
        if hasattr(self, 'prayers_title'):
            self.prayers_title.config(text=title)

        self.update_calendar_display(city_data)
        
        for widget in self.table_container.winfo_children():
            widget.destroy()
        
        self.table_frame = tk.Frame(self.table_container, bg=self.colors['bg_card'])
        self.table_frame.pack(fill='both', expand=True)
        
        columns = [("status", 80, "center"), ("period", 60, "center"), ("time", 80, "center"), ("prayer", 80, "center"), ("icon", 50, "center")]
        
        for i, (col_name, width, anchor) in enumerate(columns):
            self.table_frame.grid_columnconfigure(i, weight=1, minsize=width)
        
        prayers_data = [
            (city_data['fajr_orig'], city_data['fajr_period'], city_data['fajr_time'], self._('fajr'), '🌅'),
            (city_data['sunrise_orig'], city_data['sunrise_period'], city_data['sunrise_time'], self._('sunrise'), '🌄'),
            (city_data['dhuhr_orig'], city_data['dhuhr_period'], city_data['dhuhr_time'], self._('dhuhr'), '☀️'),
            (city_data['asr_orig'], city_data['asr_period'], city_data['asr_time'], self._('asr'), '🌤️'),
            (city_data['maghrib_orig'], city_data['maghrib_period'], city_data['maghrib_time'], self._('maghrib'), '🌅'),
            (city_data['isha_orig'], city_data['isha_period'], city_data['isha_time'], self._('isha'), '🌙')
        ]
        
        header_style = {'font': ('Segoe UI', 12, 'bold'), 'bg': self.colors['bg_accent'], 'fg': self.colors['text_accent'], 'pady': 10, 'relief': 'flat'}

        # عنوان الحالة
        tk.Label(self.table_frame, text=self._("table_header_status"), **header_style).grid(row=0, column=0, sticky='nsew')

        # عنوان الوقت
        tk.Label(self.table_frame, text=self._("table_header_time"), **header_style).grid(row=0, column=1, columnspan=2, sticky='nsew')

        # عنوان الصلاة
        tk.Label(self.table_frame, text=self._("table_header_prayer"), **header_style).grid(row=0, column=3, columnspan=4, sticky='nsew')
        
        self.prayer_rows = []
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        # تحديث حالة الصلاة
        for i, (prayer_orig, prayer_period, prayer_time, prayer_name, icon) in enumerate(prayers_data):
            row_num = i + 1
            
            prayer_minutes = self.time_to_minutes(prayer_orig)
            if prayer_minutes <= current_minutes:
                if i < len(prayers_data) - 1:
                    next_prayer_minutes = self.time_to_minutes(prayers_data[i + 1][0])
                    if current_minutes < next_prayer_minutes:
                        status = self._("prayer_status_now")
                        status_color = self.colors['success']
                    else:
                        status = self._("prayer_status_finished")
                        status_color = self.colors['text_secondary']
                else:
                    status = self._("prayer_status_finished")
                    status_color = self.colors['text_secondary']
            else:
                time_diff = prayer_minutes - current_minutes
                if time_diff <= 60:
                    status = self._("prayer_status_within_hour", time_diff=time_diff)
                    status_color = self.colors['warning']
                else:
                    status = self._("prayer_status_upcoming")
                    status_color = self.colors['text_secondary']
            
            cell_style = {'bg': self.colors['bg_card'], 'fg': self.colors['text_primary'], 'pady': 8, 'font': ('Segoe UI', 12)}
            
            status_label = tk.Label(self.table_frame, text=status, fg=status_color, font=('Segoe UI', 10, 'bold'), anchor="center", **{k: v for k, v in cell_style.items() if k not in ['fg', 'font']})
            status_label.grid(row=row_num, column=0, sticky='nsew', pady=1)
            
            period_label = tk.Label(self.table_frame, text=prayer_period, anchor="e", **cell_style)
            period_label.grid(row=row_num, column=1, sticky='nsew', pady=1)
            
            time_label = tk.Label(self.table_frame, text=prayer_time, font=('Segoe UI', 14, 'bold'), anchor="w", **{k: v for k, v in cell_style.items() if k != 'font'})
            time_label.grid(row=row_num, column=2, sticky='nsew', pady=1)
            
            prayer_label = tk.Label(self.table_frame, text=prayer_name, anchor="e", **cell_style)
            prayer_label.grid(row=row_num, column=3, sticky='nsew', pady=1)
            
            icon_label = tk.Label(self.table_frame, text=icon, anchor="w", **cell_style)
            icon_label.grid(row=row_num, column=4, sticky='nsew', pady=1)
            
            self.prayer_rows.append({'icon': icon_label, 'prayer': prayer_label, 'time': time_label, 'period': period_label, 'status': status_label, 'prayer_name': prayer_name, 'prayer_orig': prayer_orig})
        
        self.update_next_prayer()
        self.start_countdown()
        self.check_prayer_notifications()
    
    def start_countdown(self):
        """بدء العد التنازلي"""
        if hasattr(self, '_countdown_running') and self._countdown_running:
            return
        
        self._countdown_running = True
        self.update_countdown()
    
    def update_countdown(self):
        """تحديث العد التنازلي بكفاءة أفضل"""
        if not hasattr(self, '_countdown_running') or not self._countdown_running:
            return
        
        if not self.current_city or self.current_city not in self.prayer_data:
            if self.root.winfo_exists() and self._countdown_running:
                # تأخير أطول إذا لم تكن هناك بيانات متاحة
                self.root.after(10000, self.update_countdown)
            return
        
        now = datetime.now()
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        city_data = self.prayer_data[self.current_city]
        
        prayers_orig = [
            (self._('fajr'), city_data['fajr_orig']),
            (self._('sunrise'), city_data['sunrise_orig']),
            (self._('dhuhr'), city_data['dhuhr_orig']),
            (self._('asr'), city_data['asr_orig']),
            (self._('maghrib'), city_data['maghrib_orig']),
            (self._('isha'), city_data['isha_orig'])
        ]
        
        next_prayer = None
        next_prayer_seconds = None
        
        # تحويل أوقات الصلوات إلى ثوانٍ
        for name, time_str in prayers_orig:
            prayer_minutes = self.time_to_minutes(time_str)
            prayer_seconds = prayer_minutes * 60
            if prayer_seconds > current_seconds:
                next_prayer = name
                next_prayer_seconds = prayer_seconds
                break
                
        # إذا كانت الصلاة القادمة هي الفجر في اليوم التالي
        if next_prayer is None:
            next_prayer = self._('fajr')
            next_prayer_seconds = self.time_to_minutes(prayers_orig[0][1]) * 60 + 24 * 3600
        
        remaining_seconds = next_prayer_seconds - current_seconds
        hours = remaining_seconds // 3600
        minutes = (remaining_seconds % 3600) // 60
        seconds = remaining_seconds % 60
        
        # تحديث النص فقط إذا كان الوقت المتبقي قد تغير بشكل ملحوظ
        if hasattr(self, '_last_remaining_time') and abs(self._last_remaining_time - remaining_seconds) < 1:
            # إذا كان التغيير أقل من ثانية، لا تحدث تغييرًا في الواجهة
            pass
        else:
            self._last_remaining_time = remaining_seconds
            
            # عرض الساعات والدقائق فقط إذا كان الوقت المتبقي كبيرًا
            if hours > 0:
                countdown_text = f'{self._("remaining_time_on")} {next_prayer}: {hours} {self._("hour")} و {minutes} {self._("minute")}'
            elif minutes > 0:
                countdown_text = f'{self._("remaining_time_on")} {next_prayer}: {minutes} {self._("minute")}'
            else:
                countdown_text = f'{self._("remaining_time_on")} {next_prayer}: {seconds} {self._("second")}'
            
            if remaining_seconds <= 300: # 5 دقائق
                color = self.colors['error']
            elif remaining_seconds <= 1800: # 30 دقيقة
                color = self.colors['warning']
            else:
                color = self.colors['success']
            
            self.countdown_label.config(text=countdown_text, fg=color)
        
        # تحديد فترة التحديث القادم بناءً على الوقت المتبقي
        if remaining_seconds < 60:  # آخر دقيقة: تحديث كل ثانية
            update_interval = 1000
        elif remaining_seconds < 300:  # آخر 5 دقائق: تحديث كل 5 ثوانٍ
            update_interval = 5000
        elif remaining_seconds < 1800:  # آخر 30 دقيقة: تحديث كل 15 ثانية
            update_interval = 15000
        else:  # أكثر من 30 دقيقة: تحديث كل دقيقة
            update_interval = 60000
        
        if self.root.winfo_exists() and self._countdown_running:
            self.root.after(update_interval, self.update_countdown)
    
    def show_adhan_dialog(self, prayer_name: str):
        """إظهار نافذة الأذان مع زر إيقاف"""
        if hasattr(self, 'adhan_dialog') and self.adhan_dialog and self.adhan_dialog.winfo_exists():
            self.adhan_dialog.destroy()

        self.adhan_dialog = tk.Toplevel(self.root)
        self.adhan_dialog.title(self._("adhan_for_prayer", prayer_name=prayer_name))
        self.adhan_dialog.configure(bg=self.colors['bg_primary'])
        self.adhan_dialog.geometry("300x150")
        self.adhan_dialog.resizable(False, False)
        self.adhan_dialog.attributes('-topmost', True)  # جعل النافذة في المقدمة

        # مركز النافذة
        self.adhan_dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 150
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        self.adhan_dialog.geometry(f"+{x}+{y}")

        # محتوى النافذة
        main_frame = tk.Frame(self.adhan_dialog, bg=self.colors['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)

        prayer_label = tk.Label(main_frame, text=f"{self._('its_time_for_prayer', prayer_name=prayer_name)}", font=('Segoe UI', 14, 'bold'), bg=self.colors['bg_primary'], fg=self.colors['text_primary'], wraplength=260)
        prayer_label.pack(pady=(0, 10))

        stop_button = tk.Button(main_frame, text=self._("stop_adhan"), font=('Segoe UI', 12), bg=self.colors['error'], fg=self.colors['text_accent'], relief='flat', padx=20, pady=10, cursor='hand2', command=self.stop_adhan_and_close_dialog)
        stop_button.pack()


    def stop_adhan_and_close_dialog(self):
        """إيقاف الأذان وإغلاق النافذة"""
        self.adhan_player.stop_sound()
        if hasattr(self, 'adhan_dialog') and self.adhan_dialog and self.adhan_dialog.winfo_exists():
            self.adhan_dialog.destroy()

    def close_adhan_dialog_if_exists(self):
        """إغلاق نافذة الأذان إذا كانت موجودة (للاستدعاء عند انتهاء الصوت)"""
        if hasattr(self, 'adhan_dialog') and self.adhan_dialog and self.adhan_dialog.winfo_exists():
            self.adhan_dialog.destroy()

    def check_prayer_notifications(self):
        """فحص وإرسال إشعارات الصلوات بكفاءة أفضل"""
        if not self.settings.notifications_enabled or not NOTIFICATIONS_AVAILABLE:
            return
        
        if not self.current_city or self.current_city not in self.prayer_data:
            return
        
        now = datetime.now()
        current_time_str = now.strftime("%H:%M")
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        
        city_data = self.prayer_data[self.current_city]
        prayers = [
            (self._('fajr'), city_data['fajr_orig']),
            (self._('dhuhr'), city_data['dhuhr_orig']),
            (self._('asr'), city_data['asr_orig']),
            (self._('maghrib'), city_data['maghrib_orig']),
            (self._('isha'), city_data['isha_orig'])
        ]
        
        # تتبع الوقت المتبقي حتى الإشعار أو الأذان التالي لتحديد وقت الفحص القادم
        next_notification_seconds = 24 * 3600  # القيمة الافتراضية هي يوم كامل
        
        for prayer_name, prayer_time_str in prayers:
            # تحويل وقت الصلاة إلى كائن datetime
            prayer_datetime = datetime.strptime(prayer_time_str.split()[0], "%I:%M")
            if (prayer_time_str.endswith('م') or prayer_time_str.endswith('PM')) and prayer_datetime.hour != 12:
                prayer_datetime = prayer_datetime.replace(hour=prayer_datetime.hour + 12)
            elif (prayer_time_str.endswith('ص') or prayer_time_str.endswith('AM')) and prayer_datetime.hour == 12:
                prayer_datetime = prayer_datetime.replace(hour=0)
            
            # حساب وقت الإشعار المسبق
            notification_time = prayer_datetime - timedelta(minutes=self.settings.notification_before_minutes)
            notification_time_str = notification_time.strftime("%H:%M")
            
            # حساب الثواني المتبقية حتى الإشعار
            notification_seconds = notification_time.hour * 3600 + notification_time.minute * 60
            if notification_seconds < current_seconds:
                notification_seconds += 24 * 3600  # إضافة يوم كامل إذا كان الوقت في اليوم التالي
            seconds_until_notification = notification_seconds - current_seconds
            
            # حساب الثواني المتبقية حتى وقت الصلاة
            prayer_seconds = prayer_datetime.hour * 3600 + prayer_datetime.minute * 60
            if prayer_seconds < current_seconds:
                prayer_seconds += 24 * 3600  # إضافة يوم كامل إذا كان الوقت في اليوم التالي
            seconds_until_prayer = prayer_seconds - current_seconds
            
            # تحديث وقت الإشعار التالي
            next_notification_seconds = min(next_notification_seconds, seconds_until_notification, seconds_until_prayer)
            
            # التحقق من وقت الإشعار المسبق
            if current_time_str == notification_time_str:
                # منع تكرار الإشعارات في نفس الدقيقة
                notification_key = f"pre_{prayer_name}"
                if notification_key not in self.last_notification_time or self.last_notification_time[notification_key] != current_time_str:
                    logger.info(f"إرسال إشعار قبل صلاة {prayer_name}")
                    self.notification_manager.send_notification(
                        self._("prayer_notification_alert"),
                        self._("minutes_remaining_for_prayer", minutes=self.settings.notification_before_minutes, prayer_name=prayer_name),
                        timeout=15
                    )
                    if self.settings.sound_enabled:
                        sound_file = self.settings.notification_sound_file
                        if sound_file:
                            self.adhan_player.play_sound(sound_file, self.settings.sound_volume)
                        else:
                            self.adhan_player.play_sound('sounds/notification.wav', self.settings.sound_volume)
                    self.last_notification_time[notification_key] = current_time_str
            
            # التحقق من وقت الصلاة الفعلي
            prayer_time_str = prayer_datetime.strftime("%H:%M")
            if current_time_str == prayer_time_str:
                # منع تكرار الأذان في نفس الدقيقة
                prayer_key = f"adhan_{prayer_name}"
                if prayer_key not in self.last_notification_time or self.last_notification_time[prayer_key] != current_time_str:
                    logger.info(f"إرسال أذان لصلاة {prayer_name}")
                    self.notification_manager.send_notification(
                        self._("prayer_time"),
                        self._("its_time_for_prayer", prayer_name=prayer_name),
                        timeout=20
                    )
                    
                    if self.settings.sound_enabled:
                        sound_file = self.settings.adhan_sound_file
                        if sound_file:
                            self.adhan_player.play_sound(sound_file, self.settings.sound_volume)
                        else:
                            self.adhan_player.play_sound('sounds/adhan_mekka.wma', self.settings.sound_volume)
                        # إظهار نافذة الأذان مع زر الإيقاف
                        self.show_adhan_dialog(prayer_name)
                        # تعيين callback لإغلاق النافذة عند انتهاء الصوت
                        self.adhan_player.set_end_callback(lambda: self.close_adhan_dialog_if_exists())

                    self.last_notification_time[prayer_key] = current_time_str
        
        # جدولة الفحص التالي بناءً على الوقت المتبقي للإشعار أو الأذان القادم
        if next_notification_seconds < 60:  # أقل من دقيقة
            # فحص كل 10 ثوانٍ عندما يكون الوقت قريبًا جدًا
            next_check = 10000
        elif next_notification_seconds < 300:  # أقل من 5 دقائق
            # فحص كل 30 ثانية عندما يكون الوقت قريبًا
            next_check = 30000
        elif next_notification_seconds < 1800:  # أقل من 30 دقيقة
            # فحص كل دقيقة
            next_check = 60000
        else:
            # فحص كل 5 دقائق عندما يكون الوقت بعيدًا
            next_check = 300000
        
        # جدولة الفحص التالي فقط إذا كان التطبيق لا يزال قيد التشغيل
        if self.root.winfo_exists() and self.running:
            self.root.after(next_check, self.check_prayer_notifications)
    
    def update_prayer_statuses(self):
        """تحديث حالة الصلوات في الجدول"""
        if not hasattr(self, 'prayer_rows') or not self.prayer_rows:
            return

        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        for i, row_data in enumerate(self.prayer_rows):
            if 'prayer_orig' not in row_data:
                continue

            prayer_minutes = self.time_to_minutes(row_data['prayer_orig'])
            status_label = row_data['status']

            if prayer_minutes <= current_minutes:
                if i < len(self.prayer_rows) - 1:
                    next_prayer_minutes = self.time_to_minutes(self.prayer_rows[i + 1]['prayer_orig'])
                    if current_minutes < next_prayer_minutes:
                        status = self._("prayer_status_now")
                        status_color = self.colors['success']
                    else:
                        status = self._("prayer_status_finished")
                        status_color = self.colors['text_secondary']
                else:
                    status = self._("prayer_status_finished")
                    status_color = self.colors['text_secondary']
            else:
                time_diff = prayer_minutes - current_minutes
                if time_diff <= 60:
                    status = self._("prayer_status_within_hour", time_diff=time_diff)
                    status_color = self.colors['warning']
                else:
                    status = self._("prayer_status_upcoming")
                    status_color = self.colors['text_secondary']

            status_label.config(text=status, fg=status_color)

    def update_next_prayer(self):
        """تمييز الصلاة القادمة"""
        if not hasattr(self, 'prayer_rows') or not self.prayer_rows:
            return

        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute

        # إعادة تعيين جميع الصفوف إلى النمط الافتراضي
        for row_data in self.prayer_rows:
            row_data['icon'].config(font=('Segoe UI', 12))
            row_data['prayer'].config(font=('Segoe UI', 12))
            row_data['period'].config(font=('Segoe UI', 12))
            for widget in row_data.values():
                if isinstance(widget, tk.Label):
                    widget.config(bg=self.colors['bg_card'])

        next_prayer_index = -1
        for i, row_data in enumerate(self.prayer_rows):
            if 'prayer_orig' in row_data:
                prayer_minutes = self.time_to_minutes(row_data['prayer_orig'])
                if prayer_minutes > current_minutes:
                    next_prayer_index = i
                    break

        if next_prayer_index == -1:
            next_prayer_index = 0

        if 0 <= next_prayer_index < len(self.prayer_rows):
            row_data = self.prayer_rows[next_prayer_index]
            highlight_color = '#e8f4fd' if self.settings.theme == 'light' else '#1a365d'

            # جعل الخط العريض وتمييز الصف التالي من الصلاة
            row_data['icon'].config(font=('Segoe UI', 12, 'bold'))
            row_data['prayer'].config(font=('Segoe UI', 12, 'bold'))
            row_data['period'].config(font=('Segoe UI', 12, 'bold'))

            for widget in row_data.values():
                if isinstance(widget, tk.Label):
                    widget.config(bg=highlight_color)
    
    def update_calendar_display(self, city_data: dict):
        """تحديث عرض التقويم"""
        greg_parts = city_data['gregorian_date'].split('-')
        if len(greg_parts) == 3:
            day, month, year = greg_parts
            month_names_ar = {'01': 'يناير', '02': 'فبراير', '03': 'مارس', '04': 'أبريل', '05': 'مايو', '06': 'يونيو', '07': 'يوليو', '08': 'أغسطس', '09': 'سبتمبر', '10': 'أكتوبر', '11': 'نوفمبر', '12': 'ديسمبر'}
            month_names_en = {'01': 'January', '02': 'February', '03': 'March', '04': 'April', '05': 'May', '06': 'June', '07': 'July', '08': 'August', '09': 'September', '10': 'October', '11': 'November', '12': 'December'}
            month_names = month_names_ar if self.settings.language == 'ar' else month_names_en
            self.greg_day_label.config(text=day)
            self.greg_month_label.config(text=month_names.get(month, month))
            self.greg_year_label.config(text=year)
        
        hijri_text = city_data['hijri_date']
        hijri_parts = hijri_text.split()
        
        if len(hijri_parts) >= 3:
            hijri_day = hijri_parts[0]
            hijri_year = hijri_parts[-1]
            hijri_month = ' '.join(hijri_parts[1:-1])
            
            self.hijri_day_label.config(text=hijri_day)
            self.hijri_month_label.config(text=hijri_month)
            self.hijri_year_label.config(text=hijri_year)
    
    # تخزين مؤقت لتحويلات الوقت لتحسين الأداء
    _time_conversion_cache = {}
    _MAX_TIME_CACHE_SIZE = 50
    
    def time_to_minutes(self, time_str: str) -> int:
        """
        تحويل الوقت إلى دقائق مع تحسين معالجة الأخطاء وتخزين النتائج للاستخدام المتكرر        
        :param time_str: سلسلة الوقت بتنسيق "HH:MM AM/PM" أو "HH:MM ص/م"
        :return: الوقت محولاً إلى دقائق (من 0 إلى 1439)
        """
        # التحقق من التخزين المؤقت أولاً للتحسين
        if time_str in self._time_conversion_cache:
            return self._time_conversion_cache[time_str]
            
        if not time_str:
            logger.warning("محاولة تحويل سلسلة وقت فارغة إلى دقائق")
            return 0
            
        try:
            # توحيد تنسيق السلسلة للتخزين المؤقت الفعّال
            time_str = time_str.strip().upper()
            match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|ص|م)', time_str)
            
            if not match:
                logger.warning(f"تنسيق وقت غير صحيح: {time_str}")
                return 0
                
            hours, minutes, period = int(match.group(1)), int(match.group(2)), match.group(3)
            
            # تحقق من صحة الوقت
            if hours < 0 or hours > 12 or minutes < 0 or minutes > 59:
                logger.warning(f"قيم وقت غير صالحة: الساعات={hours}, الدقائق={minutes}")
                return 0
                
            # تحويل الوقت من نظام 12 ساعة إلى نظام 24 ساعة
            if (period == 'م' or period == 'PM') and hours != 12:
                hours += 12
            elif (period == 'ص' or period == 'AM') and hours == 12:
                hours = 0
            
            # حساب الدقائق الكلية
            total_minutes = hours * 60 + minutes
            
            # تخزين النتيجة في التخزين المؤقت
            if len(self._time_conversion_cache) >= self._MAX_TIME_CACHE_SIZE:
                # حذف عنصر عشوائي إذا امتلأ التخزين المؤقت
                self._time_conversion_cache.pop(next(iter(self._time_conversion_cache)))
                
            self._time_conversion_cache[time_str] = total_minutes
            return total_minutes
            
        except Exception as e:
            logger.error(f"خطأ في تحويل الوقت {time_str}: {e}")
            return 0
    
    def show_loading(self):
        """إظهار رسالة التحميل"""
        for widget in self.table_container.winfo_children():
            widget.destroy()
        
        self.loading_label = tk.Label(self.table_container, text=self._("loading_prayer_times"), font=('Segoe UI', 14), bg=self.colors['bg_card'], fg=self.colors['text_secondary'])
        self.loading_label.pack(expand=True)
    
    def hide_loading(self):
        """إخفاء رسالة التحميل"""
        if hasattr(self, 'loading_label'):
            self.loading_label.pack_forget()
    
    def start_auto_update(self):
        """بدء التحديث التلقائي مع فترات تكيفية"""
        def scheduled_update():
            try:
                if not self.root.winfo_exists() or not self.running:
                    return

                # حساب الفترة المناسبة للتحديث التالي
                next_update_interval = self._calculate_optimal_update_interval()

                # تحديث عناصر الواجهة المطلوبة
                self.update_time_display_realtime()
                self.update_next_prayer()
                self.update_prayer_statuses()  # تحديث حالة الصلوات في الجدول

                # إعادة جدولة التحديث التالي بناءً على الفترة المحسوبة
                self.root.after(next_update_interval, scheduled_update)
            except Exception as e:
                logger.error(f"خطأ في حلقة التحديث {e}", exc_info=True)

        # بدء نظام التحديث وفحص الإشعارات
        self.root.after(1000, scheduled_update)  # بدء التحديث بعد ثانية واحدة
        self.check_prayer_notifications()  # بدء نظام الإشعارات منفصلاً
    
    def _calculate_optimal_update_interval(self):
        """حساب الفترة المثلى للتحديث بناءً على حالة التطبيق"""
        # التحديث الافتراضي كل 60 ثانية
        default_interval = 60000  # 60 ثانية
        
        if not self.current_city or self.current_city not in self.prayer_data:
            return default_interval
        
        now = datetime.now()
        current_seconds = now.hour * 3600 + now.minute * 60 + now.second
        
        # الحصول على وقت الصلاة التالية
        next_prayer_seconds = None
        prayers_orig = []
        
        try:
            city_data = self.prayer_data[self.current_city]
            prayers_orig = [
                (self._('fajr'), city_data['fajr_orig']),
                (self._('sunrise'), city_data['sunrise_orig']),
                (self._('dhuhr'), city_data['dhuhr_orig']),
                (self._('asr'), city_data['asr_orig']),
                (self._('maghrib'), city_data['maghrib_orig']),
                (self._('isha'), city_data['isha_orig'])
            ]
            
            # حساب الوقت المتبقي للصلاة التالية
            for name, time_str in prayers_orig:
                prayer_minutes = self.time_to_minutes(time_str)
                prayer_seconds = prayer_minutes * 60
                if prayer_seconds > current_seconds:
                    next_prayer_seconds = prayer_seconds
                    break
            
            # إذا لم نجد صلاة تالية، فالصلاة التالية هي صلاة الفجر في اليوم التالي
            if next_prayer_seconds is None and prayers_orig:
                next_prayer_seconds = self.time_to_minutes(prayers_orig[0][1]) * 60 + 24 * 3600
        except Exception as e:
            logger.warning(f"خطأ في حساب فترة التحديث المثلى: {e}")
            return default_interval
        
        if next_prayer_seconds is None:
            return default_interval
        
        # حساب الثواني المتبقية للصلاة التالية
        seconds_until_next_prayer = next_prayer_seconds - current_seconds
        
        # تحديد فترة التحديث المثلى بناءً على الوقت المتبقي
        if seconds_until_next_prayer < 60:  # أقل من دقيقة
            return 1000  # تحديث كل ثانية
        elif seconds_until_next_prayer < 300:  # أقل من 5 دقائق
            return 5000  # تحديث كل 5 ثوانٍ
        elif seconds_until_next_prayer < 1800:  # أقل من 30 دقيقة
            return 15000  # تحديث كل 15 ثانية
        else:
            return 60000  # تحديث كل دقيقة
    
    def update_time_display_realtime(self):
        """تحديث عرض الوقت الحقيقي"""
        current_time = datetime.now()
        time_str = current_time.strftime("%H:%M:%S")
        date_str = current_time.strftime("%Y-%m-%d")
        
        if hasattr(self, 'current_time_label'):
            self.current_time_label.config(text=self._("current_time_label", time_str=time_str))
        if hasattr(self, 'time_sync_label'):
            self.time_sync_label.config(text=self._("date_label", date_str=date_str))
    
    def check_connection(self):
        """فحص حالة الاتصال بشكل دوري مع تحسين الكفاءة"""
        def connection_test():
            check_interval = 5 * 60  # فحص كل 5 دقائق بدلاً من كل دقيقة
            while self.running:
                try:
                    # استخدام موقع خفيف لفحص الاتصال
                    response = requests.get("https://www.google.com", timeout=5)
                    self.is_online = response.status_code == 200
                except requests.exceptions.RequestException:
                    self.is_online = False
                
                if not self.running:
                    break

                if self.root.winfo_exists():
                    self.root.after(0, self.update_connection_status)
                
                # استخدام فترات زمنية أقصر للفحص إذا تم إيقاف التطبيق
                for _ in range(check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        self.executor.submit(connection_test)
    
    def update_connection_status(self):
        """تحديث مؤشر حالة الاتصال"""
        if self.is_online:
            self.status_indicator.config(fg=self.colors['success'])
            self.connection_status.config(text=self._("connected"))
        else:
            self.status_indicator.config(fg=self.colors['error'])
            self.connection_status.config(text=self._("disconnected"))

    def update_last_update_time(self):
        """تحديث وقت آخر تحديث في شريط الحالة"""
        now = datetime.now()
        update_time_str = now.strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self, 'last_update_label'):
            self.last_update_label.config(text=f'{self._("last_update")} {update_time_str}')
    

    def open_settings(self):
        """فتح نافذة الإعدادات"""
        old_country = self.settings.selected_country
        old_city = self.settings.selected_city
        old_method = self.settings.calculation_method

        def on_settings_saved():
            location_changed = (self.settings.selected_country != old_country or
                                self.settings.selected_city != old_city)
            method_changed = self.settings.calculation_method != old_method

            if location_changed or method_changed:
                self.manual_refresh(show_success_message=False)

        try:
            settings_dialog = SettingsDialog(self, self.settings, self.colors, on_save_callback=on_settings_saved)
        except Exception as e:
            logger.error(f"خطأ في فتح الإعدادات {e}")
            messagebox.showerror(self._("error"), self._("error_opening_settings"))
    
    def manual_refresh(self, show_success_message=True):
        """تحديث يدوي للبيانات"""
        if self.settings.selected_city and self.settings.selected_country:
            city_to_clear = self.settings.selected_city
            country_to_clear = self.settings.selected_country
            cache_file = self.cache_manager.get_cache_file(city_to_clear, country_to_clear)
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"تم حذف البيانات المؤقتة لـ {city_to_clear}, {country_to_clear}")

            self.fetch_and_display_times(city_to_clear, country_to_clear)
            if show_success_message:
                messagebox.showinfo(self._("updated_successfully"), self._("prayer_times_updated_successfully") )
        else:
            messagebox.showwarning(self._("error"), self._("please_select_city_country") )
        
    def show_error(self, message: str):
        """عرض رسالة خطأ"""
        logger.error(f"خطأ في التطبيق {message}")
        
        error_label = tk.Label(self.table_container, text=f'❌ {self._("error")} {message}', font=('Segoe UI', 12), bg=self.colors['bg_card'], fg=self.colors['error'], wraplength=400)
        error_label.pack(expand=True, pady=20)
        
        self.root.after(5000, lambda: error_label.destroy() if error_label.winfo_exists() else None)
    
    def custom_askyesno(self, title, message):
        """إنشاء صندوق رسالة مخصص يحتوي على أزرار مترجمة"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.configure(bg=self.colors['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        # مركز الحوار فوق النافذة الرئيسية
        self.root.update_idletasks()
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        result = [None]

        def yes_action():
            result[0] = True
            dialog.destroy()

        def no_action():
            result[0] = False
            dialog.destroy()

        msg_label = tk.Label(dialog, text=message, font=('Segoe UI', 12), bg=self.colors['bg_primary'], fg=self.colors['text_primary'], pady=20, padx=20)
        msg_label.pack()

        button_frame = tk.Frame(dialog, bg=self.colors['bg_primary'], pady=10)
        button_frame.pack()

        yes_button = tk.Button(button_frame, text=self._("yes"), font=('Segoe UI', 11), bg=self.colors['success'], fg=self.colors['text_accent'], relief='flat', padx=10, pady=5, cursor='hand2', command=yes_action)
        yes_button.pack(side='left', padx=10)

        no_button = tk.Button(button_frame, text=self._("no"), font=('Segoe UI', 11), bg=self.colors['error'], fg=self.colors['text_accent'], relief='flat', padx=10, pady=5, cursor='hand2', command=no_action)
        no_button.pack(side='left', padx=10)
        
        dialog.wait_window()
        return result[0]

    def on_closing(self):
        """عند إغلاق التطبيق"""
        if self.custom_askyesno(
            self._("exit_confirmation"),
            self._("exit_confirmation_message")
        ):
            self.quit_application()
        else:
            if self.tray_icon:
                self.root.withdraw()

    def minimize_to_tray(self, event=None):
        """تصغير التطبيق إلى شريط المهام عند الضغط على زر التصغير"""
        if self.root.state() == 'iconic' and self.tray_icon:
            self.root.withdraw()
            self.notification_manager.send_notification(
                self._("app_running_in_background"),
                self._("app_running_in_background_message"),
                timeout=5
            )

    def setup_tray_icon(self):
        """إعداد أيقونة شريط المهام"""
        if not _import_pystray_and_pil():
            return

        menu = TrayMenu(
            TrayMenuItem(self._("show_window"), self.show_window, default=True),
            TrayMenuItem(self._("quit"), self.request_quit_from_tray)
        )

        try:
            image = PIL_Image.open(get_working_path("pray_times.ico"))
        except FileNotFoundError:
            logger.warning("pray_times.ico not found, creating a default tray icon.")
            image = PIL_Image.new('RGB', (64, 64), 'black')
            draw = PIL_ImageDraw.Draw(image)
            draw.rectangle((0, 0, 63, 63), fill='black', outline='white')
            draw.text((25, 20), 'P', fill='white')

        self.tray_icon = TrayIcon("PrayerTimes", image, self._("prayer_times"), menu)

        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def show_window(self):
        """إظهار نافذة التطبيق"""
        self.root.deiconify()

    def request_quit_from_tray(self):
        """Requests the application to quit from the tray menu."""
        if hasattr(self, 'root') and self.root.winfo_exists():
            self.root.event_generate('<<QuitApp>>')

    def quit_application(self):
        """معالج إغلاق التطبيق"""
        self.running = False
        if self.tray_icon:
            self.tray_icon.stop()
            if hasattr(self, 'tray_thread') and self.tray_thread.is_alive() and threading.current_thread() is not self.tray_thread:
                self.tray_thread.join(timeout=1.0)
        try:
            if hasattr(self, '_countdown_running'):
                self._countdown_running = False

            if hasattr(self, 'adhan_player'):
                self.adhan_player.stop_sound()

            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True)

            self.settings.save_settings()

            # cleanup_pyinstaller يتم استدعاؤه تلقائيًا عبر atexit
            logger.info("تم إغلاق التطبيق بنجاح")

        except Exception as e:
            logger.error(f"خطأ أثناء إغلاق التطبيق {e}")
        finally:
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.destroy_scroll_area()
                self.root.update()
                self.root.quit()
            try:
                self.root.destroy()
            except tk.TclError as e:
                logger.error(f"Error destroying root window: {e}")
    
    def destroy_scroll_area(self):
        """تنظيف وتدمير عناصر التمرير بشكل آمن"""
        try:
            # فصل الأحداث المرتبطة بالـ root و canvas
            if hasattr(self, 'root') and self.root.winfo_exists():
                self.root.unbind('<MouseWheel>')
                self.root.unbind('<Button-4>')
                self.root.unbind('<Button-5>')
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.canvas.unbind('<Configure>')
                self.canvas.config(yscrollcommand=lambda *args: None)
            if hasattr(self, 'scrollable_frame') and self.scrollable_frame.winfo_exists():
                self.scrollable_frame.unbind('<Configure>')
            if hasattr(self, 'scrollbar') and self.scrollbar.winfo_exists():
                self.scrollbar.destroy()
            if hasattr(self, 'canvas') and self.canvas.winfo_exists():
                self.canvas.destroy()
            if hasattr(self, 'container') and self.container.winfo_exists():
                self.container.destroy()
        except Exception as e:
            print(f"خطأ أثناء تدمير عناصر التمرير {e}")

    def on_frame_configure(self, event=None):
        """إعادة تعيين منطقة التمرير لتشمل الإطار الداخلي"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event=None):
        """تعديل عرض الإطار الداخلي ليتناسب مع عرض اللوحة"""
        self.canvas.itemconfig(self.canvas_frame, width=event.width)

    def _on_mousewheel(self, event):
        """معالجة التمرير بعجلة الماوس لنظام Windows وMac"""
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_button_4(self, event):
        """معالجة التمرير بعجلة الماوس لنظام Linux (التمرير لأعلى)"""
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(-1, "units")

    def _on_button_5(self, event):
        """معالجة التمرير بعجلة الماوس لنظام Linux (التمرير لأسفل)"""
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(1, "units")

    def run(self):
        """تشغيل التطبيق"""
        self.check_connection()
        
        logger.info("تم بدء تشغيل التطبيق بنجاح")
        self.root.update_idletasks()
        self.root.mainloop()