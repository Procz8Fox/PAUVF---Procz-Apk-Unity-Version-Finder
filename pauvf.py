import tkinter as tk
from tkinter import filedialog, messagebox
import zipfile
import os
import re
import struct
import threading
import time

class Theme:
    BG_DARK = "#0a1f0a"
    BG_MEDIUM = "#0f2f0f"
    BG_LIGHT = "#153515"
    
    ACCENT_PRIMARY = "#00ff6a"
    ACCENT_SECONDARY = "#00cc55"
    ACCENT_GLOW = "#00ff6a"
    
    TEXT_PRIMARY = "#e0ffe0"
    TEXT_SECONDARY = "#a0d0a0"
    TEXT_MUTED = "#607060"
    
    BUTTON_BG = "#1a4a1a"
    BUTTON_HOVER = "#2a6a2a"
    BUTTON_ACTIVE = "#3a8a3a"
    
    BORDER_COLOR = "#00cc55"
    SHADOW_COLOR = "#001a00"

    ANIMATION_SPEED = 16  # ms
    FADE_STEPS = 15
    PULSE_SPEED = 50

class UnityVersionExtractor:
    """Extracts Unity version from APK files"""
    

    VERSION_PATTERNS = [
        rb'(\d+\.\d+\.\d+[a-zA-Z]?\d*)',  # e.g., 2021.3.1f1
        rb'Unity (\d+\.\d+\.\d+)',
        rb'unity version[:\s]+(\d+\.\d+\.\d+[a-zA-Z]?\d*)',
    ]
    
    TARGET_FILES = [
        ('assets/bin/Data/globalgamemanagers', 'globalgamemanagers'),
        ('assets/bin/Data/data.unity3d', 'data.unity3d'),
        ('assets/bin/Data/level0', 'level0'),
        ('assets/bin/Data/mainData', 'mainData'),
        ('lib/armeabi-v7a/libunity.so', 'libunity.so (ARM)'),
        ('lib/arm64-v8a/libunity.so', 'libunity.so (ARM64)'),
        ('lib/x86/libunity.so', 'libunity.so (x86)'),
    ]
    
    STEPS = [
        ('validating', 'Validating APK file...', 5),
        ('opening', 'Opening APK archive...', 10),
        ('checking_unity', 'Checking for Unity signatures...', 15),
        ('scanning_files', 'Scanning file structure...', 25),
        ('extracting', 'Extracting Unity data...', 40),
        ('parsing', 'Parsing version info...', 70),
        ('deep_scan', 'Deep scanning assets...', 85),
        ('finalizing', 'Finalizing results...', 100),
    ]
    
    @staticmethod
    def extract_version(apk_path: str, progress_callback=None) -> dict:
        """
        Extract Unity version from an APK file.
        Returns a dict with version info and metadata.
        """
        result = {
            'success': False,
            'version': None,
            'source_file': None,
            'is_unity': False,
            'error': None,
            'details': []
        }
        
        def update_progress(step_name, message, progress, file_name=None):
            """Update progress with step info"""
            if progress_callback:
                if file_name:
                    progress_callback(message, progress, file_name)
                else:
                    progress_callback(message, progress)
            time.sleep(0.15) 
        
        try:
            update_progress('validating', '🔍 Validating APK file...', 5)
            
            if not zipfile.is_zipfile(apk_path):
                result['error'] = "Invalid APK file (not a valid ZIP archive)"
                return result
            
            update_progress('opening', '📂 Opening APK archive...', 10)
            
            with zipfile.ZipFile(apk_path, 'r') as apk:
                file_list = apk.namelist()
                total_files = len(file_list)
                
                update_progress('checking_unity', '🎮 Checking for Unity signatures...', 15)
                time.sleep(0.2)
                
                unity_indicators = [
                    'assets/bin/Data/',
                    'lib/armeabi-v7a/libunity.so',
                    'lib/arm64-v8a/libunity.so',
                    'lib/x86/libunity.so',
                    'lib/x86_64/libunity.so',
                ]
                
                for indicator in unity_indicators:
                    if any(f.startswith(indicator) or f == indicator for f in file_list):
                        result['is_unity'] = True
                        result['details'].append(f"✓ Found Unity indicator: {indicator}")
                        break
                
                if not result['is_unity']:
                    result['error'] = "This APK does not appear to be a Unity game"
                    return result
                
                update_progress('scanning_files', '📁 Scanning file structure...', 25)
                time.sleep(0.2)
                
                target_files_found = [(f, n) for f, n in UnityVersionExtractor.TARGET_FILES if f in file_list]
                total_targets = len(target_files_found)
                
                for i, (target, display_name) in enumerate(target_files_found):
                    progress = 30 + int((i / max(total_targets, 1)) * 40)
                    update_progress('extracting', f'📦 Extracting {display_name}...', progress, display_name)
                    
                    try:
                        data = apk.read(target)
                        
                        update_progress('parsing', f'🔎 Parsing {display_name}...', progress + 5, display_name)
                        version = UnityVersionExtractor._find_version_in_data(data)
                        
                        if version:
                            update_progress('finalizing', '✅ Version found!', 100)
                            result['success'] = True
                            result['version'] = version
                            result['source_file'] = target
                            return result
                    except Exception as e:
                        result['details'].append(f"⚠ Could not read {display_name}: {str(e)}")
                
                update_progress('deep_scan', '🔬 Deep scanning assets folder...', 75)
                data_files = [f for f in file_list if f.startswith('assets/bin/Data/')]
                scan_limit = min(20, len(data_files))
                
                for i, file_path in enumerate(data_files[:scan_limit]):
                    file_name = os.path.basename(file_path)
                    progress = 75 + int((i / scan_limit) * 20)
                    update_progress('deep_scan', f'🔬 Scanning {file_name}...', progress, file_name)
                    
                    try:
                        data = apk.read(file_path)
                        version = UnityVersionExtractor._find_version_in_data(data)
                        
                        if version:
                            update_progress('finalizing', '✅ Version found!', 100)
                            result['success'] = True
                            result['version'] = version
                            result['source_file'] = file_path
                            return result
                    except:
                        pass
                
                update_progress('finalizing', '⚠️ Version not found', 100)
                result['error'] = "Unity version could not be determined (file may be obfuscated)"
                
        except zipfile.BadZipFile:
            result['error'] = "Corrupted APK file"
        except PermissionError:
            result['error'] = "Permission denied - cannot access the file"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
        
        return result
    
    @staticmethod
    def _find_version_in_data(data: bytes) -> str:
        """Search for Unity version string in binary data"""
        unity_indices = []
        search_term = b'Unity'
        idx = 0
        while True:
            idx = data.find(search_term, idx)
            if idx == -1:
                break
            unity_indices.append(idx)
            idx += 1
        
        for idx in unity_indices[:10]:
            start = max(0, idx - 50)
            end = min(len(data), idx + 200)
            chunk = data[start:end]
            for pattern in UnityVersionExtractor.VERSION_PATTERNS:
                matches = re.findall(pattern, chunk, re.IGNORECASE)
                for match in matches:
                    version = match.decode('utf-8', errors='ignore')
                    if UnityVersionExtractor._is_valid_unity_version(version):
                        return version
        for pattern in UnityVersionExtractor.VERSION_PATTERNS:
            matches = re.findall(pattern, data[:500000], re.IGNORECASE)  # First 500KB
            for match in matches:
                version = match.decode('utf-8', errors='ignore')
                if UnityVersionExtractor._is_valid_unity_version(version):
                    return version
        version_starts = [b'20', b'5.', b'4.', b'3.']
        for vs in version_starts:
            idx = 0
            while True:
                idx = data.find(vs, idx)
                if idx == -1 or idx > 500000:
                    break
                try:
                    end_idx = idx
                    while end_idx < min(idx + 30, len(data)):
                        if data[end_idx] == 0 or data[end_idx] < 32 or data[end_idx] > 126:
                            break
                        end_idx += 1
                    
                    if end_idx > idx + 5:
                        potential = data[idx:end_idx].decode('utf-8', errors='ignore')
                        if UnityVersionExtractor._is_valid_unity_version(potential):
                            return potential
                except:
                    pass
                idx += 1
        
        return None
    
    @staticmethod
    def _is_valid_unity_version(version: str) -> bool:
        """Check if a string looks like a valid Unity version"""
        if not version or len(version) < 5 or len(version) > 20:
            return False
        valid_starts = ['2017', '2018', '2019', '2020', '2021', '2022', '2023', '2024', '2025', '5.', '4.', '3.']
        if not any(version.startswith(vs) for vs in valid_starts):
            return False
        if '.' not in version:
            return False
        pattern = r'^\d{4}\.\d+\.\d+[a-zA-Z]?\d*$|^\d\.\d+\.\d+[a-zA-Z]?\d*$'
        return bool(re.match(pattern, version))

