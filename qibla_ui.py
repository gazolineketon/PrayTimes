# -*- coding: utf-8 -*-
"""
qibla_ui.py
يحتوي هذا الملف على واجهة عرض القبلة.
"""

import tkinter as tk
from tkinter import messagebox
import math
import threading
import time
import requests
import logging

logger = logging.getLogger(__name__)

class QiblaWidget:
    def __init__(self, parent, settings, translator, colors, city, country):
        self.parent = parent
        self.settings = settings
        self.translator = translator
        self._ = self.translator.get
        self.colors = colors
        self.city = city
        self.country = country
        
        # Kaaba coordinates
        self.kaaba_lat = 21.422487
        self.kaaba_lon = 39.826206
        
        # Location variables
        self.user_lat = 0.0
        self.user_lon = 0.0
        self.qibla_direction = 0.0
        self.current_heading = 0.0
        
        # Control variables
        self.auto_update = tk.BooleanVar(value=False)
        self.compass_running = False
        
        self.qibla_card = self.create_card_frame(self.parent)
        if self.settings.qibla_enabled:
            self.setup_ui()
            self.get_location()

    def create_card_frame(self, parent, **kwargs):
        """Create a card-like frame."""
        frame = tk.Frame(parent, bg=self.colors['bg_card'], relief='flat', bd=1, highlightbackground=self.colors['border'], highlightthickness=1, **kwargs)
        return frame

    def setup_ui(self):
        """Setup the Qibla UI."""
        # Main container
        container = tk.Frame(self.qibla_card, bg=self.colors['bg_card'], pady=15)
        container.pack(fill='x', expand=True)

        # Title
        title_text = self._("qibla_direction")
        if self.city and self.country:
            title_text += f" - {self.city}, {self.country}"

        title_label = tk.Label(
            container, 
            text=title_text, 
            font=("Arial", 20, "bold"),
            fg="#16c79a", 
            bg=self.colors['bg_card']
        )
        title_label.pack(pady=10)
        
        # Location info frame
        location_frame = tk.Frame(container, bg=self.colors['bg_card'])
        location_frame.pack(pady=10)
        
        tk.Label(location_frame, text=self._("current_location"), 
                font=("Arial", 14, "bold"), fg=self.colors['text_primary'], bg=self.colors['bg_card']).pack()
        
        self.location_label = tk.Label(
            location_frame, 
            text=self._("getting_location"), 
            font=("Arial", 12), 
            fg="#16c79a", 
            bg=self.colors['bg_card']
        )
        self.location_label.pack()
        
        # Compass frame
        compass_frame = tk.Frame(container, bg=self.colors['bg_card'])
        compass_frame.pack(pady=20)
        
        self.canvas = tk.Canvas(
            compass_frame, 
            width=300, 
            height=300, 
            bg="#0f0f23", 
            highlightthickness=2,
            highlightcolor="#16c79a"
        )
        self.canvas.pack()
        
        # Direction info frame
        direction_frame = tk.Frame(container, bg=self.colors['bg_card'])
        direction_frame.pack(pady=15)
        
        tk.Label(direction_frame, text=self._("qibla_direction"), 
                font=("Arial", 14, "bold"), fg=self.colors['text_primary'], bg=self.colors['bg_card']).pack()
        
        self.direction_label = tk.Label(
            direction_frame, 
            text="--°", 
            font=("Arial", 18, "bold"), 
            fg="#ffc107", 
            bg=self.colors['bg_card']
        )
        self.direction_label.pack()
        
        self.distance_label = tk.Label(
            direction_frame, 
            text=self._("distance") + ": -- km", 
            font=("Arial", 12), 
            fg="#17a2b8", 
            bg=self.colors['bg_card']
        )
        self.distance_label.pack()
        
        # Control buttons frame
        control_frame = tk.Frame(container, bg=self.colors['bg_card'])
        control_frame.pack(pady=20)
        
        # Manual location entry
        manual_frame = tk.Frame(control_frame, bg=self.colors['bg_card'])
        manual_frame.pack(pady=10)
        
        tk.Label(manual_frame, text=self._("manual_location_entry"), 
                font=("Arial", 12), fg=self.colors['text_primary'], bg=self.colors['bg_card']).pack()
        
        coords_frame = tk.Frame(manual_frame, bg=self.colors['bg_card'])
        coords_frame.pack(pady=5)
        
        tk.Label(coords_frame, text=self._("latitude"), 
                font=("Arial", 10), fg=self.colors['text_primary'], bg=self.colors['bg_card']).grid(row=0, column=0, padx=5)
        self.lat_entry = tk.Entry(coords_frame, width=12, font=("Arial", 10))
        self.lat_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(coords_frame, text=self._("longitude"), 
                font=("Arial", 10), fg=self.colors['text_primary'], bg=self.colors['bg_card']).grid(row=0, column=2, padx=5)
        self.lon_entry = tk.Entry(coords_frame, width=12, font=("Arial", 10))
        self.lon_entry.grid(row=0, column=3, padx=5)
        
        # Buttons
        buttons_frame = tk.Frame(control_frame, bg=self.colors['bg_card'])
        buttons_frame.pack(pady=15)
        
        tk.Button(
            buttons_frame,
            text=self._("update_location"),
            command=self.update_manual_location,
            bg="#28a745",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            buttons_frame,
            text=self._("auto_detect_location"),
            command=self.get_location,
            bg="#17a2b8",
            fg="white",
            font=("Arial", 10, "bold"),
            width=15
        ).grid(row=0, column=1, padx=5)
        
        # Auto-update option
        auto_frame = tk.Frame(control_frame, bg=self.colors['bg_card'])
        auto_frame.pack(pady=10)
        
        tk.Checkbutton(
            auto_frame,
            text=self._("auto_update_compass"),
            variable=self.auto_update,
            command=self.toggle_auto_update,
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card'],
            selectcolor="#0f0f23",
            font=("Arial", 11)
        ).pack()
        
        self.draw_compass()

    def get_location(self):
        """Get current location using IP."""
        try:
            response = requests.get("http://ip-api.com/json/", timeout=5)
            data = response.json()
            
            if data['status'] == 'success':
                self.user_lat = float(data['lat'])
                self.user_lon = float(data['lon'])
                self.city = data.get('city', 'Unknown')
                self.country = data.get('country', 'Unknown')
                
                self.location_label.config(
                    text=f"{self.city}, {self.country}\n({self.user_lat:.4f}, {self.user_lon:.4f})"
                )
                
                self.calculate_qibla_direction()
                self.draw_compass()
                
            else:
                raise Exception("Failed to determine location")
                
        except Exception as e:
            messagebox.showwarning(self._("warning"), self._("auto_location_failed"))
            self.location_label.config(text=self._("location_failed_manual"))

    def update_manual_location(self):
        """Update location from manual entry."""
        try:
            lat = float(self.lat_entry.get())
            lon = float(self.lon_entry.get())
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                self.user_lat = lat
                self.user_lon = lon
                self.location_label.config(text=f"{self._('specified_location')}: ({lat:.4f}, {lon:.4f})")
                
                self.calculate_qibla_direction()
                self.draw_compass()
            else:
                messagebox.showerror(self._("error"), self._("invalid_coordinates"))
                
        except ValueError:
            messagebox.showerror(self._("error"), self._("invalid_numbers_for_coordinates"))

    def calculate_qibla_direction(self):
        """Calculate Qibla direction and distance."""
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
        
        distance = self.calculate_distance(self.user_lat, self.user_lon, self.kaaba_lat, self.kaaba_lon)
        
        self.direction_label.config(text=f"{self.qibla_direction:.1f}°")
        self.distance_label.config(text=f"{self._('distance')}: {distance:.0f} km")

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points on Earth."""
        R = 6371  # Earth radius in km
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance

    def draw_compass(self):
        """Draw the compass."""
        self.canvas.delete("all")
        center_x, center_y = 150, 150
        radius = 120
        
        self.canvas.create_oval(
            center_x - radius, center_y - radius,
            center_x + radius, center_y + radius,
            outline="#16c79a", width=3, fill="#0f0f23"
        )
        
        directions = [
            (0, self._("north_arabic"), "N"),
            (90, self._("east_arabic"), "E"), 
            (180, self._("south_arabic"), "S"),
            (270, self._("west_arabic"), "W")
        ]
        
        for angle, arabic, english in directions:
            x = center_x + (radius - 20) * math.sin(math.radians(angle))
            y = center_y - (radius - 20) * math.cos(math.radians(angle))
            
            self.canvas.create_text(
                x, y, text=f"{arabic}\n{english}", 
                fill="#16c79a", font=("Arial", 10, "bold"),
                justify="center"
            )
        
        for i in range(0, 360, 30):
            x1 = center_x + (radius - 10) * math.sin(math.radians(i))
            y1 = center_y - (radius - 10) * math.cos(math.radians(i))
            x2 = center_x + radius * math.sin(math.radians(i))
            y2 = center_y - radius * math.cos(math.radians(i))
            
            self.canvas.create_line(
                x1, y1, x2, y2, fill="#16c79a", width=2
            )
        
        if hasattr(self, 'qibla_direction'):
            self.draw_qibla_arrow(center_x, center_y, self.qibla_direction - self.current_heading)
        
        self.draw_north_arrow(center_x, center_y, -self.current_heading)

    def draw_qibla_arrow(self, center_x, center_y, angle):
        """Draw the Qibla direction arrow."""
        length = 80
        angle_rad = math.radians(angle)
        
        end_x = center_x + length * math.sin(angle_rad)
        end_y = center_y - length * math.cos(angle_rad)
        
        self.canvas.create_line(
            center_x, center_y, end_x, end_y,
            fill="#ffc107", width=4, arrow=tk.LAST,
            arrowshape=(10, 12, 5)
        )
        
        kaaba_x = center_x + (length + 15) * math.sin(angle_rad)
        kaaba_y = center_y - (length + 15) * math.cos(angle_rad)
        
        self.canvas.create_text(
            kaaba_x, kaaba_y, text="🕋", 
            font=("Arial", 16), fill="#ffc107"
        )

    def draw_north_arrow(self, center_x, center_y, angle):
        """Draw the North direction arrow."""
        length = 60
        angle_rad = math.radians(angle)
        
        end_x = center_x + length * math.sin(angle_rad)
        end_y = center_y - length * math.cos(angle_rad)
        
        self.canvas.create_line(
            center_x, center_y, end_x, end_y,
            fill="#dc3545", width=2, arrow=tk.LAST,
            arrowshape=(8, 10, 4)
        )

    def toggle_auto_update(self):
        """Toggle auto-update for the compass."""
        if self.auto_update.get():
            if not self.compass_running:
                self.compass_running = True
                threading.Thread(target=self.compass_simulation, daemon=True).start()
        else:
            self.compass_running = False
            # self.parent.destroy() # The widget doesn't control the window anymore.

    def compass_simulation(self):
        """Simulate compass movement."""
        while self.compass_running and self.auto_update.get():
            self.current_heading = (self.current_heading + 2) % 360
            if self.parent.winfo_exists():
                self.parent.after(0, self.draw_compass)
            time.sleep(0.1)

    def update_qibla(self, latitude: float, longitude: float, city: str, country: str):
        """Update Qibla direction based on coordinates."""
        if not self.settings.qibla_enabled:
            return
        try:
            if latitude != 0.0 or longitude != 0.0:
                self.user_lat = latitude
                self.user_lon = longitude
                self.city = city
                self.country = country
                self.location_label.config(text=f"{self.city}, {self.country}\n({self.user_lat:.4f}, {self.user_lon:.4f})")
                self.calculate_qibla_direction()
                self.draw_compass()
        except Exception as e:
            logger.error(f"Error updating Qibla: {e}")

    def pack(self, *args, **kwargs):
        if self.settings.qibla_enabled:
            self.qibla_card.pack(*args, **kwargs)

    def pack_forget(self):
        self.qibla_card.pack_forget()

    def on_closing(self):
        """Handle window closing."""
        self.compass_running = False