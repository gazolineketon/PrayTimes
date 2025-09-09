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

from config import Translator
from settings_manager import Settings
from data_manager import CacheManager, get_countries, get_cities
from prayer_logic import TimeSync
from media_manager import AdhanPlayer, NotificationManager, NOTIFICATIONS_AVAILABLE
from ui_components import SettingsDialog
from qibla_ui import QiblaWidget

logger = logging.getLogger(__name__)

class EnhancedPrayerTimesApp:
    """تطبيق مواقيت الصلاة"""
    def __init__(self):
        self.root = tk.Tk()
        self.version = "2.0.0"
        
        # تهيئة المكونات
        self.settings = Settings()
        self.translator = Translator(self.settings.language)
        self._ = self.translator.get
        
        self.root.title(self._("prayer_times"))
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
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def on_closing(self):
        """عند إغلاق التطبيق"""
        self.running = False
        self.executor.shutdown(wait=False)
        self.root.destroy()

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
        container = tk.Frame(self.root)
        container.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(container, orient='vertical')
        scrollbar.pack(side='right', fill='y')

        self.canvas = tk.Canvas(container, bg=self.colors['bg_primary'], highlightthickness=0, yscrollcommand=scrollbar.set)
        self.canvas.pack(side='left', fill='both', expand=True)

        scrollbar.config(command=self.canvas.yview)

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
        
        self.greg_month_frame = self.create_date_box(greg_boxes_frame, self.colors['bg_accent'], 90, 35)
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

        self.hijri_month_frame = self.create_date_box(hijri_boxes_frame, self.colors['warning'], 90, 35)
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
        
        prayers_title = tk.Label(prayers_container, text=self._("prayer_times_table_title"), font=('Segoe UI', 16, 'bold'), bg=self.colors['bg_card'], fg=self.colors['text_primary'])
        prayers_title.pack(pady=(0, 15))
        
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
    
    def robust_api_call(self, url: str, params: dict, retries: int = 3):
        """استدعاء API مع إعادة المحاولة"""
        for attempt in range(retries):
            try:
                response = requests.get(url, params=params, timeout=15)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"محاولة {attempt + 1} فشلت {e}")
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)
        return None
    
    
    
    def parse_api_data(self, city: str, data: dict):
        """تحليل البيانات من API مع تحسينات"""
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
        
        self.update_calendar_display(city_data)
        
        for widget in self.table_container.winfo_children():
            widget.destroy()
        
        table_frame = tk.Frame(self.table_container, bg=self.colors['bg_card'])
        table_frame.pack(fill='both', expand=True)
        
        columns = [("status", 80, "center"), ("period", 60, "center"), ("time", 80, "center"), ("prayer", 80, "center"), ("icon", 50, "center")]
        
        for i, (col_name, width, anchor) in enumerate(columns):
            table_frame.grid_columnconfigure(i, weight=1, minsize=width)
        
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
        tk.Label(table_frame, text=self._("table_header_status"), **header_style).grid(row=0, column=0, sticky='nsew')

        # عنوان الوقت
        tk.Label(table_frame, text=self._("table_header_time"), **header_style).grid(row=0, column=1, columnspan=2, sticky='nsew')

        # عنوان الصلاة
        tk.Label(table_frame, text=self._("table_header_prayer"), **header_style).grid(row=0, column=3, columnspan=4, sticky='nsew')
        
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
            
            status_label = tk.Label(table_frame, text=status, fg=status_color, font=('Segoe UI', 10, 'bold'), anchor="center", **{k: v for k, v in cell_style.items() if k not in ['fg', 'font']})
            status_label.grid(row=row_num, column=0, sticky='nsew', pady=1)
            
            period_label = tk.Label(table_frame, text=prayer_period, anchor="e", **cell_style)
            period_label.grid(row=row_num, column=1, sticky='nsew', pady=1)
            
            time_label = tk.Label(table_frame, text=prayer_time, font=('Segoe UI', 14, 'bold'), anchor="w", **{k: v for k, v in cell_style.items() if k != 'font'})
            time_label.grid(row=row_num, column=2, sticky='nsew', pady=1)
            
            prayer_label = tk.Label(table_frame, text=prayer_name, anchor="e", **cell_style)
            prayer_label.grid(row=row_num, column=3, sticky='nsew', pady=1)
            
            icon_label = tk.Label(table_frame, text=icon, anchor="w", **cell_style)
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
        """تحديث العد التنازلي"""
        if not hasattr(self, '_countdown_running') or not self._countdown_running:
            return
        
        if not self.current_city or self.current_city not in self.prayer_data:
            if self.root.winfo_exists() and self._countdown_running:
                self.root.after(1000, self.update_countdown)
            return
        
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
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
        next_prayer_minutes = None
        
        for name, time_str in prayers_orig:
            prayer_minutes = self.time_to_minutes(time_str)
            if prayer_minutes > current_minutes:
                next_prayer = name
                next_prayer_minutes = prayer_minutes
                break
        # إذا كانت الصلاة القادمة هي الفجر في اليوم التالي
        if next_prayer is None:
            next_prayer = self._('fajr')
            next_prayer_minutes = self.time_to_minutes(prayers_orig[0][1]) + 24 * 60
        
        remaining_minutes = next_prayer_minutes - current_minutes
        hours = remaining_minutes // 60
        minutes = remaining_minutes % 60
        
        if hours > 0:
            countdown_text = f'{self._("remaining_time_on")} {next_prayer}: {hours} {self._("hour")} و {minutes} {self._("minute")}'
        else:
            countdown_text = f'{self._("remaining_time_on")} {next_prayer}: {minutes} {self._("minute")}'
        
        if remaining_minutes <= 5: color = self.colors['error']
        elif remaining_minutes <= 30: color = self.colors['warning']
        else: color = self.colors['success']
        
        self.countdown_label.config(text=countdown_text, fg=color)
        
        if self.root.winfo_exists() and self._countdown_running:
            self.root.after(1000, self.update_countdown)
    
    def check_prayer_notifications(self):
        """فحص وإرسال إشعارات الصلوات"""
        if not self.settings.notifications_enabled or not NOTIFICATIONS_AVAILABLE:
            return
        
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        if not self.current_city or self.current_city not in self.prayer_data:
            return
        
        city_data = self.prayer_data[self.current_city]
        prayers = [
            (self._('fajr'), city_data['fajr_orig']),
            (self._('dhuhr'), city_data['dhuhr_orig']),
            (self._('asr'), city_data['asr_orig']),
            (self._('maghrib'), city_data['maghrib_orig']),
            (self._('isha'), city_data['isha_orig'])
        ]
        
        for prayer_name, prayer_time_str in prayers:
            prayer_datetime = datetime.strptime(prayer_time_str.split()[0], "%I:%M")
            if (prayer_time_str.endswith('م') or prayer_time_str.endswith('PM')) and prayer_datetime.hour != 12:
                prayer_datetime = prayer_datetime.replace(hour=prayer_datetime.hour + 12)
            elif (prayer_time_str.endswith('ص') or prayer_time_str.endswith('AM')) and prayer_datetime.hour == 12:
                prayer_datetime = prayer_datetime.replace(hour=0)
            
            notification_time = prayer_datetime - timedelta(minutes=self.settings.notification_before_minutes)
            notification_time_str = notification_time.strftime("%H:%M")
            
            if current_time == notification_time_str:
                if prayer_name not in self.last_notification_time or self.last_notification_time[prayer_name] != current_time:
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
                    self.last_notification_time[prayer_name] = current_time
            
            prayer_time_24 = prayer_datetime.strftime("%H:%M")
            if current_time == prayer_time_24:
                if f"{prayer_name}_adhan" not in self.last_notification_time or self.last_notification_time[f"{prayer_name}_adhan"] != current_time:
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
                    
                    self.last_notification_time[f"{prayer_name}_adhan"] = current_time
    
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
    
    def time_to_minutes(self, time_str: str) -> int:
        """تحويل الوقت إلى دقائق"""
        try:
            time_str = time_str.strip().upper()
            match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM|ص|م)', time_str)
            
            if not match:
                return 0
                
            hours, minutes, period = int(match.group(1)), int(match.group(2)), match.group(3)
            
            if (period == 'م' or period == 'PM') and hours != 12:
                hours += 12
            elif (period == 'ص' or period == 'AM') and hours == 12:
                hours = 0
                
            return hours * 60 + minutes
        except Exception as e:
            logger.error(f"خطأ في تحويل الوقت {time_str} {e}")
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
        """بدء التحديث التلقائي"""
        def scheduled_update():
            try:
                if self.root.winfo_exists():
                    self.update_time_display_realtime()
                    self.update_next_prayer()
                    self.check_prayer_notifications()
                    
                    # إعادة جدولة التحديث التالي
                    self.root.after(self.settings.auto_update_interval * 1000, scheduled_update)
            except Exception as e:
                logger.error(f"خطأ في حلقة التحديث {e}", exc_info=True)

        # بدء التحديث الأولي
        self.root.after(self.settings.auto_update_interval * 1000, scheduled_update)
    
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
        """فحص حالة الاتصال بشكل دوري"""
        def connection_test():
            while self.running:
                try:
                    response = requests.get("https://www.google.com", timeout=5)
                    self.is_online = response.status_code == 200
                except requests.exceptions.RequestException:
                    self.is_online = False
                
                if not self.running:
                    break

                if self.root.winfo_exists():
                    self.root.after(0, self.update_connection_status)
                
                for _ in range(60):
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
        """عرض رسالة خطأ محسّنة"""
        logger.error(f"خطأ في التطبيق {message}")
        
        error_label = tk.Label(self.table_container, text=f'❌ {self._("error")} {message}', font=('Segoe UI', 12), bg=self.colors['bg_card'], fg=self.colors['error'], wraplength=400)
        error_label.pack(expand=True, pady=20)
        
        self.root.after(5000, lambda: error_label.destroy() if error_label.winfo_exists() else None)
    
    def on_closing(self):
        """معالج إغلاق التطبيق"""
        self.running = False
        try:
            if hasattr(self, '_countdown_running'):
                self._countdown_running = False
            
            if hasattr(self, 'adhan_player'):
                self.adhan_player.stop_sound()
            
            if hasattr(self, 'executor'):
                self.executor.shutdown(wait=True, cancel_futures=True)
            
            self.cache_manager.cleanup_old_cache()
            
            self.settings.save_settings()
            
            logger.info("تم إغلاق التطبيق بنجاح")
            
        except Exception as e:
            logger.error(f"خطأ أثناء إغلاق التطبيق {e}")
        finally:
            self.root.destroy()
    
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
        self.root.mainloop()