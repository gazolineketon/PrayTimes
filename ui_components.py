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
        self.current_dropdown = None
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

        self.country_frame = tk.Frame(location_frame)
        self.country_frame.pack(fill='x', padx=10, pady=(0,5))

        self.country_entry = ttk.Entry(self.country_frame, font=('Segoe UI', 12))
        self.country_entry.pack(side='left', fill='x', expand=True)
        self.country_entry.bind('<KeyRelease>', self.on_country_entry_key_release)

        self.country_button = ttk.Button(self.country_frame, text='▼', width=3, command=self.toggle_country_list)
        self.country_button.pack(side='right')

        city_label = ttk.Label(location_frame, text=self._("city"))
        city_label.pack(anchor='w', padx=10, pady=(5,0))

        self.city_frame = tk.Frame(location_frame)
        self.city_frame.pack(fill='x', padx=10, pady=(0,10))

        self.city_entry = ttk.Entry(self.city_frame, font=('Segoe UI', 12))
        self.city_entry.pack(side='left', fill='x', expand=True)
        self.city_entry.bind('<KeyRelease>', self.on_city_entry_key_release)

        self.city_button = ttk.Button(self.city_frame, text='▼', width=3, command=self.toggle_city_list)
        self.city_button.pack(side='right')

        self.populate_countries_combobox()



    def on_combobox_key_release(self, event):
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

    def populate_countries_combobox(self):
        """ملء قائمة البلدان بالأسماء العربية"""
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
        self.city_entry.delete(0, tk.END)
        self.city_entry.insert(0, self._("searching"))
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

    def on_country_entry_key_release(self, event):
        """معالجة كتابة النص في حقل البلد"""
        # تجاهل المفاتيح الخاصة للتنقل
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'):
            if self.country_dropdown and self.country_dropdown.winfo_ismapped():
                if event.keysym == 'Up':
                    selection = self.country_listbox.curselection()
                    if selection:
                        new_index = max(0, selection[0] - 1)
                    else:
                        new_index = 0
                    self.country_listbox.selection_clear(0, tk.END)
                    self.country_listbox.selection_set(new_index)
                    self.country_listbox.see(new_index)
                    return
                elif event.keysym == 'Down':
                    selection = self.country_listbox.curselection()
                    if selection:
                        new_index = min(self.country_listbox.size() - 1, selection[0] + 1)
                    else:
                        new_index = 0
                    self.country_listbox.selection_clear(0, tk.END)
                    self.country_listbox.selection_set(new_index)
                    self.country_listbox.see(new_index)
                    return
                elif event.keysym == 'Return':
                    self.on_country_select()
                    return
                elif event.keysym == 'Escape':
                    if self.country_dropdown:
                        self.country_dropdown.withdraw()
                    return
            else:
                # إذا لم تكن القائمة مفتوحة، تجاهل هذه المفاتيح
                return

        typed_text = self.country_entry.get()
        if typed_text:
            typed_lower = typed_text.lower()
            filtered = []
            starts_with = [v for v in self.all_countries if v.lower().startswith(typed_lower)]
            contains = [v for v in self.all_countries if typed_lower in v.lower() and v not in starts_with]
            filtered = starts_with + contains
            if filtered:
                if self.country_dropdown is None:
                    self.country_dropdown = tk.Toplevel(self.dialog)
                    self.country_dropdown.overrideredirect(True)
                    frame = tk.Frame(self.country_dropdown)
                    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
                    self.country_listbox = tk.Listbox(frame, font=('Segoe UI', 12), selectmode='single', yscrollcommand=scrollbar.set)
                    scrollbar.config(command=self.country_listbox.yview)
                    self.country_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    frame.pack(fill=tk.BOTH, expand=True)
                    self.country_listbox.bind('<Double-Button-1>', self.on_country_select)
                    self.country_listbox.bind('<Return>', self.on_country_select)
                self.country_listbox.delete(0, tk.END)
                for item in filtered[:10]:  # عرض أول 10 نتائج
                    self.country_listbox.insert(tk.END, item)
                x = self.country_frame.winfo_rootx()
                y = self.country_frame.winfo_rooty() + self.country_frame.winfo_height()
                # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
                self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
                self.country_frame.update_idletasks()
                frame_width = self.country_frame.winfo_width()
                if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                    frame_width = 300
                frame_width += 20  # Add space for scrollbar
                height = min(200, self.country_listbox.size() * 20 + 10)  # تعديل الارتفاع حسب عدد العناصر
                self.country_dropdown.geometry(f"{frame_width}x{height}+{x}+{y}")
                self.country_dropdown.lift()
                self.country_dropdown.deiconify()
                self.current_dropdown = 'country'
                self.close_bind_id = self.dialog.bind_all('<Button-1>', self.check_close_dropdown)
                # الحفاظ على التركيز على الحقل للسماح بكتابة المزيد
                self.country_entry.focus_force()
                # تحديد العنصر الأول تلقائياً
                if self.country_listbox.size() > 0:
                    self.country_listbox.selection_set(0)
            else:
                if self.country_dropdown:
                    self.country_dropdown.withdraw()
        else:
            if self.country_dropdown:
                self.country_dropdown.withdraw()

    def toggle_country_list(self):
        """تبديل عرض قائمة البلدان"""
        if self.country_dropdown and self.country_dropdown.winfo_ismapped():
            self.country_dropdown.withdraw()
        else:
            if self.country_dropdown is None:
                self.country_dropdown = tk.Toplevel(self.dialog)
                self.country_dropdown.overrideredirect(True)
                frame = tk.Frame(self.country_dropdown)
                scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
                self.country_listbox = tk.Listbox(frame, font=('Segoe UI', 12), selectmode='single', yscrollcommand=scrollbar.set)
                scrollbar.config(command=self.country_listbox.yview)
                self.country_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                frame.pack(fill=tk.BOTH, expand=True)
                self.country_listbox.bind('<Double-Button-1>', self.on_country_select)
                self.country_listbox.bind('<Return>', self.on_country_select)
            self.country_listbox.delete(0, tk.END)
            for item in self.all_countries:
                self.country_listbox.insert(tk.END, item)
            x = self.country_frame.winfo_rootx()
            y = self.country_frame.winfo_rooty() + self.country_frame.winfo_height()
            # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
            self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
            self.country_frame.update_idletasks()
            frame_width = self.country_frame.winfo_width()
            if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                frame_width = 300
            frame_width += 20  # Add space for scrollbar
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
                self.update_cities_for_country(english_country)

    def on_city_entry_key_release(self, event):
        """معالجة كتابة النص في حقل المدينة"""
        # تجاهل المفاتيح الخاصة للتنقل
        if event.keysym in ('Up', 'Down', 'Return', 'Tab', 'Escape'):
            if self.city_dropdown and self.city_dropdown.winfo_ismapped():
                if event.keysym == 'Up':
                    selection = self.city_listbox.curselection()
                    if selection:
                        new_index = max(0, selection[0] - 1)
                    else:
                        new_index = 0
                    self.city_listbox.selection_clear(0, tk.END)
                    self.city_listbox.selection_set(new_index)
                    self.city_listbox.see(new_index)
                    return
                elif event.keysym == 'Down':
                    selection = self.city_listbox.curselection()
                    if selection:
                        new_index = min(self.city_listbox.size() - 1, selection[0] + 1)
                    else:
                        new_index = 0
                    self.city_listbox.selection_clear(0, tk.END)
                    self.city_listbox.selection_set(new_index)
                    self.city_listbox.see(new_index)
                    return
                elif event.keysym == 'Return':
                    self.on_city_select()
                    return
                elif event.keysym == 'Escape':
                    if self.city_dropdown:
                        self.city_dropdown.withdraw()
                    return
            else:
                # إذا لم تكن القائمة مفتوحة، تجاهل هذه المفاتيح
                return

        typed_text = self.city_entry.get()
        if typed_text:
            typed_lower = typed_text.lower()
            filtered = []
            starts_with = [v for v in self.all_cities if v.lower().startswith(typed_lower)]
            contains = [v for v in self.all_cities if typed_lower in v.lower() and v not in starts_with]
            filtered = starts_with + contains
            if filtered:
                if self.city_dropdown is None:
                    self.city_dropdown = tk.Toplevel(self.dialog)
                    self.city_dropdown.overrideredirect(True)
                    frame = tk.Frame(self.city_dropdown)
                    scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
                    self.city_listbox = tk.Listbox(frame, font=('Segoe UI', 12), selectmode='single', yscrollcommand=scrollbar.set)
                    scrollbar.config(command=self.city_listbox.yview)
                    self.city_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    frame.pack(fill=tk.BOTH, expand=True)
                    self.city_listbox.bind('<Double-Button-1>', self.on_city_select)
                    self.city_listbox.bind('<Return>', self.on_city_select)
                self.city_listbox.delete(0, tk.END)
                for item in filtered[:10]:  # عرض أول 10 نتائج
                    self.city_listbox.insert(tk.END, item)
                x = self.city_frame.winfo_rootx()
                y = self.city_frame.winfo_rooty() + self.city_frame.winfo_height()
                # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
                self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
                self.city_frame.update_idletasks()
                frame_width = self.city_frame.winfo_width()
                if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                    frame_width = 300
                frame_width += 20  # Add space for scrollbar
                height = min(200, self.city_listbox.size() * 20 + 10)  # تعديل الارتفاع حسب عدد العناصر
                self.city_dropdown.geometry(f"{frame_width}x{height}+{x}+{y}")
                self.city_dropdown.lift()
                self.city_dropdown.deiconify()
                self.current_dropdown = 'city'
                self.close_bind_id = self.dialog.bind_all('<Button-1>', self.check_close_dropdown)
                # الحفاظ على التركيز على الحقل للسماح بكتابة المزيد
                self.city_entry.focus_force()
                # تحديد العنصر الأول تلقائياً
                if self.city_listbox.size() > 0:
                    self.city_listbox.selection_set(0)
            else:
                if self.city_dropdown:
                    self.city_dropdown.withdraw()
        else:
            if self.city_dropdown:
                self.city_dropdown.withdraw()

    def toggle_city_list(self):
        """تبديل عرض قائمة المدن"""
        if self.city_dropdown and self.city_dropdown.winfo_ismapped():
            self.city_dropdown.withdraw()
        else:
            if self.city_dropdown is None:
                self.city_dropdown = tk.Toplevel(self.dialog)
                self.city_dropdown.overrideredirect(True)
                frame = tk.Frame(self.city_dropdown)
                scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
                self.city_listbox = tk.Listbox(frame, font=('Segoe UI', 12), selectmode='single', yscrollcommand=scrollbar.set)
                scrollbar.config(command=self.city_listbox.yview)
                self.city_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                frame.pack(fill=tk.BOTH, expand=True)
                self.city_listbox.bind('<Double-Button-1>', self.on_city_select)
                self.city_listbox.bind('<Return>', self.on_city_select)
            self.city_listbox.delete(0, tk.END)
            for item in self.all_cities:
                self.city_listbox.insert(tk.END, item)
            x = self.city_frame.winfo_rootx()
            y = self.city_frame.winfo_rooty() + self.city_frame.winfo_height()
            # جعل عرض القائمة مطابقاً لعرض حقل الإدخال
            self.dialog.update_idletasks()  # التأكد من تحديث الأبعاد
            self.city_frame.update_idletasks()
            frame_width = self.city_frame.winfo_width()
            if frame_width <= 0:  # في حالة عدم توفر العرض، استخدم عرض افتراضي
                frame_width = 300
            frame_width += 20  # Add space for scrollbar
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
        """Check if click is outside the dropdown and close it"""
        if self.current_dropdown == 'country' and self.country_dropdown and self.country_dropdown.winfo_exists() and self.country_dropdown.winfo_ismapped():
            x, y = event.x_root, event.y_root
            dx, dy = self.country_dropdown.winfo_rootx(), self.country_dropdown.winfo_rooty()
            dw, dh = self.country_dropdown.winfo_width(), self.country_dropdown.winfo_height()
            if not (dx <= x <= dx + dw and dy <= y <= dy + dh):
                self.country_dropdown.withdraw()
                self.current_dropdown = None
                self.dialog.unbind('<Button-1>', self.close_bind_id)
        elif self.current_dropdown == 'city' and self.city_dropdown and self.city_dropdown.winfo_exists() and self.city_dropdown.winfo_ismapped():
            x, y = event.x_root, event.y_root
            dx, dy = self.city_dropdown.winfo_rootx(), self.city_dropdown.winfo_rooty()
            dw, dh = self.city_dropdown.winfo_width(), self.city_dropdown.winfo_height()
            if not (dx <= x <= dx + dw and dy <= y <= dy + dh):
                self.city_dropdown.withdraw()
                self.current_dropdown = None
                self.dialog.unbind('<Button-1>', self.close_bind_id)

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