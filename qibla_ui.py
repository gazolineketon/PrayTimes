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

logger = logging.getLogger(__name__)

class QiblaWidget(tk.Frame):
    def __init__(self, parent, settings, translator, colors, city, country):
        super().__init__(parent, bg=colors['bg_card'], relief='flat', bd=1, highlightbackground=colors['border'], highlightthickness=1)
        self.parent = parent
        self.settings = settings
        self.translator = translator
        self._ = self.translator.get
        self.colors = colors
        self.city = city
        self.country = country
        self.kaaba_lat = 21.422487
        self.kaaba_lon = 39.826206
        self.user_lat = 0.0
        self.user_lon = 0.0
        self.qibla_direction = 0.0
        self.current_heading = 0.0
        self.auto_update = tk.BooleanVar(value=False)
        self.compass_running = False
        if self.settings.qibla_enabled:
            self.setup_ui()
            self.get_location()

    # إعداد واجهة المستخدم
    def setup_ui(self):
        container = tk.Frame(self, bg=self.colors['bg_card'], pady=5)
        container.pack(fill='x', expand=True)
        title_text = self._("qibla_direction")
        self.title_label = tk.Label(container, text=title_text, font=("Arial", 20, "bold"), fg="#16c79a", bg=self.colors['bg_card'])
        self.title_label.pack(pady=10)
        location_frame = tk.Frame(container, bg=self.colors['bg_card'])
        location_frame.pack(pady=10)
        self.location_label = tk.Label(location_frame, text=self._("getting_location"), font=("Arial", 14), fg="#16c79a", bg=self.colors['bg_card'])
        self.location_label.pack()
        compass_frame = tk.Frame(container, bg=self.colors['bg_card'])
        compass_frame.pack(pady=10)
        self.canvas = tk.Canvas(compass_frame, width=300, height=300, bg="#0f0f23", highlightthickness=2, highlightcolor="#16c79a")
        self.canvas.pack()
        direction_frame = tk.Frame(container, bg=self.colors['bg_card'])
        direction_frame.pack(pady=10)
        self.direction_label = tk.Label(direction_frame, text="°--", font=("Arial", 18, "bold"), fg="#ffc107", bg=self.colors['bg_card'])
        self.direction_label.pack()
        self.direction_note = tk.Label(direction_frame, text="اضبط اتجاه السهم الأحمر نحو الشمال الجغرافي", font=("Arial", 10, "bold"), fg="#000000", bg=self.colors['bg_card'])
        self.direction_note.pack()
        control_frame = tk.Frame(container, bg=self.colors['bg_card'])
        control_frame.pack(pady=10)
        auto_frame = tk.Frame(control_frame, bg=self.colors['bg_card'])
        auto_frame.pack(pady=10)
        tk.Checkbutton(auto_frame, text=self._("auto_update_compass"), variable=self.auto_update, command=self.toggle_auto_update, fg=self.colors['text_primary'], bg=self.colors['bg_card'], selectcolor="#0f0f23", font=("Arial", 11)).pack()
        self.draw_compass()

    # تحديث الموقع الحالي من API
    def get_location(self):
        def _get_location_task():
            location_found = False
            user_lat = None
            user_lon = None
            try:
                # استخدام geolocation-db.com للحصول على الإحداثيات
                response = requests.get("https://geolocation-db.com/json/", timeout=5)
                response.raise_for_status()
                data = response.json()
                if data and data.get('latitude') and data.get('longitude'):
                    user_lat = float(data['latitude'])
                    user_lon = float(data['longitude'])
                    logger.info(f"Coordinates from geolocation-db.com: ({user_lat}, {user_lon})")

                    # Nominatim الآن احصل على المدينة/الدولة من الإحداثيات باستخدام
                    city, country = self._get_city_country_from_coords(user_lat, user_lon)
                    if city and country:
                        self.user_lat = user_lat
                        self.user_lon = user_lon
                        self.city = city
                        self.country = country
                        location_found = True
                        logger.info(f"Nominatim الموقع من {self.city}, {self.country}")
                    else:
                        logger.warning("Nominatim لم يتمكن من تحديد المدينة والدولة من خط العرض والطول")
                else:
                    logger.warning(f"استجابة geolocation-db.com لبيانات الموقع المفقودة {data}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"فشل طلب geolocation-db.com {e}")
            except Exception as e:
                logger.error(f"حدث خطأ غير متوقع مع geolocation-db.com {e}")

            if not location_found:
                logger.info("Nominatim محاولة الحصول على الموقع من الإعدادات المحفوظة باستخدام")
                # الرجوع إلى المدينة/البلد الحالي من الإعدادات
                lat, lon = self._get_coords_from_city_country(self.city, self.country)
                if lat is not None and lon is not None:
                    self.user_lat = lat
                    self.user_lon = lon
                    location_found = True
                    logger.info(f"Location from Nominatim (settings): {self.city}, {self.country} ({self.user_lat}, {self.user_lon})")
                else:
                    logger.error(f"Failed to get coordinates for {self.city}, {self.country} from Nominatim.")

            if location_found:
                self.parent.after(0, lambda: self.location_label.config(text=f"{self.city}, {self.country}"))
                self.parent.after(0, self.calculate_qibla_direction)
                self.parent.after(0, self.draw_compass)
            else:
                self.parent.after(0, lambda: self.location_label.config(text=self._("فشل تحديد الموقع")))
                # اختياريًا، قم بتعيين خط العرض/الطول الافتراضي إذا فشلت جميع المحاولات
                self.user_lat = 0.0
                self.user_lon = 0.0
                self.parent.after(0, self.calculate_qibla_direction)
                self.parent.after(0, self.draw_compass)

        threading.Thread(target=_get_location_task, daemon=True).start()

    def _get_city_country_from_coords(self, lat, lon):
        """
        جلب المدينة والدولة من خط العرض والطول باستخدام Nominatim API.
        """
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=10&accept-language=ar"
            headers = {'User-Agent': 'PrayTimesApp/1.0 (gazoline1022@gmail.com)'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if data and 'address' in data:
                address = data['address']
                city = address.get('city', address.get('town', address.get('village')))
                country = address.get('country')
                if city and country:
                    return city, country
                else:
                    logger.warning(f"Nominatim reverse geocoding did not return city or country for {lat}, {lon}. Address {address}")
                    return None, None
            else:
                logger.warning(f"Nominatim reverse geocoding found no results for {lat}, {lon}")
                return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Nominatim API reverse geocoding request failed for {lat}, {lon}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"An unexpected error occurred with Nominatim API reverse for {lat}, {lon}: {e}")
            return None, None

    def _get_coords_from_city_country(self, city, country):
        """
        جلب الإحداثيات (خط العرض والطول) لمدينة ودولة معينة باستخدام Nominatim API.
        """
        try:
            # استخدام API Nominatim OpenStreetMap لتوفير وكيل المستخدم
            url = f"https://nominatim.openstreetmap.org/search?city={city}&country={country}&format=json&limit=1"
            headers = {'User-Agent': 'PrayTimesApp/1.0 (gazoline1022@gmail.com)'}
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()

            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
            else:
                logger.warning(f"Nominatim found no results for {city}, {country}")
                return None, None
        except requests.exceptions.RequestException as e:
            logger.error(f"Nominatim API request failed for {city}, {country}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"An unexpected error occurred with Nominatim API for {city}, {country}: {e}")
            return None, None

    # تحديث الموقع يدويًا
    def update_qibla(self, lat, lon, city, country):
        self.user_lat = lat
        self.user_lon = lon
        self.city = city
        self.country = country
        if hasattr(self, 'location_label'):
            self.location_label.config(text=f"{self.city}, {self.country}\n({self.user_lat:.4f}, {self.user_lon:.4f})")
        if hasattr(self, 'title_label'):
            title_text = self._("qibla_direction")
            self.title_label.config(text=title_text)
        self.calculate_qibla_direction()
        self.draw_compass()

    # حساب اتجاه القبلة
    def calculate_qibla_direction(self):
        lat1_rad = math.radians(self.user_lat)
        lon1_rad = math.radians(self.user_lon)
        lat2_rad = math.radians(self.kaaba_lat)
        lon2_rad = math.radians(self.kaaba_lon)
        dlon = lon2_rad - lon1_rad
        y = math.sin(dlon) * math.cos(lat2_rad)
        x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        self.qibla_direction = (bearing_deg + 360) % 360
        self.direction_label.config(text=f"°{self.qibla_direction:.1f} زاوية القبلة من الشمال")
        self.direction_note.config(text="اضبط اتجاه السهم الأحمر نحو الشمال الجغرافي")

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