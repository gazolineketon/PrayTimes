# -*- coding: utf-8 -*-

"""
ui_components.py
SettingsDialog يحتوي هذا الملف على أجزاء الواجهة الرسومية القابلة لإعادة الاستخدام مثل
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import ImageTk, Image
from config import CALCULATION_METHODS, CALCULATION_METHODS_REV
from data_manager import get_cities
from settings_manager import Settings
from qibla_ui import QiblaWidget
from media_manager import AdhanPlayer

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
        self.sound_player = AdhanPlayer()
        self.playing_sound = None
        self.create_dialog()
    
    def create_dialog(self):
        """إنشاء نافذة الإعدادات"""
        self.dialog = tk.Toplevel(self.parent.root)
        self.dialog.title(self._("app_settings"))
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent.root)
        self.dialog.grab_set()
        
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
        self.dialog.geometry(f"500x600+{x}+{y}")
        
        self.setup_settings_ui()
    
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
        try:
            img = Image.open("pray_logo.png")
            img = img.resize((128, 128), Image.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(img)
            
            logo_label = tk.Label(logo_frame, image=self.logo_img, bg=self.colors.get('bg_secondary', '#FFFFFF'))
            logo_label.pack(pady=(20, 10))
        except FileNotFoundError:
            tk.Label(logo_frame, text=self._("logo_not_found"), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_primary', '#000000')).pack(pady=(20, 10))

        # عرض معلومات البرنامج
        info_frame = tk.Frame(main_frame, bg=self.colors.get('bg_secondary', '#FFFFFF'))
        info_frame.grid(row=1, column=0, sticky='n')

        tk.Label(info_frame, text="برنامج مواقيت الصلاة", font=("Segoe UI", 16, "bold"), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_primary', '#000000')).pack()
        tk.Label(info_frame, text="مجانى لوجة الله تعالى", font=("Segoe UI", 12), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack()
        tk.Label(info_frame, text=f'الإصدار : {self.parent.version}', font=("Segoe UI", 10), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack()
        tk.Label(info_frame, text="برمجة : محمود نصار", font=("Segoe UI", 10), bg=self.colors.get('bg_secondary', '#FFFFFF'), fg=self.colors.get('text_secondary', '#000000')).pack(pady=(10, 0))

    
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

        lang_combo.bind('<<ComboboxSelected>>', on_lang_selected)

        # طريقة الحساب
        calc_frame = ttk.LabelFrame(parent, text=self._("prayer_calculation_method"))
        calc_frame.pack(fill='x', padx=10, pady=10)
        
        self.calc_method_var = tk.StringVar(value=CALCULATION_METHODS_REV.get(self.settings.calculation_method, "الهيئة المصرية العامة للمساحة"))
        calc_combo = ttk.Combobox(calc_frame, textvariable=self.calc_method_var, 
                                 values=list(CALCULATION_METHODS.keys()),
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
        location_frame = ttk.LabelFrame(parent, text=self._("location_settings_title"))
        location_frame.pack(fill='x', padx=10, pady=10)

        country_label = ttk.Label(location_frame, text=self._("country"))
        country_label.pack(anchor='w', padx=10, pady=(5,0))
        
        self.country_var = tk.StringVar()
        self.country_combobox = ttk.Combobox(location_frame, textvariable=self.country_var, font=('Segoe UI', 12), state='readonly')
        self.country_combobox.pack(fill='x', padx=10, pady=(0,10))
        self.country_combobox.bind('<<ComboboxSelected>>', self.on_country_selected)

        city_label = ttk.Label(location_frame, text=self._("city"))
        city_label.pack(anchor='w', padx=10, pady=(5,0))

        self.city_var = tk.StringVar()
        self.city_combobox = ttk.Combobox(location_frame, textvariable=self.city_var, font=('Segoe UI', 12), state='readonly')
        self.city_combobox.pack(fill='x', padx=10, pady=(0,10))

        self.populate_countries_combobox()

    def populate_countries_combobox(self):
        """ملء قائمة البلدان بالأسماء العربية"""
        if not self.parent.countries:
            return

        if self.settings.language == 'ar':
            display_names = [arabic_name for _, arabic_name in self.parent.countries]
        else:
            display_names = [english_name for english_name, _ in self.parent.countries]

        self.country_combobox['values'] = display_names
        
        saved_english_country = self.settings.selected_country
        
        country_found = False
        for eng, ara in self.parent.countries:
            if eng == saved_english_country:
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.country_var.set(display_name_to_set)
                self.update_cities_for_country(eng)
                country_found = True
                break
        
        if not country_found and self.parent.countries:
            eng, ara = self.parent.countries[0]
            display_name_to_set = ara if self.settings.language == 'ar' else eng
            self.country_var.set(display_name_to_set)
            self.update_cities_for_country(eng)

    def update_cities_for_country(self, country_name: str):
        """تحديث قائمة المدن بناءً على البلد المختار"""
        self.city_combobox['values'] = []
        self.city_var.set(self._("searching"))
        def task():
            self.cities = get_cities(country_name)
            if self.dialog.winfo_exists():
                self.dialog.after(0, self.populate_cities_combobox)

        self.parent.executor.submit(task)

    def populate_cities_combobox(self):
        """ملء قائمة المدن بالأسماء العربية"""
        if self.settings.language == 'ar':
            display_names = [arabic_name for _, arabic_name in self.cities]
        else:
            display_names = [english_name for english_name, _ in self.cities]

        self.city_combobox['values'] = display_names
        
        saved_english_city = self.settings.selected_city
        city_found = False
        for eng, ara in self.cities:
            if eng == saved_english_city:
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.city_var.set(display_name_to_set)
                city_found = True
                break
        
        if not city_found:
            if self.cities:
                eng, ara = self.cities[0]
                display_name_to_set = ara if self.settings.language == 'ar' else eng
                self.city_var.set(display_name_to_set)
            else:
                self.city_var.set(self._("no_cities"))

    def on_country_selected(self, event=None):
        """معالجة اختيار بلد جديد"""
        selected_display_country = self.country_var.get()
        
        english_country = ""
        for eng, ara in self.parent.countries:
            if ara == selected_display_country or eng == selected_display_country:
                english_country = eng
                break
    
        if english_country:
            self.update_cities_for_country(english_country)

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
            initialdir="C:/Windows/Media",
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
        self.settings.language = self.lang_var.get()
        self.settings.notifications_enabled = self.notifications_var.get()
        self.settings.sound_enabled = self.sound_var.get()
        self.settings.calculation_method = CALCULATION_METHODS[self.calc_method_var.get()]
        self.settings.theme = self.theme_var.get()
        self.settings.notification_before_minutes = self.notify_before_var.get()
        self.settings.auto_update_interval = self.update_interval_var.get()
        self.settings.sound_volume = self.volume_var.get()
        self.settings.adhan_sound_file = self.adhan_sound_file_var.get()
        self.settings.notification_sound_file = self.notification_sound_file_var.get()
        
        selected_display_country = self.country_var.get()
        english_country = ""
        for eng, ara in self.parent.countries:
            if ara == selected_display_country or eng == selected_display_country:
                english_country = eng
                break
        if english_country:
            self.settings.selected_country = english_country
        # حفظ المدينة المختارة
        selected_display_city = self.city_var.get()
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
    
    # عرض مربع حوار لإعادة التشغيل
    def show_restart_dialog(self):
        dialog = tk.Toplevel(self.parent.root)
        dialog.title(self._("restart_required"))
        
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
        label.pack(pady=20, fill='x', expand=True)

        buttons_frame = tk.Frame(dialog)
        buttons_frame.pack(pady=10)

        # إعادة تشغيل التطبيق
        def restart():
            import sys
            import os
            import subprocess

            dialog.destroy()
            
            main_py_path = os.path.abspath(sys.argv[0])
            restart_py_path = os.path.join(os.path.dirname(main_py_path), "restart.py")

            subprocess.Popen([sys.executable, restart_py_path, main_py_path])

            self.parent.on_closing()

        def continue_later():
            dialog.destroy()

        restart_button = ttk.Button(buttons_frame, text=self._("restart_now"), command=restart)
        restart_button.pack(side='left', padx=10)

        continue_button = ttk.Button(buttons_frame, text=self._("continue_later"), command=continue_later)
        continue_button.pack(side='right', padx=10)

        if self.on_save_callback:
            self.on_save_callback()
    
    def reset_settings(self):
        """استعادة الإعدادات الافتراضية"""
        if messagebox.askyesno(self._("confirm"), self._("confirm_restore_defaults")):
            # حفظ اللغة الحالية
            lang = self.settings.language
            self.settings = Settings()
            self.settings.language = lang
            self.settings.save_settings()
            self.dialog.destroy()
            messagebox.showinfo(self._("saved_successfully"), self._("settings_saved_successfully"))