class RoundedFrame(tk.Canvas):
    """A frame with rounded corners"""
    
    def __init__(self, parent, width, height, radius=20, bg=Theme.BG_MEDIUM, 
                 border_color=Theme.BORDER_COLOR, border_width=2, **kwargs):
        super().__init__(parent, width=width, height=height, 
                        bg=Theme.BG_DARK, highlightthickness=0, **kwargs)
        
        self.radius = radius
        self.bg_color = bg
        self.border_color = border_color
        self.border_width = border_width
        self._draw_rounded_rect()
    
    def _draw_rounded_rect(self):
        """Draw a rounded rectangle"""
        self.delete("rounded_rect")
        
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        r = self.radius
        bw = self.border_width

        points = [
            r, 0,
            w - r, 0,
            w, 0,
            w, r,
            w, h - r,
            w, h,
            w - r, h,
            r, h,
            0, h,
            0, h - r,
            0, r,
            0, 0,
        ]

        self.create_polygon(points, smooth=True, fill=self.border_color, 
                           tags="rounded_rect", outline="")

        inner_points = [
            r, bw,
            w - r, bw,
            w - bw, bw,
            w - bw, r,
            w - bw, h - r,
            w - bw, h - bw,
            w - r, h - bw,
            r, h - bw,
            bw, h - bw,
            bw, h - r,
            bw, r,
            bw, bw,
        ]
        
        self.create_polygon(inner_points, smooth=True, fill=self.bg_color,
                           tags="rounded_rect", outline="")


