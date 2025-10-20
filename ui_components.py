# -*- coding: utf-8 -*-

"""
ui_components.py
SettingsDialog يحتوي هذا الملف على أجزاء الواجهة الرسومية القابلة لإعادة الاستخدام مثل
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes

# تأجيل استيراد PIL حتى يتم استخدامه فعلياً
PIL_AVAILABLE = False
PIL_ImageTk = None
PIL_Image = None

def _import_pil():
    """استيراد PIL عند الحاجة"""
    global PIL_AVAILABLE, PIL_ImageTk, PIL_Image
    if not PIL_AVAILABLE:
        try:
            from PIL import ImageTk, Image
            PIL_ImageTk = ImageTk
            PIL_Image = Image
            PIL_AVAILABLE = True
        except ImportError:
            PIL_AVAILABLE = False
    return PIL_AVAILABLE
from config import CALCULATION_METHODS, CALCULATION_METHODS_REV, CALCULATION_METHODS_EN, CALCULATION_METHODS_EN_REV
from data_manager import get_cities
from settings_manager import Settings
from qibla_ui import QiblaWidget
from media_manager import AdhanPlayer
from resource_helper import get_working_path

class SettingsDialog:
    """نافذة الإعدادات"""
    def __init__(self, parent, settings: Settings, colors, on_save_callback=None):
        self.parent = parent
        self.settings = settings
        self._ = self.parent._
        self.colors = colors
        self.on_save_callback = on_save_callback
        self.dialog = None
        self.cities = []
        self.all_cities = []
        self.country_dropdown = None
        self.city_dropdown = None
        self.country_listbox = None
        self.city_listbox = None
        self.current_dropdown = None
        self.sound_player = AdhanPlayer()
        self.playing_sound = None
        self.tooltips = {}  # تخزين تلميحات الأدوات
        self.loading = False  # تتبع حالة التحميل
        self.close_bind_id = None  # تخزين معرف الربط للتنظيف
        self.scroll_job = None  # تخزين معرف التمرير المستمر
        self.create_dialog()
        
    def set_tooltip(self, widget, text):
        """إضافة تلميح للأداة لتسهيل الوصول"""
        def show_tooltip(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            
            # إنشاء نافذة تلميح
            tooltip = tk.Toplevel(widget)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            label = tk.Label(tooltip, text=text, justify='left',
                           background="#ffffe0", relief='solid', borderwidth=1)
            label.pack()
            
            self.tooltips[widget] = tooltip
            
        def hide_tooltip(event):
            if widget in self.tooltips:
                self.tooltips[widget].destroy()
                del self.tooltips[widget]
                
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)
    
    def create_dialog(self):
        """إنشاء نافذة الإعدادات"""
        self.dialog = tk.Toplevel(self.parent.root)
        self.dialog.title(self._("app_settings"))
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent.root)
        self.dialog.grab_set()
        try:
            self.dialog.iconbitmap(get_working_path("pray_times.ico"))
        except tk.TclError:
            pass
        
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self.setup_settings_ui()

    def close_country_dropdown(self, event=None):
        """إغلاق القائمة المنسدلة للبلدان"""
        if self.country_dropdown:
            self.country_dropdown.withdraw()

    def close_city_dropdown(self, event=None):
        """إغلاق القائمة المنسدلة للمدن"""
        if self.city_dropdown:
            self.city_dropdown.withdraw()

    def show_country_dropdown(self, event=None):
        """إظهار القائمة المنسدلة لاختيار البلد"""
        if self.country_dropdown and self.country_dropdown.winfo_ismapped():
            return
        self.show_dropdown('country')

    def show_city_dropdown(self, event=None):
        """إظهار القائمة المنسدلة لاختيار المدينة"""
        if self.city_dropdown and self.city_dropdown.winfo_ismapped():
            return
        self.show_dropdown('city')

    def show_dropdown(self, dropdown_type):
        """إظهار القائمة المنسدلة مع التركيز المناسب وإدارة الأحداث"""
        if self.loading:
            return
            
        # تحديد الأدوات التي سيتم استخدامها
        if dropdown_type == 'country':
            dropdown = self.country_dropdown
            entry = self.country_entry
            frame = self.country_frame
            listbox = self.country_listbox if hasattr(self, 'country_listbox') else None
            items = self.parent.countries if hasattr(self.parent, 'countries') else []
            if self.settings.language == 'ar':
                items = [arabic_name for _, arabic_name in items]
            else:
                items = [english_name for english_name, _ in items]
        else:
            dropdown = self.city_dropdown
            entry = self.city_entry
            frame = self.city_frame
            listbox = self.city_listbox if hasattr(self, 'city_listbox') else None
            items = self.all_cities if hasattr(self, 'all_cities') else []

        # إنشاء قائمة منسدلة إذا لم تكن موجودة
        if not dropdown:
            dropdown = tk.Toplevel(self.dialog)
            dropdown.overrideredirect(True)
            
            frame_inner = tk.Frame(dropdown)
            scrollbar = tk.Scrollbar(frame_inner, orient=tk.VERTICAL)
            listbox = tk.Listbox(frame_inner, 
                              font=('Segoe UI', 12),
                              selectmode='single',
                              yscrollcommand=scrollbar.set,
                              activestyle='dotbox')  # يجعل الاختيار أكثر وضوحًا
            
            # تكوين شريط التمرير
            scrollbar.config(command=listbox.yview)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            frame_inner.pack(fill=tk.BOTH, expand=True)
            
            # إعداد روابط الأحداث
            listbox.bind('<Double-Button-1>', 
                       lambda e: self.on_country_select() if dropdown_type == 'country' else self.on_city_select())
            listbox.bind('<Return>',
                       lambda e: self.on_country_select() if dropdown_type == 'country' else self.on_city_select())
            listbox.bind('<Escape>', lambda e: self.close_dropdown(dropdown_type))
            
            # تخزين المراجع
            if dropdown_type == 'country':
                self.country_dropdown = dropdown
                self.country_listbox = listbox
            else:
                self.city_dropdown = dropdown
                self.city_listbox = listbox
        
        # تحديث محتويات مربع القائمة
        listbox.delete(0, tk.END)
        for item in items:
            listbox.insert(tk.END, item)
            
        # وضع القائمة المنسدلة أسفل حقل الإدخال
        x = frame.winfo_rootx()
        y = frame.winfo_rooty() + frame.winfo_height()
        
        # حساب الأبعاد
        self.dialog.update_idletasks()
        frame.update_idletasks()
        frame_width = frame.winfo_width()
        if frame_width <= 0:
            frame_width = 300
        frame_width += 20  # إضافة مساحة لشريط التمرير
        height = min(200, listbox.size() * 20 + 10)
        
        dropdown.geometry(f"{frame_width}x{height}+{x}+{y}")
        
        # إظهار القائمة المنسدلة وتعيين التركيز
        dropdown.lift()
        dropdown.deiconify()
        
        # إعداد معالجة التركيز
        dropdown.bind('<FocusOut>', lambda e: self.handle_focus_lost(e, dropdown_type))
        entry.focus_set()
        
        # تحديث التتبع
        self.current_dropdown = dropdown_type
        self.close_bind_id = self.dialog.bind_all('<Button-1>', self.check_close_dropdown)
        
        # تحديد العنصر الأول في حالة وجوده
        if listbox.size() > 0:
            listbox.selection_set(0)
            listbox.see(0)

    def handle_focus_lost(self, event, dropdown_type):
        """معالجة فقدان التركيز للقوائم المنسدلة"""
        widget = event.widget
        
        # الحصول على الأدوات ذات الصلة
        dropdown = self.country_dropdown if dropdown_type == 'country' else self.city_dropdown
        entry = self.country_entry if dropdown_type == 'country' else self.city_entry
        
        # التحقق مما إذا كان التركيز قد انتقل إلى أداة ذات صلة
        focus_widget = self.dialog.focus_get()
        if focus_widget in (entry, dropdown):
            return
            
        # إغلاق القائمة المنسدلة إذا انتقل التركيز إلى مكان آخر
        self.close_dropdown(dropdown_type)

    def close_dropdown(self, dropdown_type):
        """إغلاق القائمة المنسدلة وتنظيف الروابط"""
        dropdown = self.country_dropdown if dropdown_type == 'country' else self.city_dropdown
        if not dropdown:
            return
            
        dropdown.withdraw()
        dropdown.unbind('<FocusOut>')
        dropdown.unbind('<Escape>')
        
        if self.current_dropdown == dropdown_type:
            self.current_dropdown = None
            
        if hasattr(self, 'close_bind_id'):
            try:
                self.dialog.unbind('<Button-1>', self.close_bind_id)
            except Exception as e:
                print(f"Error unbinding event: {e}")
    
    def setup_settings_ui(self):
        """إعداد واجهة الإعدادات"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text=self._("general"))
        self.setup_general_settings(general_frame)
        
        notifications_frame = ttk.Frame(notebook)
        notebook.add(notifications_frame, text=self._("notifications"))
        self.setup_notifications_settings(notifications_frame)
        
        audio_frame = ttk.Frame(notebook)
        notebook.add(audio_frame, text=self._("sounds"))
        self.setup_audio_settings(audio_frame)
        
        qibla_frame = ttk.Frame(notebook)
        notebook.add(qibla_frame, text=self._("qibla"))
        self.setup_qibla_settings(qibla_frame)
        
        location_frame = ttk.Frame(notebook)
        notebook.add(location_frame, text=self._("location"))
        self.setup_location_settings(location_frame)
        
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text=self._("about"))
        self.setup_about_tab(about_frame)
        
        buttons_frame = tk.Frame(self.dialog)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        # زر حفظ الإعدادات
        ttk.Button(buttons_frame, text=self._("save"), command=self.save_settings).pack(side='right', padx=(5, 0))
        ttk.Button(buttons_frame, text=self._("cancel"), command=self.dialog.destroy).pack(side='right')
        ttk.Button(buttons_frame, text=self._("restore_defaults"), command=self.reset_settings).pack(side='left')

    def setup_about_tab(self, parent):
        """إعداد تبويب حول"""
        # الإطار الرئيسي
        main_frame = tk.Frame(parent, bg=self.colors.get('bg_secondary', '#FFFFFF'))
        main_frame.pack(fill='both', expand=True)

        # وضع المحتوى بالمنتصف
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # إطار الشعار
        logo_frame = tk.Frame(main_frame, bg=self.colors.get('bg_secondary', '#FFFFFF'))
        logo_frame.grid(row=0, column=0, sticky='s')

        # تحميل وعرض الشعار
        if _import_pil():
            try:
                img = PIL_Image.open(get_working_path("pray_logo.png"))
                img = img.resize((128, 128), PIL_Image.LANCZOS)
                self.logo_img = PIL_ImageTk.PhotoImage(img)

                logo_label = tk.Label(logo_frame, image=self.logo_img, bg=self.colors.get('bg_secondary', '#FFFFFF'))
                logo_label.pack(pady=(20, 10))
            except FileNotFoundError:
                tk.Label(logo_frame, text=self._("logo_not_found"), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_primary', '#000000')).pack(pady=(20, 10))
        else:
            tk.Label(logo_frame, text=self._("logo_not_found"), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_primary', '#000000')).pack(pady=(20, 10))

        # عرض معلومات البرنامج
        info_frame = tk.Frame(main_frame, bg=self.colors.get('bg_secondary', '#FFFFFF'))
        info_frame.grid(row=1, column=0, sticky='n')

        tk.Label(info_frame, text=self._("prayer_times_program"), font=("Segoe UI", 16, "bold"), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_primary', '#000000')).pack()
        tk.Label(info_frame, text=self._("programmed_by"), font=("Segoe UI", 12), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack(pady=(10, 0))
        tk.Label(info_frame, text=self._("free_for_the_sake_of_allah"), font=("Segoe UI", 10), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack()
        tk.Label(info_frame, text=self._("version_label", version=self.parent.version), font=("Segoe UI", 10), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack()

    
    def setup_general_settings(self, parent):
        """إعداد الإعدادات العامة"""
        # اللغة
        lang_frame = ttk.LabelFrame(parent, text=self._("language"))
        lang_frame.pack(fill='x', padx=10, pady=10)
        
        self.lang_var = tk.StringVar(value=self.settings.language)
        
        # إنشاء قاموس لربط رموز اللغة بأسماء العرض
        language_display_names = {"ar": self._("arabic"), "en": self._("english")}
        
        # وظيفة مساعدة للحصول على رمز اللغة من اسم العرض
        def get_lang_code(display_name):
            for code, name in language_display_names.items():
                if name == display_name:
                    return code
            return None

        # تعيين القيمة الأولية للصندوق باستخدام اسم العرض
        self.lang_display_var = tk.StringVar(value=language_display_names.get(self.settings.language))

        lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_display_var, 
                                 values=list(language_display_names.values()),
                                 state='readonly')
        lang_combo.pack(fill='x', padx=10, pady=10)
        
        # تحديث متغير رمز اللغة الداخلي عند تحديد لغة جديدة
        def on_lang_selected(event):
            selected_display_name = self.lang_display_var.get()
            lang_code = get_lang_code(selected_display_name)
            if lang_code:
                self.lang_var.set(lang_code)
                # تحديث التلميحات عند تغيير اللغة
                if hasattr(self, 'set_location_tooltips'):
                    self.set_location_tooltips(lang_code)

        lang_combo.bind('<<ComboboxSelected>>', on_lang_selected)

        # طريقة الحساب
        calc_frame = ttk.LabelFrame(parent, text=self._("prayer_calculation_method"))
        calc_frame.pack(fill='x', padx=10, pady=10)
        
        if self.settings.language == 'ar':
            current_method = CALCULATION_METHODS_REV.get(self.settings.calculation_method, "الهيئة المصرية العامة للمساحة")
            methods = list(CALCULATION_METHODS.keys())
        else:
            current_method = CALCULATION_METHODS_EN_REV.get(self.settings.calculation_method, "Egyptian General Authority of Survey")
            methods = list(CALCULATION_METHODS_EN.keys())

        self.calc_method_var = tk.StringVar(value=current_method)
        calc_combo = ttk.Combobox(calc_frame, textvariable=self.calc_method_var, 
                                 values=methods,
                                 state='readonly')
        calc_combo.pack(fill='x', padx=10, pady=10)
        
        # فترة التحديث التلقائي
        update_frame = ttk.LabelFrame(parent, text=self._("auto_update_interval"))
        update_frame.pack(fill='x', padx=10, pady=10)
        
        self.update_interval_var = tk.IntVar(value=self.settings.auto_update_interval)
        update_spinbox = ttk.Spinbox(update_frame, from_=30, to=300, 
                                   textvariable=self.update_interval_var)
        update_spinbox.pack(fill='x', padx=10, pady=10)
        
        # المظهر
        theme_frame = ttk.LabelFrame(parent, text=self._("theme"))
        theme_frame.pack(fill='x', padx=10, pady=10)
        # اختيار المظهر
        self.theme_var = tk.StringVar(value=self.settings.theme)
        ttk.Radiobutton(theme_frame, text=self._("light"), variable=self.theme_var, 
                       value="light").pack(anchor='w', padx=10, pady=5)
        ttk.Radiobutton(theme_frame, text=self._("dark"), variable=self.theme_var, 
                       value="dark").pack(anchor='w', padx=10, pady=5)
    
    def setup_notifications_settings(self, parent):
        """إعداد إعدادات الإشعارات"""
        self.notifications_var = tk.BooleanVar(value=self.settings.notifications_enabled)
        ttk.Checkbutton(parent, text=self._("enable_notifications"),
                       variable=self.notifications_var).pack(anchor='w', padx=10, pady=10)
        # وقت الإشعار قبل الصلاة
        notify_frame = ttk.LabelFrame(parent, text=self._("notification_before_prayer"))
        notify_frame.pack(fill='x', padx=10, pady=10)
        # من 0 إلى 30 دقيقة
        self.notify_before_var = tk.IntVar(value=self.settings.notification_before_minutes)
        notify_spinbox = ttk.Spinbox(notify_frame, from_=0, to=30,
                                   textvariable=self.notify_before_var)
        notify_spinbox.pack(fill='x', padx=10, pady=10)
    
    def setup_audio_settings(self, parent):
        """إعداد إعدادات الصوت"""
        self.sound_var = tk.BooleanVar(value=self.settings.sound_enabled)
        ttk.Checkbutton(parent, text=self._("enable_adhan_sounds"),
                       variable=self.sound_var).pack(anchor='w', padx=10, pady=10)

        volume_frame = ttk.LabelFrame(parent, text=self._("volume"))
        volume_frame.pack(fill='x', padx=10, pady=10)

        self.volume_var = tk.DoubleVar(value=self.settings.sound_volume)
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0,
                               variable=self.volume_var, orient='horizontal')
        volume_scale.pack(fill='x', padx=10, pady=10)

        # إعدادات الأذان لكل صلاة
        prayer_adhan_frame = ttk.LabelFrame(parent, text=self._("adhan_settings_for_each_prayer"))
        prayer_adhan_frame.pack(fill='x', padx=10, pady=10)

        # إنشاء متغيرات للصلاة
        self.fajr_adhan_var = tk.BooleanVar(value=self.settings.adhan_fajr_enabled)
        self.dhuhr_adhan_var = tk.BooleanVar(value=self.settings.adhan_dhuhr_enabled)
        self.asr_adhan_var = tk.BooleanVar(value=self.settings.adhan_asr_enabled)
        self.maghrib_adhan_var = tk.BooleanVar(value=self.settings.adhan_maghrib_enabled)
        self.isha_adhan_var = tk.BooleanVar(value=self.settings.adhan_isha_enabled)

        # إضافة مربعات التحديد لكل صلاة
        ttk.Checkbutton(prayer_adhan_frame, text=self._("fajr"), variable=self.fajr_adhan_var).pack(anchor='w', padx=10, pady=2)
        ttk.Checkbutton(prayer_adhan_frame, text=self._("dhuhr"), variable=self.dhuhr_adhan_var).pack(anchor='w', padx=10, pady=2)
        ttk.Checkbutton(prayer_adhan_frame, text=self._("asr"), variable=self.asr_adhan_var).pack(anchor='w', padx=10, pady=2)
        ttk.Checkbutton(prayer_adhan_frame, text=self._("maghrib"), variable=self.maghrib_adhan_var).pack(anchor='w', padx=10, pady=2)
        ttk.Checkbutton(prayer_adhan_frame, text=self._("isha"), variable=self.isha_adhan_var).pack(anchor='w', padx=10, pady=2)

        # ملف صوت الأذان
        adhan_sound_file_frame = ttk.LabelFrame(parent, text=self._("adhan_sound_file"))
        adhan_sound_file_frame.pack(fill='x', padx=10, pady=10)

        self.adhan_sound_file_var = tk.StringVar(value=self.settings.adhan_sound_file)
        adhan_sound_file_entry = ttk.Entry(adhan_sound_file_frame, textvariable=self.adhan_sound_file_var)
        adhan_sound_file_entry.pack(side='left', fill='x', expand=True, padx=(10, 5), pady=10)
        self.play_adhan_button = ttk.Button(adhan_sound_file_frame, text=self._("play"),
                                           command=lambda: self.toggle_sound("adhan"))
        self.play_adhan_button.pack(side='right', padx=(5, 5), pady=10)

        ttk.Button(adhan_sound_file_frame, text=self._("browse"),
                  command=self.browse_adhan_sound_file).pack(side='right', padx=(0, 10), pady=10)

        # ملف صوت التنبيه
        notification_sound_file_frame = ttk.LabelFrame(parent, text=self._("notification_sound_file"))
        notification_sound_file_frame.pack(fill='x', padx=10, pady=10)

        self.notification_sound_file_var = tk.StringVar(value=self.settings.notification_sound_file)
        notification_sound_file_entry = ttk.Entry(notification_sound_file_frame, textvariable=self.notification_sound_file_var)
        notification_sound_file_entry.pack(side='left', fill='x', expand=True, padx=(10, 5), pady=10)

        self.play_notification_button = ttk.Button(notification_sound_file_frame, text=self._("play"),
                                                      command=lambda: self.toggle_sound("notification"))
        self.play_notification_button.pack(side='right', padx=(5, 5), pady=10)

        ttk.Button(notification_sound_file_frame, text=self._("browse"),
                  command=self.browse_notification_sound_file).pack(side='right', padx=(0, 10), pady=10)
    
    def setup_qibla_settings(self, parent):
        """إعداد إعدادات القبلة"""
        qibla_widget_container = tk.Frame(parent, bg=self.colors['bg_primary'])
        qibla_widget_container.pack(fill='both', expand=True, padx=10, pady=10)

        city_name = self.parent.current_city
        country_name = self.parent.current_country

        if self.settings.language == 'ar':
            # بحث عن الاسم العربي للبلد
            for eng, ara in self.parent.countries:
                if eng == country_name:
                    country_name = ara
                    break
            # بحث عن الاسم العربي للمدينة
            if hasattr(self.parent, 'cities') and self.parent.cities:
                for eng, ara in self.parent.cities:
                    if eng == city_name:
                        city_name = ara
                        break

        self.qibla_widget = QiblaWidget(qibla_widget_container, self.settings, self.parent.translator, self.colors, city_name, country_name)
        self.qibla_widget.pack(fill='both', expand=True)

        if self.parent.current_city and self.parent.prayer_data and self.parent.current_city in self.parent.prayer_data:
            lat = self.parent.prayer_data[self.parent.current_city]['latitude']
            lon = self.parent.prayer_data[self.parent.current_city]['longitude']
            self.qibla_widget.update_qibla(lat, lon, city_name, country_name)

        
    
    def setup_location_settings(self, parent):
        """إعداد إعدادات الموقع"""
        # التأكد من تحميل البلدان في النافذة الرئيسية
        if not hasattr(self.parent, 'countries') or not self.parent.countries:
            from data_manager import get_countries
            self.parent.countries = get_countries()
            
        location_frame = ttk.LabelFrame(parent, text=self._("location_settings_title"))
        location_frame.pack(fill='x', padx=10, pady=10)

        country_label = ttk.Label(location_frame, text=self._("country"))
        country_label.pack(anchor='w', padx=10, pady=(5,0))

        self.country_frame = tk.Frame(location_frame)
        self.country_frame.pack(fill='x', padx=10, pady=(0,5))

        # إنشاء إدخال يمكن الوصول إليه مع دور ARIA المناسب
        # إنشاء إدخال البلد مع إمكانية الوصول المناسبة
        self.country_entry = ttk.Entry(
            self.country_frame,
            font=('Segoe UI', 12),
            name='country_entry'  # تعيين الاسم في وقت الإنشاء
        )
        self.country_entry.pack(side='left', fill='x', expand=True)
        
        # إضافة روابط الأحداث لإمكانية الوصول
        self.country_entry.bind('<KeyRelease>', self.on_country_entry_key_release)
        self.country_entry.bind('<Down>', self.show_country_dropdown)
        self.country_entry.bind('<Escape>', self.close_country_dropdown)
        self.country_entry.bind('<Tab>', lambda e: self.close_country_dropdown())
        self.country_entry.bind('<KeyPress-Up>', self.on_arrow_press)
        self.country_entry.bind('<KeyPress-Down>', self.on_arrow_press)
        self.country_entry.bind('<KeyRelease-Up>', self.on_arrow_release)
        self.country_entry.bind('<KeyRelease-Down>', self.on_arrow_release)
        
        # تعيين تلميح / وصف إمكانية الوصول
        tooltip_text = "اكتب للبحث عن البلد أو استخدم مفاتيح الأسهم للتنقل" if self.settings.language == 'ar' else "Type to search country or use arrow keys to navigate"
        self.set_tooltip(self.country_entry, tooltip_text)

        self.country_button = ttk.Button(self.country_frame, text='▼', width=3, command=self.toggle_country_list)
        self.country_button.pack(side='right')

        city_label = ttk.Label(location_frame, text=self._("city"))
        city_label.pack(anchor='w', padx=10, pady=(5,0))

        self.city_frame = tk.Frame(location_frame)
        self.city_frame.pack(fill='x', padx=10, pady=(0,10))

        # إنشاء إدخال المدينة مع إمكانية الوصول المناسبة
        self.city_entry = ttk.Entry(
            self.city_frame,
            font=('Segoe UI', 12),
            name='city_entry'  # تعيين الاسم في وقت الإنشاء
        )
        self.city_entry.pack(side='left', fill='x', expand=True)
        
        # إضافة روابط الأحداث لإمكانية الوصول
        self.city_entry.bind('<KeyRelease>', self.on_city_entry_key_release)
        self.city_entry.bind('<Down>', self.show_city_dropdown)
        self.city_entry.bind('<Escape>', self.close_city_dropdown)
        self.city_entry.bind('<KeyPress-Up>', self.on_arrow_press)
        self.city_entry.bind('<KeyPress-Down>', self.on_arrow_press)
        self.city_entry.bind('<KeyRelease-Up>', self.on_arrow_release)
        self.city_entry.bind('<KeyRelease-Down>', self.on_arrow_release)
        
        # تعيين تلميح / وصف إمكانية الوصول
        tooltip_text = "اكتب للبحث عن المدينة أو استخدم مفاتيح الأسهم للتنقل" if self.settings.language == 'ar' else "Type to search city or use arrow keys to navigate"
        self.set_tooltip(self.city_entry, tooltip_text)

        self.city_button = ttk.Button(self.city_frame, text='▼', width=3, command=self.toggle_city_list)
        self.city_button.pack(side='right')

        self.populate_countries_combobox()



    def on_combobox_key_release(self, event, combobox, values):
        """معالجة التنقل السريع عند كتابة النص"""
        # تجاهل المفاتيح الخاصة
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape', 'Left', 'Right'):
            return

        combobox = event.widget
        typed_text = combobox.get()
        
        # الحصول على القائمة الكاملة حسب نوع الحقل
        if combobox == self.country_combobox and hasattr(self, 'all_countries'):
            all_values = self.all_countries
        elif combobox == self.city_combobox and hasattr(self, 'all_cities'):
            all_values = self.all_cities
        else:
            return
        
        if not typed_text:
            # إذا كان الحقل فارغاً، أظهر كل القيم
            combobox['values'] = all_values
            return
            
        # تصفية القيم بناء على النص المكتوب
        filtered = []
        typed_lower = typed_text.lower()
        
        # أولاً: العناصر التي تبدأ بالنص المكتوب
        starts_with = [v for v in all_values if v.lower().startswith(typed_lower)]
        # ثانياً: العناصر التي تحتوي على النص (إن لم توجد عناصر تبدأ به)
        contains = [v for v in all_values if typed_lower in v.lower() and v not in starts_with]
        
        filtered = starts_with + contains
        
        # تحديث قائمة القيم
        if filtered:
            combobox['values'] = filtered
        else:
            combobox['values'] = all_values

        # فتح القائمة المنسدلة عند كتابة أول حرف
        if len(typed_text) == 1:  # عند كتابة أول حرف فقط
            try:
                combobox.event_generate('<Down>')
                # إعادة تعيين النص ووضع المؤشر في النهاية للسماح بكتابة المزيد
                combobox.set(typed_text)
                combobox.icursor(len(typed_text))
                combobox.selection_clear()
                combobox.focus_force()
            except:
                pass

    def on_arrow_press(self, event):
        """يتعامل مع التمرير المستمر عند الضغط على مفتاح الأسهم"""
        if hasattr(self, 'scroll_job') and self.scroll_job:
            self.dialog.after_cancel(self.scroll_job)

        direction = 1 if event.keysym == 'Down' else -1

        if event.widget == self.country_entry:
            if not (self.country_dropdown and self.country_dropdown.winfo_ismapped()):
                self.show_country_dropdown()
                return  # لا تقم بالتمرير عند الضغط لأول مرة، فقط افتح وحدد الأول
            listbox = self.country_listbox
        elif event.widget == self.city_entry:
            if not (self.city_dropdown and self.city_dropdown.winfo_ismapped()):
                self.show_city_dropdown()
                return  # لا تقم بالتمرير عند الضغط لأول مرة، فقط افتح وحدد الأول
            listbox = self.city_listbox
        else:
            return

        self.perform_scroll_for_listbox(listbox, direction)

    def on_arrow_release(self, event):
        """إيقاف التمرير المستمر عند إطلاق مفتاح الأسهم"""
        if self.scroll_job:
            self.dialog.after_cancel(self.scroll_job)
            self.scroll_job = None

    def perform_scroll_for_listbox(self, listbox, direction):
        """تنفيذ خطوة تمرير واحدة"""
        if not listbox or not listbox.winfo_ismapped():
            return

        selection_indices = listbox.curselection()
        current_index = -1
        if selection_indices:
            current_index = selection_indices[0]

        new_index = current_index + direction

        if 0 <= new_index < listbox.size():
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(new_index)
            listbox.see(new_index)

    def populate_countries_combobox(self):
        """تعبئة قائمة البلدان في الكومبوبوكس"""
        if not self.parent.countries:
            return

        if self.settings.language == 'ar':
            display_names = [arabic_name for _, arabic_name in self.parent.countries]
        else:
            display_names = [english_name for english_name, _ in self.parent.countries]

        self.all_countries = display_names[:]

        saved_english_country = self.settings.selected_country

        country_found = False
        for eng, ara in self.parent.countries:
            if eng == saved_english_country:
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.country_entry.delete(0, tk.END)
                self.country_entry.insert(0, display_name_to_set)
                self.update_cities_for_country(eng)
                country_found = True
                break

        if not country_found and self.parent.countries:
            eng, ara = self.parent.countries[0]
            display_name_to_set = ara if self.settings.language == 'ar' else eng
            self.country_entry.delete(0, tk.END)
            self.country_entry.insert(0, display_name_to_set)
            self.update_cities_for_country(eng)

    def update_cities_for_country(self, country_name: str):
        """تحديث قائمة المدن بناءً على البلد المختار"""
        if self.loading:
            return
            
        self.loading = True
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, self._("searching"))
        self.city_entry.config(state="disabled")
        self.city_button.config(state="disabled")
        
        def enable_city_controls():
            if self.dialog.winfo_exists():
                self.city_entry.config(state="normal")
                self.city_button.config(state="normal")
                self.city_entry.delete(0, tk.END)
                self.loading = False
                self.populate_cities_combobox()
        
        def handle_error(error):
            if self.dialog.winfo_exists():
                messagebox.showerror(
                    self._("Error"),
                    self._("Failed to fetch cities: {}").format(str(error))
                )
            enable_city_controls()
        
        def task():
            try:
                self.cities = get_cities(country_name)
                if self.dialog.winfo_exists():
                    self.dialog.after(0, enable_city_controls)
            except Exception as e:
                if self.dialog.winfo_exists():
                    self.dialog.after(0, lambda: handle_error(e))
        
        self.parent.executor.submit(task)

    def populate_cities_combobox(self):
        """ملء قائمة المدن بالأسماء العربية"""
        if self.settings.language == 'ar':
            display_names = [arabic_name for _, arabic_name in self.cities]
        else:
            display_names = [english_name for english_name, _ in self.cities]

        self.all_cities = display_names[:]

        saved_english_city = self.settings.selected_city
        city_found = False
        for eng, ara in self.cities:
            if eng == saved_english_city:
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, display_name_to_set)
                city_found = True
                break

        if not city_found:
            if self.cities:
                eng, ara = self.cities[0]
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, display_name_to_set)
            else:
                self.city_entry.delete(0, tk.END)
                self.city_entry.insert(0, self._("no_cities"))

        # تحديث القائمة المنسدلة إذا كانت مفتوحة
        if self.city_dropdown and self.city_dropdown.winfo_ismapped():
            self.city_listbox.delete(0, tk.END)
            for item in self.all_cities:
                self.city_listbox.insert(tk.END, item)
            if self.all_cities:
                self.city_listbox.selection_set(0)
                self.city_listbox.see(0)

    def navigate_dropdown(self, direction):
        """التنقل في القائمة المنسدلة باستخدام مفاتيح الأسهم"""
        current_dropdown = getattr(self, 'current_dropdown', None)
        if not current_dropdown:
            # إذا لم تكن هناك قائمة منسدلة مفتوحة، افتحها
            if self.country_entry == self.dialog.focus_get():
                self.show_dropdown('country')
            elif self.city_entry == self.dialog.focus_get():
                self.show_dropdown('city')
            return

        # الحصول على القائمة المنسدلة النشطة
        if current_dropdown == 'country':
            listbox = getattr(self, 'country_listbox', None)
        else:
            listbox = getattr(self, 'city_listbox', None)

        if not listbox or listbox.size() == 0:
            return

        # الحصول على العنصر المحدد حالياً
        selection = listbox.curselection()
        if not selection:
            new_index = 0 if direction == 'down' else listbox.size() - 1
        else:
            current_index = selection[0]
            if direction == 'down':
                new_index = min(current_index + 1, listbox.size() - 1)
            else:
                new_index = max(current_index - 1, 0)

        # تحديث التحديد ورؤية العنصر
        listbox.selection_clear(0, tk.END)
        listbox.selection_set(new_index)
        listbox.see(new_index)

        # تحديث النص في حقل الإدخال
        selected_text = listbox.get(new_index)
        if current_dropdown == 'country':
            self.country_entry.delete(0, tk.END)
            self.country_entry.insert(0, selected_text)
        else:
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, selected_text)

    def on_country_entry_key_release(self, event):
        """معالجة كتابة النص في حقل البلد"""
        if event.keysym == 'Tab':
            if self.country_dropdown and self.country_dropdown.winfo_ismapped():
                self.on_country_select()
            self.city_entry.focus_set()
            return "break"

        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            if event.keysym == 'Return':
                self.on_country_select()
            return

        typed_text = self.country_entry.get()
        if not typed_text:
            self.close_dropdown('country')
            return

        self.show_dropdown('country')
        
        typed_lower = typed_text.lower()
        
        starts_with = [v for v in self.all_countries if v.lower().startswith(typed_lower)]
        contains = [v for v in self.all_countries if typed_lower in v.lower() and v not in starts_with]
        filtered = starts_with + contains

        self.country_listbox.delete(0, tk.END)
        if filtered:
            for item in filtered:
                self.country_listbox.insert(tk.END, item)
            self.country_listbox.selection_set(0)
        else:
            self.close_dropdown('country')

    def on_city_entry_key_release(self, event):
        """معالجة كتابة النص في حقل المدينة"""
        if event.keysym == 'Tab':
            if self.city_dropdown and self.city_dropdown.winfo_ismapped():
                self.on_city_select()
            # يمكنك نقل التركيز إلى عنصر واجهة المستخدم التالي هنا إذا لزم الأمر
            return "break"

        if event.keysym in ('Up', 'Down', 'Return', 'Escape'):
            if event.keysym == 'Return':
                self.on_city_select()
            return

        typed_text = self.city_entry.get()
        if not typed_text:
            self.close_dropdown('city')
            return

        self.show_dropdown('city')
        
        typed_lower = typed_text.lower()
        
        starts_with = [v for v in self.all_cities if v.lower().startswith(typed_lower)]
        contains = [v for v in self.all_cities if typed_lower in v.lower() and v not in starts_with]
        filtered = starts_with + contains

        self.city_listbox.delete(0, tk.END)
        if filtered:
            for item in filtered:
                self.city_listbox.insert(tk.END, item)
            self.city_listbox.selection_set(0)
        else:
            self.close_dropdown('city')

    def toggle_country_list(self):
        """تبديل عرض قائمة البلدان"""
        if self.country_dropdown and self.country_dropdown.winfo_ismapped():
            self.close_dropdown('country')
        else:
            self.show_dropdown('country')
            x = self.country_frame.winfo_rootx()
            y = self.country_frame.winfo_rooty() + self.country_frame.winfo_height()
            # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
            self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
            self.country_frame.update_idletasks()
            frame_width = self.country_frame.winfo_width()
            if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                frame_width = 300
            frame_width += 20  # إضافة مساحة لشريط التمرير
            height = min(200, self.country_listbox.size() * 20 + 10)  # تعديل الارتفاع حسب عدد العناصر
            self.country_dropdown.geometry(f"{frame_width}x{height}+{x}+{y}")
            self.country_dropdown.lift()
            self.country_dropdown.deiconify()
            self.current_dropdown = 'country'
            self.close_bind_id = self.dialog.bind_all('<Button-1>', self.check_close_dropdown)

    def on_country_select(self, event=None):
        """معالجة اختيار بلد من القائمة"""
        selection = self.country_listbox.curselection()
        if selection:
            selected = self.country_listbox.get(selection[0])
            self.country_entry.delete(0, tk.END)
            self.country_entry.insert(0, selected)
            if self.country_dropdown:
                self.country_dropdown.withdraw()
            self.current_dropdown = None
            if hasattr(self, 'close_bind_id'):
                try:
                    self.dialog.unbind('<Button-1>', self.close_bind_id)
                except:
                    pass
            # تحديث المدن
            english_country = ""
            for eng, ara in self.parent.countries:
                if ara == selected or eng == selected:
                    english_country = eng
                    break
            if english_country:
                self.city_entry.delete(0, tk.END)
                self.update_cities_for_country(english_country)

    def toggle_city_list(self):
        """تبديل عرض قائمة المدن"""
        if self.city_dropdown and self.city_dropdown.winfo_ismapped():
            self.close_dropdown('city')
        else:
            self.show_dropdown('city')
            x = self.city_frame.winfo_rootx()
            y = self.city_frame.winfo_rooty() + self.city_frame.winfo_height()
            # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
            self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
            self.city_frame.update_idletasks()
            frame_width = self.city_frame.winfo_width()
            if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                frame_width = 300
            frame_width += 20  # إضافة مساحة لشريط التمرير
            height = min(200, self.city_listbox.size() * 20 + 10)  # تعديل الارتفاع حسب عدد العناصر
            self.city_dropdown.geometry(f"{frame_width}x{height}+{x}+{y}")
            self.city_dropdown.lift()
            self.city_dropdown.deiconify()
            self.current_dropdown = 'city'
            self.close_bind_id = self.dialog.bind_all('<Button-1>', self.check_close_dropdown)

    def on_city_select(self, event=None):
        """معالجة اختيار مدينة من القائمة"""
        selection = self.city_listbox.curselection()
        if selection:
            selected = self.city_listbox.get(selection[0])
            self.city_entry.delete(0, tk.END)
            self.city_entry.insert(0, selected)
            if self.city_dropdown:
                self.city_dropdown.withdraw()
            self.current_dropdown = None
            if hasattr(self, 'close_bind_id'):
                try:
                    self.dialog.unbind('<Button-1>', self.close_bind_id)
                except:
                    pass

    def check_close_dropdown(self, event):
        """تحقق مما إذا كان النقر خارج القائمة المنسدلة وأغلقها"""
        if not self.current_dropdown:
            return
            
        dropdown = self.country_dropdown if self.current_dropdown == 'country' else self.city_dropdown
        if not (dropdown and dropdown.winfo_exists() and dropdown.winfo_ismapped()):
            return
            
        # تحقق مما إذا كان النقر داخل منطقة الإدخال أو الزر
        entry = self.country_entry if self.current_dropdown == 'country' else self.city_entry
        button = self.country_button if self.current_dropdown == 'country' else self.city_button
        
        widget_under_mouse = event.widget
        if widget_under_mouse in (entry, button):
            return
            
        # تحقق مما إذا كان النقر داخل منطقة القائمة المنسدلة
        x, y = event.x_root, event.y_root
        dx, dy = dropdown.winfo_rootx(), dropdown.winfo_rooty()
        dw, dh = dropdown.winfo_width(), dropdown.winfo_height()
        
        if not (dx <= x <= dx + dw and dy <= y <= dy + dh):
            # إغلاق القائمة المنسدلة وتنظيف الارتباطات
            dropdown.withdraw()
            dropdown.unbind('<FocusOut>')
            dropdown.unbind('<Escape>')
            self.current_dropdown = None
            
            if hasattr(self, 'close_bind_id'):
                try:
                    self.dialog.unbind('<Button-1>', self.close_bind_id)
                except Exception as e:
                    # تسجيل الخطأ ولكن لا تنهار
                    print(f"Error unbinding event: {e}")
                    
            # إعادة التركيز إلى الإدخال
            entry.focus_set()

    def browse_adhan_sound_file(self):
        """تصفح واختيار ملف صوتي للأذان"""
        file_types = [
            (self._("audio_files"), "*.mp3 *.wav *.ogg *.wma *.aac *.flac *.m4a *.mp4 *.opus *.aiff *.amr *.au *.caf *.dts *.mka *.mp2 *.mpga *.oga *.spx *.tta *.wv"),
            ("MP3", "*.mp3"),
            ("WAV", "*.wav"),
            ("OGG", "*.ogg"),
            ("WMA", "*.wma"),
            ("AAC", "*.aac"),
            ("FLAC", "*.flac"),
            ("M4A", "*.m4a"),
            ("MP4", "*.mp4"),
            ("OPUS", "*.opus"),
            ("AIFF", "*.aiff"),
            ("AMR", "*.amr"),
            ("AU", "*.au"),
            ("CAF", "*.caf"),
            ("DTS", "*.dts"),
            ("MKA", "*.mka"),
            ("MP2", "*.mp2"),
            ("MPGA", "*.mpga"),
            ("OGA", "*.oga"),
            ("SPX", "*.spx"),
            ("TTA", "*.tta"),
            ("WV", "*.wv"),
            (self._("all_files"), "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title=self._("select_adhan_file"),
            initialdir=get_working_path('sounds'),
            filetypes=file_types
        )
        
        if filename:
            self.adhan_sound_file_var.set(filename)

    def browse_notification_sound_file(self):
        """تصفح واختيار ملف صوتي للتنبيه"""
        file_types = [
            (self._("audio_files"), "*.mp3 *.wav *.ogg *.wma *.aac *.flac *.m4a *.mp4 *.opus *.aiff *.amr *.au *.caf *.dts *.mka *.mp2 *.mpga *.oga *.spx *.tta *.wv"),
            ("MP3", "*.mp3"),
            ("WAV", "*.wav"),
            ("OGG", "*.ogg"),
            ("WMA", "*.wma"),
            ("AAC", "*.aac"),
            ("FLAC", "*.flac"),
            ("M4A", "*.m4a"),
            ("MP4", "*.mp4"),
            ("OPUS", "*.opus"),
            ("AIFF", "*.aiff"),
            ("AMR", "*.amr"),
            ("AU", "*.au"),
            ("CAF", "*.caf"),
            ("DTS", "*.dts"),
            ("MKA", "*.mka"),
            ("MP2", "*.mp2"),
            ("MPGA", "*.mpga"),
            ("OGA", "*.oga"),
            ("SPX", "*.spx"),
            ("TTA", "*.tta"),
            ("WV", "*.wv"),
            (self._("all_files"), "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title=self._("select_notification_file"),
            initialdir=get_working_path('sounds'),
            filetypes=file_types
        )
        
        if filename:
            self.notification_sound_file_var.set(filename)

    def toggle_sound(self, sound_type):
        if self.playing_sound:
            self.sound_player.stop_sound()
            if self.playing_sound == 'adhan':
                self.play_adhan_button.config(text=self._("play"))
            else:
                self.play_notification_button.config(text=self._("play"))
            self.playing_sound = None
            return

        if sound_type == 'adhan':
            sound_file = self.adhan_sound_file_var.get()
            button = self.play_adhan_button
        else:
            sound_file = self.notification_sound_file_var.get()
            button = self.play_notification_button

        if sound_file:
            self.sound_player.play_sound(sound_file, self.volume_var.get())
            button.config(text=self._("stop"))
            self.playing_sound = sound_type
        else:
            messagebox.showwarning(self._("error"), self._("no_sound_file_selected"))

    def save_settings(self):
        """حفظ الإعدادات"""
        self.sound_player.stop_sound()
        # طريقة الحساب باستخدام اللغة الحالية
        method_key = self.calc_method_var.get()
        if self.settings.language == 'ar':
            self.settings.calculation_method = CALCULATION_METHODS.get(method_key, self.settings.calculation_method)
        else:
            self.settings.calculation_method = CALCULATION_METHODS_EN.get(method_key, self.settings.calculation_method)

        self.settings.language = self.lang_var.get()
        self.settings.notifications_enabled = self.notifications_var.get()
        self.settings.sound_enabled = self.sound_var.get()
        
        self.settings.theme = self.theme_var.get()
        self.settings.notification_before_minutes = self.notify_before_var.get()
        self.settings.auto_update_interval = self.update_interval_var.get()
        self.settings.sound_volume = self.volume_var.get()
        self.settings.adhan_sound_file = self.adhan_sound_file_var.get()
        self.settings.notification_sound_file = self.notification_sound_file_var.get()

        # حفظ إعدادات الأذان لكل صلاة
        self.settings.adhan_fajr_enabled = self.fajr_adhan_var.get()
        self.settings.adhan_dhuhr_enabled = self.dhuhr_adhan_var.get()
        self.settings.adhan_asr_enabled = self.asr_adhan_var.get()
        self.settings.adhan_maghrib_enabled = self.maghrib_adhan_var.get()
        self.settings.adhan_isha_enabled = self.isha_adhan_var.get()


        
        selected_display_country = self.country_entry.get()
        english_country = ""
        for eng, ara in self.parent.countries:
            if ara == selected_display_country or eng == selected_display_country:
                english_country = eng
                break
        if english_country:
            self.settings.selected_country = english_country
        # حفظ المدينة المختارة
        selected_display_city = self.city_entry.get()
        english_city = ""
        if hasattr(self, 'cities') and self.cities:
            for eng, ara in self.cities:
                if ara == selected_display_city or eng == selected_display_city:
                    english_city = eng
                    break
        if english_city:
            self.settings.selected_city = english_city
        
        self.settings.save_settings()
        self.dialog.destroy()
        
        self.show_restart_dialog()
    
    def _perform_restart(self, dialog):
        """
        تنفيذ إعادة تشغيل التطبيق باستخدام restart.py للاستقرار
        """
        import sys
        import os
        import subprocess
        import logging
        import traceback

        logger = logging.getLogger(__name__)
        logger.info("بدء عملية إعادة تشغيل التطبيق باستخدام restart.py...")

        try:
            # لا نحتاج لتنظيف المجلدات المؤقتة هنا - سيتم ذلك في restart.py بعد خروج التطبيق
            logger.info("بدء عملية إعادة التشغيل...")

            # احصل على PID الحالي ومسار التنفيذ
            parent_pid = os.getpid()

            # تحديد المسار الصحيح للتطبيق
            if getattr(sys, 'frozen', False):
                # للملفات التنفيذية المجمدة (exe)
                app_path = sys.executable
                logger.info(f"مسار الملف التنفيذي المجمد: {app_path}")
            else:
                # للبرامج النصية العادية
                app_path = os.path.abspath(sys.argv[0])
                logger.info(f"مسار البرنامج النصي: {app_path}")

            # مسار restart.py
            restart_script = os.path.join(os.path.dirname(app_path), 'restart.py')
            logger.info(f"مسار برنامج إعادة التشغيل: {restart_script}")

            # تشغيل restart.py في خلفية منفصلة
            logger.info(f"تشغيل برنامج إعادة التشغيل: {sys.executable} {restart_script} {app_path} {parent_pid}")

            if sys.platform == "win32":
                # في Windows، استخدام أعلام خاصة
                CREATE_NO_WINDOW = 0x08000000
                subprocess.Popen([sys.executable, restart_script, app_path, str(parent_pid)],
                                creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.Popen([sys.executable, restart_script, app_path, str(parent_pid)])

            logger.info("تم تشغيل برنامج إعادة التشغيل بنجاح، إغلاق التطبيق الحالي...")

            dialog.destroy()

            # إغلاق التطبيق الحالي
            self.parent.quit_application()

        except Exception as e:
            error_msg = f"خطأ في إعادة تشغيل التطبيق: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            dialog.destroy()
            try:
                messagebox.showerror(self._("error"), f"{self._('restart_error')}: {str(e)}", parent=self.parent.root)
            except Exception as tk_error:
                logger.error(f"Failed to show error dialog: {tk_error}")
                print(f"Restart error: {str(e)}")

    # عرض مربع حوار لإعادة التشغيل
    def show_restart_dialog(self):
        dialog = tk.Toplevel(self.parent.root)
        dialog.title(self._("restart_required"))
        try:
            dialog.iconbitmap(get_working_path("pray_times.ico"))
        except tk.TclError:
            pass

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        dialog.resizable(False, False)
        dialog.transient(self.parent.root)
        dialog.grab_set()

        label = ttk.Label(dialog, text=self._("settings_saved_successfully_restart"), wraplength=380, justify='center')
        label.pack(pady=20, expand=True)

        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=10)

        def restart():
            self._perform_restart(dialog)

        def continue_later():
            dialog.destroy()

        restart_button = ttk.Button(buttons_frame, text=self._("restart_now"), command=restart)
        restart_button.pack(side='left', padx=10)

        continue_button = ttk.Button(buttons_frame, text=self._("continue_later"), command=continue_later)
        continue_button.pack(side='right', padx=10)

        if self.on_save_callback:
            self.on_save_callback()

    def show_force_restart_dialog(self):
        dialog = tk.Toplevel(self.parent.root)
        dialog.title(self._("restart_required"))
        try:
            dialog.iconbitmap(get_working_path("pray_times.ico"))
        except tk.TclError:
            pass

        dialog.update_idletasks()
        width = 400
        height = 150
        x = (dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (dialog.winfo_screenheight() // 2) - (height // 2)
        dialog.geometry(f'{width}x{height}+{x}+{y}')

        dialog.resizable(False, False)
        dialog.transient(self.parent.root)
        dialog.grab_set()

        label = ttk.Label(dialog, text=self._("settings_saved_successfully_restart"), wraplength=380, justify='center')
        label.pack(pady=20, expand=True)

        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=10)

        def restart():
            self._perform_restart(dialog)

        restart_button = ttk.Button(buttons_frame, text=self._("restart_now"), command=restart)
        restart_button.pack(padx=10)

        if self.on_save_callback:
            self.on_save_callback()
            
    def reset_settings(self):
        """استعادة الإعدادات الافتراضية"""
        # حفظ اللغة الحالية
        lang = self.settings.language
        self.settings = Settings()
        self.settings.language = lang
        self.settings.save_settings()
        self.dialog.destroy()
        self.show_force_restart_dialog()