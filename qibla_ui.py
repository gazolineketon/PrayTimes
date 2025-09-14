# -*- coding: utf-8 -*-
"""
qibla_ui.py
يحتوي هذا الملف على واجهة عرض القبلة.
"""

import tkinter as tk
import math
import threading
import time
import requests
import logging
from prayer_logic import QiblaCalculator
from data_manager import get_coordinates_for_city

logger = logging.getLogger(__name__)

class QiblaWidget(tk.Frame):
    # تهيئة واجهة عرض القبلة
    def __init__(self, parent, settings, translator, colors, city, country):
        super().__init__(parent, bg=colors['bg_card'], relief='flat', bd=1, highlightbackground=colors['border'], highlightthickness=1)
        self.parent = parent
        self.settings = settings
        self.translator = translator
        self._ = self.translator.get
        self.colors = colors
        self.city = city
        self.country = country
        self.user_lat = 0.0
        self.user_lon = 0.0
        self.qibla_direction = 0.0
        self.current_heading = 0.0
        self.auto_update = tk.BooleanVar(value=False)
        self.compass_running = False
        if self.settings.qibla_enabled:
            self.setup_ui()
            self.fetch_and_update_coordinates()

    # جلب وتحديث الإحداثيات
    def fetch_and_update_coordinates(self):
        self.city_country_label.config(text=self._("loading_coordinates"))
        self.coordinates_label.config(text="")
        threading.Thread(target=self._get_and_set_coordinates, daemon=True).start()

    # الحصول على الإحداثيات وتحديثها
    def _get_and_set_coordinates(self):
        coordinates = get_coordinates_for_city(self.city, self.country)
        if coordinates:
            lat, lon = coordinates
            if self.parent.winfo_exists():
                self.parent.after(0, self.update_qibla, lat, lon, self.city, self.country)
        else:
            if self.parent.winfo_exists():
                self.parent.after(0, self.show_coordinates_error)

    # عرض خطأ في حالة فشل تحميل الإحداثيات
    def show_coordinates_error(self):
        self.city_country_label.config(text=self._("failed_to_load_coordinates"))
        self.coordinates_label.config(text="")

    # إعداد واجهة المستخدم
    def setup_ui(self):
        container = tk.Frame(self, bg=self.colors['bg_card'], pady=5)
        container.pack(fill='x', expand=True)
        title_text = self._("qibla_direction")
        self.title_label = tk.Label(container, text=title_text, font=("Arial", 20, "bold"), fg="#16c79a", bg=self.colors['bg_card'])
        self.title_label.pack(pady=3)
        location_frame = tk.Frame(container, bg=self.colors['bg_card'])
        location_frame.pack(pady=3)
        self.city_country_label = tk.Label(location_frame, text="الرجاء تحديد الموقع من الإعدادات", font=("Arial", 16, "bold"), fg="#16c79a", bg=self.colors['bg_card'])
        self.city_country_label.pack()
        self.coordinates_label = tk.Label(location_frame, text="", font=("Arial", 8), fg="#000000", bg=self.colors['bg_card'])
        self.coordinates_label.pack()
        compass_frame = tk.Frame(container, bg=self.colors['bg_card'])
        compass_frame.pack(pady=5)
        self.canvas = tk.Canvas(compass_frame, width=300, height=300, bg="#0f0f23", highlightthickness=2, highlightcolor="#16c79a")
        self.canvas.pack()
        direction_frame = tk.Frame(container, bg=self.colors['bg_card'])
        direction_frame.pack(pady=5)
        self.direction_label = tk.Label(direction_frame, text="", font=("Arial", 14, "bold"), fg="#ffc107", bg=self.colors['bg_card'])
        self.direction_label.pack()
        self.direction_note = tk.Label(direction_frame, text="اضبط اتجاه السهم الأحمر نحو الشمال الجغرافي", font=("Arial", 10, "bold"), fg="#8B0D0D", bg=self.colors['bg_card'])
        self.direction_note.pack()

    
    # تحديث الموقع يدويًا
    def update_qibla(self, lat, lon, city, country):
        self.user_lat = lat
        self.user_lon = lon
        self.city = city
        self.country = country
        if hasattr(self, 'city_country_label'):
            self.city_country_label.config(text=f"{self.city} , {self.country}")
        if hasattr(self, 'coordinates_label'):
            self.coordinates_label.config(text=f"({self.user_lat:.4f}, {self.user_lon:.4f})")
        if hasattr(self, 'title_label'):
            title_text = self._("qibla_direction")
            self.title_label.config(text=title_text)
        self.calculate_qibla_direction()
        self.draw_compass()

    # حساب اتجاه القبلة
    def calculate_qibla_direction(self):
        self.qibla_direction = QiblaCalculator.calculate_qibla(self.user_lat, self.user_lon)
        self.direction_label.config(text=f"°{self.qibla_direction:.1f} {self._('qibla_angle_from_north')}")
        self.direction_note.config(text=self._('set_arrow_towards_north'))


    # رسم البوصلة
    def draw_compass(self):
        self.canvas.delete("all")
        center_x, center_y = 150, 150
        radius = 120
        self.canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline="#16c79a", width=3, fill="#0f0f23")
        directions = [(0, "N"), (90, "E"), (180, "S"), (270, "W")]
        for angle, letter in directions:
            x = center_x + (radius - 20) * math.sin(math.radians(angle))
            y = center_y - (radius - 20) * math.cos(math.radians(angle))
            self.canvas.create_text(x, y, text=letter, fill="#16c79a", font=("Arial", 10, "bold"), justify="center")
        for i in range(0, 360, 30):
            x1 = center_x + (radius - 10) * math.sin(math.radians(i))
            y1 = center_y - (radius - 10) * math.cos(math.radians(i))
            x2 = center_x + radius * math.sin(math.radians(i))
            y2 = center_y - radius * math.cos(math.radians(i))
            self.canvas.create_line(x1, y1, x2, y2, fill="#16c79a", width=2)
        if hasattr(self, 'qibla_direction'):
            self.draw_qibla_arrow(center_x, center_y, self.qibla_direction - self.current_heading)
        self.draw_north_arrow(center_x, center_y, -self.current_heading)

    # رسم سهم القبلة
    def draw_qibla_arrow(self, center_x, center_y, angle):
        length = 80
        angle_rad = math.radians(angle)
        end_x = center_x + length * math.sin(angle_rad)
        end_y = center_y - length * math.cos(angle_rad)
        self.canvas.create_line(center_x, center_y, end_x, end_y, fill="#ffc107", width=4, arrow=tk.LAST, arrowshape=(10, 12, 5))
        kaaba_x = center_x + (length + 15) * math.sin(angle_rad)
        kaaba_y = center_y - (length + 15) * math.cos(angle_rad)
        self.canvas.create_text(kaaba_x, kaaba_y, text="🕋", font=("Arial", 16), fill="#ffc107")

    # رسم سهم الشمال
    def draw_north_arrow(self, center_x, center_y, angle):
        length = 60
        angle_rad = math.radians(angle)
        end_x = center_x + length * math.sin(angle_rad)
        end_y = center_y - length * math.cos(angle_rad)
        self.canvas.create_line(center_x, center_y, end_x, end_y, fill="#dc3545", width=2, arrow=tk.LAST, arrowshape=(8, 10, 4))

    # تبديل التحديث التلقائي
    def toggle_auto_update(self):
        if self.auto_update.get():
            if not self.compass_running:
                self.compass_running = True
                threading.Thread(target=self.compass_simulation, daemon=True).start()
        else:
            self.compass_running = False

    # محاكاة تحديث البوصلة
    def compass_simulation(self):
        while self.compass_running and self.auto_update.get():
            self.current_heading = (self.current_heading + 2) % 360
            if self.parent.winfo_exists():
                self.parent.after(0, self.draw_compass)
            time.sleep(0.1)