class GlowButton(tk.Canvas):
    """A button with glow effect and hover animation"""
    
    def __init__(self, parent, text, command, width=200, height=50, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=Theme.BG_DARK, highlightthickness=0, **kwargs)
        
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.hover = False
        self.glow_alpha = 0
        self.radius = 15
        self.font_size = 12
        
        self._draw_button()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)
    
    def _draw_button(self, pressed=False):
        """Draw the button"""
        self.delete("all")
        
        w, h = self.width, self.height
        r = self.radius

        if pressed:
            bg = Theme.BUTTON_ACTIVE
            border = Theme.ACCENT_PRIMARY
        elif self.hover:
            bg = Theme.BUTTON_HOVER
            border = Theme.ACCENT_PRIMARY
        else:
            bg = Theme.BUTTON_BG
            border = Theme.ACCENT_SECONDARY

        if self.hover and self.glow_alpha > 0:
            for i in range(3):
                alpha = int(self.glow_alpha * (3 - i) / 3)
                glow_color = self._blend_color(Theme.BG_DARK, Theme.ACCENT_GLOW, alpha / 255)
                offset = (3 - i) * 2
                self._draw_rounded_rect(offset, offset, w - offset * 2, h - offset * 2, 
                                       r, glow_color, glow_color)

        self._draw_rounded_rect(0, 0, w, h, r, bg, border)

        font_size = getattr(self, 'font_size', 12)
        self.create_text(w // 2, h // 2, text=self.text, fill=Theme.TEXT_PRIMARY,
                        font=("Segoe UI", font_size, "bold"), anchor="center")
    
    def _draw_rounded_rect(self, x, y, w, h, r, fill, outline):
        """Draw a single rounded rectangle"""
        points = [
            x + r, y,
            x + w - r, y,
            x + w, y,
            x + w, y + r,
            x + w, y + h - r,
            x + w, y + h,
            x + w - r, y + h,
            x + r, y + h,
            x, y + h,
            x, y + h - r,
            x, y + r,
            x, y,
        ]
        self.create_polygon(points, smooth=True, fill=fill, outline=outline, width=2)
    
    def _blend_color(self, color1, color2, alpha):
        """Blend two colors"""
        c1 = self.winfo_rgb(color1)
        c2 = self.winfo_rgb(color2)
        
        r = int((c1[0] * (1 - alpha) + c2[0] * alpha) / 256)
        g = int((c1[1] * (1 - alpha) + c2[1] * alpha) / 256)
        b = int((c1[2] * (1 - alpha) + c2[2] * alpha) / 256)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _on_enter(self, event):
        self.hover = True
        self._animate_glow(True)
    
    def _on_leave(self, event):
        self.hover = False
        self._animate_glow(False)
    
    def _animate_glow(self, fade_in):
        """Animate the glow effect"""
        target = 100 if fade_in else 0
        step = 10 if fade_in else -10
        
        def animate():
            self.glow_alpha += step
            if fade_in:
                self.glow_alpha = min(self.glow_alpha, target)
            else:
                self.glow_alpha = max(self.glow_alpha, target)
            
            self._draw_button()
            
            if self.glow_alpha != target:
                self.after(Theme.ANIMATION_SPEED, animate)
        
        animate()
    
    def _on_click(self, event):
        self._draw_button(pressed=True)
    
    def _on_release(self, event):
        self._draw_button()
        if self.command:
            self.command()
    
    def resize(self, width, height, font_size=12):
        """Resize the button dynamically"""
        self.width = width
        self.height = height
        self.radius = min(15, height // 3)
        self.font_size = font_size
        self.config(width=width, height=height)
        self._draw_button()


class AnimatedLabel(tk.Label):
    """Label with fade-in animation"""
    
    def __init__(self, parent, **kwargs):
        self.target_fg = kwargs.pop('fg', Theme.TEXT_PRIMARY)
        super().__init__(parent, fg=Theme.BG_DARK, **kwargs)
        self._fade_in()
    
    def _fade_in(self):
        """Animate text fading in"""
        steps = Theme.FADE_STEPS
        
        def get_color(step):
            bg_rgb = self.winfo_rgb(Theme.BG_DARK)
            fg_rgb = self.winfo_rgb(self.target_fg)
            
            r = int((bg_rgb[0] + (fg_rgb[0] - bg_rgb[0]) * step / steps) / 256)
            g = int((bg_rgb[1] + (fg_rgb[1] - bg_rgb[1]) * step / steps) / 256)
            b = int((bg_rgb[2] + (fg_rgb[2] - bg_rgb[2]) * step / steps) / 256)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        
        def animate(step=0):
            if step <= steps:
                self.config(fg=get_color(step))
                self.after(Theme.ANIMATION_SPEED, lambda: animate(step + 1))
        
        self.after(100, animate)
    
    def set_text(self, text):
        """Set text with animation"""
        self.config(text=text)


class PulsingDot(tk.Canvas):
    """A pulsing dot indicator"""
    
    def __init__(self, parent, size=10, **kwargs):
        super().__init__(parent, width=size * 3, height=size * 3,
                        bg=Theme.BG_DARK, highlightthickness=0, **kwargs)
        
        self.size = size
        self.pulse_value = 0
        self.pulse_direction = 1
        self.running = False
    
    def start(self):
        """Start the pulsing animation"""
        self.running = True
        self._pulse()
    
    def stop(self):
        """Stop the animation"""
        self.running = False
        self.delete("all")
    
    def _pulse(self):
        """Animate the pulse"""
        if not self.running:
            return
        
        self.delete("all")

        self.pulse_value += self.pulse_direction * 5
        if self.pulse_value >= 100:
            self.pulse_direction = -1
        elif self.pulse_value <= 0:
            self.pulse_direction = 1

        for i in range(3, 0, -1):
            alpha = (self.pulse_value / 100) * (4 - i) / 3
            radius = self.size + i * 2
            color = self._get_alpha_color(Theme.ACCENT_PRIMARY, alpha * 0.5)
            cx, cy = self.size * 1.5, self.size * 1.5
            self.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                           fill=color, outline="")

        cx, cy = self.size * 1.5, self.size * 1.5
        self.create_oval(cx - self.size/2, cy - self.size/2, 
                        cx + self.size/2, cy + self.size/2,
                        fill=Theme.ACCENT_PRIMARY, outline="")
        
        self.after(Theme.PULSE_SPEED, self._pulse)
    
    def _get_alpha_color(self, color, alpha):
        """Get a color with alpha blended against background"""
        bg_rgb = self.winfo_rgb(Theme.BG_DARK)
        fg_rgb = self.winfo_rgb(color)
        
        r = int((bg_rgb[0] * (1 - alpha) + fg_rgb[0] * alpha) / 256)
        g = int((bg_rgb[1] * (1 - alpha) + fg_rgb[1] * alpha) / 256)
        b = int((bg_rgb[2] * (1 - alpha) + fg_rgb[2] * alpha) / 256)
        
        return f"#{r:02x}{g:02x}{b:02x}"


class ProgressBar(tk.Canvas):
    """Animated progress bar with smooth transitions"""
    
    def __init__(self, parent, width=400, height=10, **kwargs):
        super().__init__(parent, width=width, height=height,
                        bg=Theme.BG_DARK, highlightthickness=0, **kwargs)
        
        self.bar_width = width
        self.bar_height = height
        self.progress = 0
        self.target_progress = 0
        self.indeterminate = False
        self.ind_pos = 0
        self.animating = False
        self.radius = height // 2
        
        self._draw()
    
    def _draw(self):
        """Draw the progress bar with rounded corners"""
        self.delete("all")
        
        h = self.bar_height
        r = self.radius
        
        self._draw_rounded_bar(0, self.bar_width, Theme.BG_LIGHT)
        
        if self.indeterminate:
            seg_width = 120
            x1 = self.ind_pos - seg_width
            x2 = self.ind_pos

            for i in range(seg_width):
                alpha = (i / seg_width) ** 0.5 
                color = self._blend(Theme.BG_LIGHT, Theme.ACCENT_PRIMARY, alpha)
                x = x1 + i
                if 0 <= x < self.bar_width:
                    self.create_line(x, 1, x, h - 1, fill=color, width=1)
        else:
            fill_width = int(self.bar_width * self.progress / 100)
                for i in range(3):
                    glow_alpha = 0.15 * (3 - i)
                    glow_color = self._blend(Theme.BG_DARK, Theme.ACCENT_GLOW, glow_alpha)
                    offset = i + 1
                    self.create_rectangle(0, -offset, fill_width, h + offset,
                                         fill=glow_color, outline="")
                
                self._draw_rounded_bar(0, fill_width, Theme.ACCENT_PRIMARY)
                
                if fill_width > 10:
                    shine_x = fill_width - 5
                    self.create_rectangle(shine_x, 2, fill_width - 2, h - 2,
                                         fill=self._blend(Theme.ACCENT_PRIMARY, "#ffffff", 0.3),
                                         outline="")
    
    def _draw_rounded_bar(self, start_x, end_x, color):
        """Draw a rounded bar segment"""
        h = self.bar_height
        if end_x - start_x < 4:
            self.create_rectangle(start_x, 0, end_x, h, fill=color, outline="")
        else:
            self.create_rectangle(start_x + 2, 0, end_x - 2, h, fill=color, outline="")
            self.create_oval(start_x, 0, start_x + h, h, fill=color, outline="")
            self.create_oval(end_x - h, 0, end_x, h, fill=color, outline="")
    
    def _blend(self, c1, c2, alpha):
        """Blend two colors"""
        try:
            r1 = int(c1[1:3], 16)
            g1 = int(c1[3:5], 16)
            b1 = int(c1[5:7], 16)
            
            r2 = int(c2[1:3], 16)
            g2 = int(c2[3:5], 16)
            b2 = int(c2[5:7], 16)
            
            r = int(r1 + (r2 - r1) * alpha)
            g = int(g1 + (g2 - g1) * alpha)
            b = int(b1 + (b2 - b1) * alpha)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return c1
    
    def set_progress(self, value, animate=True):
        """Set progress value (0-100) with optional smooth animation"""
        self.indeterminate = False
        self.target_progress = max(0, min(100, value))
        
        if animate and not self.animating:
            self._animate_to_target()
        elif not animate:
            self.progress = self.target_progress
            self._draw()
    
    def _animate_to_target(self):
        """Smoothly animate to target progress"""
        if self.animating:
            return
        
        self.animating = True
        
        def animate():
            if abs(self.progress - self.target_progress) < 1:
                self.progress = self.target_progress
                self._draw()
                self.animating = False
                return
            
            diff = self.target_progress - self.progress
            self.progress += diff * 0.2
            self._draw()
            self.after(16, animate)
        
        animate()
    
    def start_indeterminate(self):
        """Start indeterminate animation"""
        self.indeterminate = True
        self.animating = False
        self._animate_indeterminate()
    
    def _animate_indeterminate(self):
        """Animate indeterminate mode"""
        if not self.indeterminate:
            return
        
        self.ind_pos += 6
        if self.ind_pos > self.bar_width + 120:
            self.ind_pos = 0
        
        self._draw()
        self.after(16, self._animate_indeterminate)
    
    def stop(self):
        """Stop animation and reset"""
        self.indeterminate = False
        self.animating = False
        self.progress = 0
        self.target_progress = 0
        self._draw()
    
    def resize(self, width, height):
        """Resize the progress bar dynamically"""
        self.bar_width = width
        self.bar_height = height
        self.radius = height // 2
        self.config(width=width, height=height)
        self._draw()

class PAUVFApp:
    """Procz APK Unity Version Finder Application"""
    
    BASE_WIDTH = 600
    BASE_HEIGHT = 550
    MIN_WIDTH = 450
    MIN_HEIGHT = 400
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PAUVF - Procz APK Unity Version Finder")
        self.root.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}")
        self.root.configure(bg=Theme.BG_DARK)
        self.root.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.BASE_WIDTH) // 2
        y = (self.root.winfo_screenheight() - self.BASE_HEIGHT) // 2
        self.root.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}+{x}+{y}")
        self.current_scale = 1.0
        self.last_width = self.BASE_WIDTH
        self.last_height = self.BASE_HEIGHT
        self._create_ui()
        self._animate_intro()
        self.root.bind('<Configure>', self._on_resize)
    
    def _get_scale(self):
        """Calculate current scale factor based on window size"""
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        scale_w = width / self.BASE_WIDTH
        scale_h = height / self.BASE_HEIGHT
        
        return min(scale_w, scale_h)
    
    def _scale_font(self, base_size):
        """Scale font size based on current window size"""
        return max(8, int(base_size * self.current_scale))
    
    def _on_resize(self, event):
        """Handle window resize events"""
        if event.widget != self.root:
            return
        new_width = event.width
        new_height = event.height
        if abs(new_width - self.last_width) < 10 and abs(new_height - self.last_height) < 10:
            return
        
        self.last_width = new_width
        self.last_height = new_height
        self.current_scale = self._get_scale()
        self._update_scaling()
    
    def _update_scaling(self):
        """Update all UI elements with new scale"""
        scale = self.current_scale
        self.title_label.config(font=("Consolas", self._scale_font(32), "bold"))
        self.subtitle_label.config(font=("Segoe UI", self._scale_font(12)))
        self.file_icon.config(font=("Segoe UI Emoji", self._scale_font(40)))
        self.file_label.config(font=("Segoe UI", self._scale_font(11)))
        self.progress_percent_label.config(font=("Consolas", self._scale_font(11), "bold"))
        self.status_label.config(font=("Segoe UI", self._scale_font(10)))
        self.current_file_label.config(font=("Consolas", self._scale_font(9)))
        self.result_label.config(font=("Consolas", self._scale_font(14)))
        self.details_label.config(font=("Segoe UI", self._scale_font(9)),
                                  wraplength=int(500 * scale))
        self.footer.config(font=("Segoe UI", self._scale_font(9)))
        new_bar_width = int(450 * scale)
        new_bar_height = max(8, int(12 * scale))
        self.progress_bar.resize(new_bar_width, new_bar_height)
        line_width = int(400 * scale)
        self.line_canvas.config(width=line_width)
        self.line_canvas.delete("all")
        self.line_canvas.create_rectangle(0, 0, line_width, 3, fill=Theme.ACCENT_SECONDARY, outline="")
        btn_width = int(250 * scale)
        btn_height = int(50 * scale)
        self.select_button.resize(btn_width, btn_height, self._scale_font(12))
        pad = int(30 * scale)
        self.main_frame.pack_configure(padx=pad, pady=pad)
    
    def _create_ui(self):
        """Create the main UI"""
        self.main_frame = tk.Frame(self.root, bg=Theme.BG_DARK)
        self.main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        self.header_frame = tk.Frame(self.main_frame, bg=Theme.BG_DARK)
        self.header_frame.pack(fill="x", pady=(0, 20))
        self.title_label = tk.Label(
            self.header_frame,
            text="🎮 PAUVF",
            font=("Consolas", 32, "bold"),
            fg=Theme.ACCENT_PRIMARY,
            bg=Theme.BG_DARK
        )
        self.title_label.pack()
        
        self.subtitle_label = tk.Label(
            self.header_frame,
            text="Procz APK Unity Version Finder",
            font=("Segoe UI", 12),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_DARK
        )
        self.subtitle_label.pack(pady=(5, 0))
        self.line_canvas = tk.Canvas(
            self.header_frame, 
            width=400, height=3,
            bg=Theme.BG_DARK, 
            highlightthickness=0
        )
        self.line_canvas.pack(pady=15)
        self.line_canvas.create_rectangle(0, 0, 400, 3, fill=Theme.ACCENT_SECONDARY, outline="")
        self.content_frame = tk.Frame(self.main_frame, bg=Theme.BG_DARK)
        self.content_frame.pack(fill="both", expand=True)
        self.file_frame = tk.Frame(self.content_frame, bg=Theme.BG_MEDIUM, 
                                  highlightbackground=Theme.BORDER_COLOR,
                                  highlightthickness=2)
        self.file_frame.pack(fill="x", pady=10, ipady=20, ipadx=20)
        
        self.file_icon = tk.Label(
            self.file_frame,
            text="📦",
            font=("Segoe UI Emoji", 40),
            bg=Theme.BG_MEDIUM
        )
        self.file_icon.pack(pady=(10, 5))
        
        self.file_label = tk.Label(
            self.file_frame,
            text="No APK file selected",
            font=("Segoe UI", 11),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_MEDIUM
        )
        self.file_label.pack()
        self.button_frame = tk.Frame(self.content_frame, bg=Theme.BG_DARK)
        self.button_frame.pack(pady=20)
        
        self.select_button = GlowButton(
            self.button_frame,
            text="📂 SELECT APK FILE",
            command=self._select_file,
            width=250,
            height=50
        )
        self.select_button.pack()
        self.status_frame = tk.Frame(self.content_frame, bg=Theme.BG_DARK)
        self.status_frame.pack(fill="x", pady=10)
        self.progress_percent_label = tk.Label(
            self.status_frame,
            text="",
            font=("Consolas", 11, "bold"),
            fg=Theme.ACCENT_PRIMARY,
            bg=Theme.BG_DARK
        )
        self.progress_percent_label.pack(pady=(0, 5))
        self.progress_bar = ProgressBar(self.status_frame, width=450, height=12)
        self.progress_bar.pack(pady=5)
        self.status_label = tk.Label(
            self.status_frame,
            text="",
            font=("Segoe UI", 10),
            fg=Theme.TEXT_SECONDARY,
            bg=Theme.BG_DARK
        )
        self.status_label.pack(pady=(5, 0))
        self.current_file_label = tk.Label(
            self.status_frame,
            text="",
            font=("Consolas", 9),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        )
        self.current_file_label.pack()
        self.result_frame = tk.Frame(self.content_frame, bg=Theme.BG_DARK)
        self.result_frame.pack(fill="both", expand=True, pady=10)
        
        self.result_label = tk.Label(
            self.result_frame,
            text="",
            font=("Consolas", 14),
            fg=Theme.ACCENT_PRIMARY,
            bg=Theme.BG_DARK,
            justify="center"
        )
        self.result_label.pack(pady=10)
        
        self.details_label = tk.Label(
            self.result_frame,
            text="",
            font=("Segoe UI", 9),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK,
            justify="center",
            wraplength=500
        )
        self.details_label.pack()
        self.footer = tk.Label(
            self.main_frame,
            text="Made with 💚 by Procz",
            font=("Segoe UI", 9),
            fg=Theme.TEXT_MUTED,
            bg=Theme.BG_DARK
        )
        self.footer.pack(side="bottom", pady=(10, 0))
    
    def _animate_intro(self):
        """Play intro animation"""
        def pulse_title(step=0):
            if step < 20:
                alpha = abs(10 - step) / 10
                color = self._blend_color(Theme.ACCENT_SECONDARY, Theme.ACCENT_PRIMARY, alpha)
                self.title_label.config(fg=color)
                self.root.after(50, lambda: pulse_title(step + 1))
            else:
                self.title_label.config(fg=Theme.ACCENT_PRIMARY)
        
        self.root.after(500, pulse_title)
    
    def _blend_color(self, c1, c2, alpha):
        """Blend two colors"""
        r1 = int(c1[1:3], 16)
        g1 = int(c1[3:5], 16)
        b1 = int(c1[5:7], 16)
        
        r2 = int(c2[1:3], 16)
        g2 = int(c2[3:5], 16)
        b2 = int(c2[5:7], 16)
        
        r = int(r1 + (r2 - r1) * alpha)
        g = int(g1 + (g2 - g1) * alpha)
        b = int(b1 + (b2 - b1) * alpha)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    def _select_file(self):
        """Open file dialog to select APK"""
        file_path = filedialog.askopenfilename(
            title="Select APK File",
            filetypes=[
                ("APK Files", "*.apk"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            self._process_file(file_path)
    
    def _process_file(self, file_path):
        """Process the selected APK file"""
        filename = os.path.basename(file_path)
        self.file_label.config(text=filename, fg=Theme.TEXT_PRIMARY)
        self.file_icon.config(text="📱")
        
        self.result_label.config(text="")
        self.details_label.config(text="")
        self.status_label.config(text="Starting analysis...")
        self.current_file_label.config(text="")
        self.progress_percent_label.config(text="0%")
        self.progress_bar.set_progress(0, animate=False)
        def extract():
            def update_status(message, progress, file_name=None):
                """Update UI with detailed progress"""
                def update():
                    self.status_label.config(text=message)
                    self.progress_bar.set_progress(progress)
                    self.progress_percent_label.config(text=f"{int(progress)}%")
                    if file_name:
                        self.current_file_label.config(text=f"└─ {file_name}")
                    else:
                        self.current_file_label.config(text="")
                
                self.root.after(0, update)
            
            result = UnityVersionExtractor.extract_version(file_path, update_status)
            self.root.after(0, lambda: self._show_result(result))
        
        thread = threading.Thread(target=extract, daemon=True)
        thread.start()
    
    def _show_result(self, result):
        self.current_file_label.config(text="")
        self.progress_bar.set_progress(100)
        self.progress_percent_label.config(text="100%")
        
        if result['success']:
            self.file_icon.config(text="✅")
            self.status_label.config(text="✨ Unity version found!", fg=Theme.ACCENT_PRIMARY)
            
            version_text = f"Unity {result['version']}"
            self.result_label.config(text=version_text, fg=Theme.ACCENT_PRIMARY)
            
            if result['source_file']:
                source = os.path.basename(result['source_file'])
                self.details_label.config(text=f"📄 Found in: {source}")
            self._animate_result()
            
        elif result['is_unity'] and not result['success']:
            self.file_icon.config(text="⚠️")
            self.status_label.config(text="⚠️ Unity game detected", fg=Theme.TEXT_SECONDARY)
            self.result_label.config(
                text="Version Unknown",
                fg=Theme.TEXT_SECONDARY
            )
            self.details_label.config(
                text=result['error'] or "Could not determine Unity version"
            )
        else:
            self.file_icon.config(text="❌")
            self.status_label.config(text="❌ Analysis complete", fg=Theme.TEXT_MUTED)
            self.result_label.config(
                text="Not a Unity Game",
                fg="#ff6b6b"
            )
            self.details_label.config(
                text=result['error'] or "This APK is not a Unity-based game"
            )
    
    def _animate_result(self):
        """Animate the result display"""
        original_color = Theme.ACCENT_PRIMARY
        flash_color = "#ffffff"
        
        def flash(step=0):
            if step < 6:
                color = flash_color if step % 2 == 0 else original_color
                self.result_label.config(fg=color)
                self.root.after(100, lambda: flash(step + 1))
            else:
                self.result_label.config(fg=original_color)
        
        flash()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()
if __name__ == "__main__":
    app = PAUVFApp()
    app.run()
