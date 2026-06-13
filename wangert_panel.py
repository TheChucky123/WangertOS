import sys, os, subprocess, json, getpass
from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout,
                             QPushButton, QLabel, QScrollArea, QMenu, QCalendarWidget, QFrame)
from PyQt6.QtCore import Qt, QTimer, QSize, QPoint, QEvent
from PyQt6.QtGui import QFont, QIcon, QAction, QImage, QColor, QPixmap
from datetime import datetime

# ==========================================
# 1. EINSTELLUNGEN & THEME ENGINE
# ==========================================
CONFIG_DIR = os.path.expanduser("~/.config/wangert_os")
PINNED_FILE = os.path.join(CONFIG_DIR, "pinned.json")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PINNED_CACHE = None 

def load_config():
    cfg = {"chameleon": True, "alpha_panel": 65, "alpha_menu": 90}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f: cfg.update(json.load(f))
        except: pass
    return cfg

CFG = load_config()

def get_wallpaper_color():
    base_r, base_g, base_b = 30, 30, 46 
    if not CFG["chameleon"]: return (base_r, base_g, base_b), (137, 180, 250)

    bg_path = "/usr/share/backgrounds/wangert/wangert_bg.jpg"
    try:
        nitro_cfg = os.path.expanduser("~/.config/nitrogen/bg-saved.cfg")
        if os.path.exists(nitro_cfg):
            with open(nitro_cfg, "r") as f:
                for line in f:
                    if line.startswith("file="): bg_path = line.split("=")[1].strip()
    except: pass

    if os.path.exists(bg_path):
        img = QImage(bg_path)
        if not img.isNull():
            avg_color = img.scaled(1, 1).pixelColor(0, 0)
            r = int((avg_color.red() * 0.2) + (15 * 0.8))
            g = int((avg_color.green() * 0.2) + (15 * 0.8))
            b = int((avg_color.blue() * 0.2) + (20 * 0.8))
            hr = min(255, r + 60)
            hg = min(255, g + 70)
            hb = min(255, b + 70)
            return (r, g, b), (hr, hg, hb)
    return (base_r, base_g, base_b), (137, 180, 250)

(R, G, B), (HR, HG, HB) = get_wallpaper_color()
alpha_p, alpha_m = CFG["alpha_panel"] / 100.0, CFG["alpha_menu"] / 100.0

PANEL_BG = f"rgba({R}, {G}, {B}, {alpha_p})"
MENU_BG = f"rgba({R}, {G}, {B}, {alpha_m})"
HIGHLIGHT = f"rgb({HR}, {HG}, {HB})"
HOVER_BG = f"rgba(255, 255, 255, 0.1)"
TEXT_COLOR = "#ffffff"

def load_pinned():
    global PINNED_CACHE
    if PINNED_CACHE is not None: return PINNED_CACHE 
    if os.path.exists(PINNED_FILE):
        try:
            with open(PINNED_FILE, "r") as f:
                PINNED_CACHE = json.load(f)
                return PINNED_CACHE
        except: pass
    PINNED_CACHE = [{"name": "Terminal", "exec": "terminator", "icon": "utilities-terminal"}]
    return PINNED_CACHE

def save_pinned(pinned_list):
    global PINNED_CACHE
    PINNED_CACHE = pinned_list
    with open(PINNED_FILE, "w") as f: json.dump(pinned_list, f)

def get_app_info():
    apps = {}
    app_dirs = ["/usr/share/applications", os.path.expanduser("~/.local/share/applications")]
    for app_dir in app_dirs:
        if not os.path.exists(app_dir): continue
        for filename in os.listdir(app_dir):
            if not filename.endswith(".desktop"): continue
            filepath = os.path.join(app_dir, filename)
            name, exec_cmd, icon, wm_class = "", "", "", ""
            actions = {}
            current_action, skip_app = None, False
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("NoDisplay=true") or line.startswith("Hidden=true"):
                            skip_app = True; break
                        if line.startswith("[Desktop Action"):
                            current_action = line[16:-1]
                            actions[current_action] = {"name": current_action, "exec": ""}
                        elif current_action:
                            if line.startswith("Name="): actions[current_action]["name"] = line[5:]
                            elif line.startswith("Exec="): actions[current_action]["exec"] = line[5:].split(" %")[0]
                        else:
                            if line.startswith("Name=") and not name: name = line[5:]
                            elif line.startswith("Exec=") and not exec_cmd: exec_cmd = line[5:].split(" %")[0]
                            elif line.startswith("Icon=") and not icon: icon = line[5:]
                            elif line.startswith("StartupWMClass="): wm_class = line[15:].lower()
                if name and exec_cmd and not skip_app:
                    key = wm_class if wm_class else filename.replace(".desktop", "").lower()
                    apps[key] = {"name": name, "exec": exec_cmd, "icon": icon, "actions": actions}
            except: pass
    return apps

APP_DB = get_app_info()

def find_app_by_wmclass(wm_class):
    wm_class = wm_class.lower()
    for key, info in APP_DB.items():
        if key in wm_class or wm_class in key: return info
    return None

class AutoCloseMenu(QWidget):
    def event(self, e):
        if e.type() == QEvent.Type.WindowDeactivate:
            self.hide()
        return super().event(e)

# ==========================================
# 2. NEU: HIER IST DIE AKKU-LOGIK
# ==========================================
def get_battery_info():
    try:
        base_path = "/sys/class/power_supply"
        if not os.path.exists(base_path): return ""
        for ps in os.listdir(base_path):
            if ps.startswith("BAT"):
                cap_path = os.path.join(base_path, ps, "capacity")
                stat_path = os.path.join(base_path, ps, "status")
                if os.path.exists(cap_path) and os.path.exists(stat_path):
                    with open(cap_path, "r") as f: cap = f.read().strip()
                    with open(stat_path, "r") as f: stat = f.read().strip()
                    
                    # Status ermitteln (Laden / Entladen)
                    icon = "🔋"
                    status_str = ""
                    if stat == "Charging": status_str = " ⚡"
                    elif stat == "Full" or stat == "Not charging": status_str = " 🔌"
                    
                    return f"{icon} {cap}%{status_str}"
    except: pass
    return ""

def has_hardware(hw_type):
    try:
        output = subprocess.check_output(['rfkill', 'list', hw_type]).decode('utf-8')
        return len(output.strip()) > 0
    except: return False

class NetworkMenu(AutoCloseMenu):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setFixedSize(280, 220)
        self.setStyleSheet(f"QWidget {{ background-color: {MENU_BG}; color: {TEXT_COLOR}; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); font-family: 'Segoe UI'; }} QPushButton {{ background-color: {HOVER_BG}; border: 1px solid rgba(255,255,255,0.05); padding: 12px; font-size: 14px; border-radius: 8px; font-weight: bold; text-align: left; }} QPushButton:hover {{ background-color: {HIGHLIGHT}; color: #11111b; }} QLabel {{ font-size: 16px; font-weight: bold; border: none; background: transparent; padding-bottom: 5px; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.addWidget(QLabel("🌐 Verbindungen"))
        hw_wifi, hw_bt = has_hardware('wlan'), has_hardware('bluetooth')

        if hw_wifi:
            self.btn_wifi = QPushButton("📶 WLAN an/aus")
            self.btn_wifi.clicked.connect(lambda: os.system("nmcli radio wifi | grep -q 'enabled' && nmcli radio wifi off || nmcli radio wifi on"))
            layout.addWidget(self.btn_wifi)
        if hw_bt:
            self.btn_bt = QPushButton("ᛒ Bluetooth an/aus")
            self.btn_bt.clicked.connect(lambda: os.system("rfkill list bluetooth | grep -q 'Soft blocked: yes' && rfkill unblock bluetooth || rfkill block bluetooth"))
            layout.addWidget(self.btn_bt)
        if not hw_wifi and not hw_bt:
            lbl_no_hw = QLabel("Nur Ethernet (Kabelverbindung)")
            lbl_no_hw.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 13px; font-weight: normal;")
            layout.addWidget(lbl_no_hw)
        layout.addStretch()
        btn_settings = QPushButton("⚙️ Netzwerk-Details")
        btn_settings.clicked.connect(lambda: os.system("nm-connection-editor &"))
        layout.addWidget(btn_settings)

class CalendarMenu(AutoCloseMenu):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setFixedSize(320, 380)
        self.setStyleSheet(f"QWidget {{ background-color: {MENU_BG}; color: {TEXT_COLOR}; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }} QLabel#big_clock {{ font-size: 36px; font-weight: bold; color: {HIGHLIGHT}; border: none; padding-bottom: 5px; background: transparent; }} QLabel#date_text {{ font-size: 14px; color: rgba(255,255,255,0.7); border: none; padding-bottom: 15px; background: transparent; }} QCalendarWidget QWidget {{ alternate-background-color: rgba(255,255,255,0.05); background: transparent; }} QCalendarWidget QAbstractItemView:enabled {{ color: {TEXT_COLOR}; background-color: transparent; selection-background-color: {HIGHLIGHT}; selection-color: #ffffff; border-radius: 5px; }} QCalendarWidget QToolButton {{ color: {TEXT_COLOR}; background-color: transparent; border: none; font-weight: bold; font-size: 14px; }} QCalendarWidget QToolButton:hover {{ background-color: {HOVER_BG}; border-radius: 4px; }}")
        layout = QVBoxLayout(self)
        self.lbl_big_clock, self.lbl_date_text = QLabel(), QLabel()
        self.lbl_big_clock.setObjectName("big_clock"); self.lbl_date_text.setObjectName("date_text")
        self.lbl_big_clock.setAlignment(Qt.AlignmentFlag.AlignCenter); self.lbl_date_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_big_clock); layout.addWidget(self.lbl_date_text)
        self.calendar = QCalendarWidget(); self.calendar.setGridVisible(False); layout.addWidget(self.calendar)
        self.timer = QTimer(self); self.timer.timeout.connect(self.update_time); self.timer.start(1000); self.update_time()

    def update_time(self):
        self.lbl_big_clock.setText(datetime.now().strftime("%H:%M:%S")); self.lbl_date_text.setText(datetime.now().strftime("%A, %d. %B %Y"))

class ControlCenter(AutoCloseMenu):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setFixedSize(300, 150)
        self.setStyleSheet(f"QWidget {{ background-color: {MENU_BG}; color: {TEXT_COLOR}; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); font-family: 'Segoe UI'; }} QPushButton {{ background-color: {HOVER_BG}; border: 1px solid rgba(255,255,255,0.05); padding: 12px; font-size: 14px; border-radius: 8px; font-weight: bold; }} QPushButton:hover {{ background-color: {HIGHLIGHT}; color: #ffffff; }} QLabel {{ font-size: 16px; font-weight: bold; border: none; background: transparent; }}")
        layout = QVBoxLayout(self); layout.setContentsMargins(15, 15, 15, 15); layout.addWidget(QLabel("🎛️ Audio Steuerung"))
        grid = QGridLayout()
        btn_vol_down = QPushButton("🔉 Leiser"); btn_vol_down.clicked.connect(lambda: os.system("amixer -D pulse sset Master 5%-"))
        btn_vol_up = QPushButton("🔊 Lauter"); btn_vol_up.clicked.connect(lambda: os.system("amixer -D pulse sset Master 5%+"))
        grid.addWidget(btn_vol_down, 0, 0); grid.addWidget(btn_vol_up, 0, 1); layout.addLayout(grid)

class StartMenu(AutoCloseMenu):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setFixedSize(350, 600)
        self.setStyleSheet(f"QWidget {{ background-color: {MENU_BG}; color: {TEXT_COLOR}; font-family: 'Segoe UI', Arial; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); }} QLabel {{ font-weight: bold; color: {HIGHLIGHT}; padding-top: 15px; padding-bottom: 5px; border: none; font-size: 12px; background: transparent; }} QPushButton.app-btn {{ background-color: transparent; border: none; border-left: 3px solid transparent; text-align: left; padding: 10px 15px; font-size: 14px; border-radius: 6px; }} QPushButton.app-btn:hover {{ background-color: {HOVER_BG}; border-left: 3px solid {HIGHLIGHT}; }} QPushButton.pwr-btn {{ background-color: transparent; border: none; font-size: 18px; padding: 10px; border-radius: 8px; }} QPushButton.pwr-btn:hover {{ background-color: {HOVER_BG}; color: {HIGHLIGHT}; }} QScrollArea {{ border: none; background-color: transparent; }} QScrollBar:vertical {{ border: none; background-color: transparent; width: 6px; margin: 0px; }} QScrollBar::handle:vertical {{ background-color: rgba(255,255,255,0.2); border-radius: 3px; min-height: 30px; }} QScrollBar::handle:vertical:hover {{ background-color: {HIGHLIGHT}; }}")
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(15, 15, 15, 15)
        
        user_layout = QHBoxLayout(); lbl_pic = QLabel(); lbl_pic.setFixedSize(40, 40)
        lbl_pic.setStyleSheet("background-color: rgba(255,255,255,0.1); border-radius: 20px;"); lbl_pic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        face_path = os.path.expanduser("~/.face")
        if os.path.exists(face_path): lbl_pic.setPixmap(QPixmap(face_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation))
        else: lbl_pic.setText("👤"); lbl_pic.setStyleSheet("font-size: 24px; background: transparent; border: none;")
        lbl_name = QLabel(getpass.getuser().capitalize()); lbl_name.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT_COLOR}; border: none; background: transparent; padding-left: 10px;")
        user_layout.addWidget(lbl_pic); user_layout.addWidget(lbl_name); user_layout.addStretch(); main_layout.addLayout(user_layout)
        
        line_top = QFrame(); line_top.setFrameShape(QFrame.Shape.HLine); line_top.setStyleSheet("background-color: rgba(255,255,255,0.1); border: none; max-height: 1px; margin-top: 10px; margin-bottom: 5px;"); main_layout.addWidget(line_top)

        scroll_area = QScrollArea(); scroll_area.setWidgetResizable(True); scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_content = QWidget(); scroll_content.setStyleSheet("background-color: transparent; border: none;"); self.scroll_layout = QVBoxLayout(scroll_content); self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.load_applications(); scroll_area.setWidget(scroll_content); main_layout.addWidget(scroll_area)

        line_bot = QFrame(); line_bot.setFrameShape(QFrame.Shape.HLine); line_bot.setStyleSheet("background-color: rgba(255,255,255,0.1); border: none; max-height: 1px; margin-top: 10px; margin-bottom: 10px;"); main_layout.addWidget(line_bot)

        bot_layout = QHBoxLayout(); bot_layout.setContentsMargins(0, 0, 0, 0)
        btn_settings = QPushButton("⚙️ Einstellungen"); btn_settings.setProperty("class", "app-btn"); btn_settings.clicked.connect(lambda: self.launch_app("python3 /opt/wangert_os/wangert_settings.py"))
        bot_layout.addWidget(btn_settings); bot_layout.addStretch()
        
        btn_sleep = QPushButton("🌙"); btn_sleep.setProperty("class", "pwr-btn"); btn_sleep.clicked.connect(lambda: subprocess.Popen(["systemctl", "suspend"]))
        btn_reboot = QPushButton("🔄"); btn_reboot.setProperty("class", "pwr-btn"); btn_reboot.clicked.connect(lambda: subprocess.Popen(["systemctl", "reboot"]))
        btn_power = QPushButton("🔌"); btn_power.setProperty("class", "pwr-btn"); btn_power.clicked.connect(lambda: subprocess.Popen(["systemctl", "poweroff"]))
        bot_layout.addWidget(btn_sleep); bot_layout.addWidget(btn_reboot); bot_layout.addWidget(btn_power); main_layout.addLayout(bot_layout)

    def load_applications(self):
        apps = {"Internet": [], "Multimedia": [], "System": [], "Zubehör": [], "Sonstige": []}
        for key, info in APP_DB.items():
            cat = "Sonstige"
            exec_str = info["exec"].lower()
            if any(x in exec_str for x in ["firefox", "chrome", "network", "web"]): cat = "Internet"
            elif any(x in exec_str for x in ["pavucontrol", "audio", "video", "vlc"]): cat = "Multimedia"
            elif any(x in exec_str for x in ["obconf", "settings", "lxappearance"]): cat = "System"
            elif any(x in exec_str for x in ["term", "nano", "editor"]): cat = "Zubehör"
            apps[cat].append(info)

        for category, app_list in apps.items():
            if app_list:
                self.scroll_layout.addWidget(QLabel(category.upper()))
                for app in sorted(app_list, key=lambda x: x["name"]):
                    btn = QPushButton(f"  {app['name']}")
                    btn.setProperty("class", "app-btn")
                    btn.clicked.connect(lambda checked, cmd=app["exec"]: self.launch_app(cmd))
                    self.scroll_layout.addWidget(btn)

    def launch_app(self, command):
        try: subprocess.Popen(command.split()); self.hide()
        except: pass

class TaskButton(QPushButton):
    def __init__(self, win_id, title, wm_class, panel_ref, is_pinned=False, app_info=None):
        super().__init__()
        self.win_id, self.app_info, self.is_pinned, self.panel_ref = win_id, (app_info or find_app_by_wmclass(wm_class)), is_pinned, panel_ref
        if self.app_info and self.app_info.get("icon"):
            QIcon.setThemeName("Papirus"); self.setIcon(QIcon.fromTheme(self.app_info["icon"])); self.setIconSize(QSize(22, 22))
            self.setText(f" {self.app_info['name'][:15]}")
        else: self.setText(f" {title[:15]}")
        self.setProperty("class", "pinned" if is_pinned else "task")
        self.clicked.connect(self.action); self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu); self.customContextMenuRequested.connect(self.show_context_menu)

    def action(self):
        if self.win_id: os.system(f"wmctrl -i -a {self.win_id}")
        elif self.app_info: subprocess.Popen(self.app_info["exec"].split())

    def show_context_menu(self, pos):
        self.panel_ref.is_menu_open = True
        menu = QMenu(self)
        menu.setStyleSheet(f"QMenu {{ background-color: {MENU_BG}; color: {TEXT_COLOR}; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 5px; }} QMenu::item {{ padding: 10px 25px; border-radius: 6px; }} QMenu::item:selected {{ background-color: {HIGHLIGHT}; color: #ffffff; font-weight: bold; }}")
        if self.app_info and self.app_info.get("actions"):
            for act_key, act_data in self.app_info["actions"].items():
                action = QAction(f"✨ {act_data['name']}", self)
                action.triggered.connect(lambda checked, cmd=act_data['exec']: subprocess.Popen(cmd.split()))
                menu.addAction(action)
            menu.addSeparator()
        if self.app_info:
            pin_action = QAction("📌 Lösen" if self.is_pinned else "📌 Anheften", self)
            pin_action.triggered.connect(self.toggle_pin)
            menu.addAction(pin_action)
        if self.win_id:
            menu.addSeparator()
            close_action = QAction("❌ Schließen", self)
            close_action.triggered.connect(lambda: os.system(f"wmctrl -i -c {self.win_id}"))
            menu.addAction(close_action)
        menu.adjustSize()
        menu.exec(QPoint(int(self.mapToGlobal(QPoint(0, 0)).x()), int(self.panel_ref.y() - menu.height() - 5)))
        self.panel_ref.is_menu_open = False

    def toggle_pin(self):
        pinned = load_pinned()
        if any(p["exec"] == self.app_info["exec"] for p in pinned): pinned = [p for p in pinned if p["exec"] != self.app_info["exec"]]
        else: pinned.append({"name": self.app_info["name"], "exec": self.app_info["exec"], "icon": self.app_info["icon"]})
        save_pinned(pinned); self.panel_ref.last_state = ""; self.panel_ref.update_system()

class WangertPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WangertPanel_Ignore")
        self.is_menu_open = False 
        self.menu_start, self.menu_calendar, self.menu_ctrl, self.menu_net = StartMenu(), CalendarMenu(), ControlCenter(), NetworkMenu()
        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setFixedHeight(50) 
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet(f"QWidget {{ font-family: 'Segoe UI', Arial; font-size: 14px; color: {TEXT_COLOR}; }} #main_panel {{ background-color: {PANEL_BG}; }} QPushButton#start_btn {{ background-color: {HIGHLIGHT}; color: #ffffff; border-radius: 8px; padding: 6px 20px; font-weight: bold; font-size: 16px; margin: 6px; }} QPushButton#start_btn:hover {{ background-color: {HOVER_BG}; border: 1px solid {HIGHLIGHT}; }} QPushButton.pinned {{ background-color: transparent; border: none; border-radius: 8px; padding: 6px 12px; margin: 6px; }} QPushButton.pinned:hover {{ background-color: {HOVER_BG}; }} QPushButton.task {{ background-color: {HOVER_BG}; border: none; border-bottom: 3px solid {HIGHLIGHT}; border-radius: 8px; border-bottom-left-radius: 2px; border-bottom-right-radius: 2px; padding: 6px 15px; margin: 6px; }} QPushButton.task:hover {{ background-color: rgba(255,255,255,0.2); }} QPushButton#sys_tray {{ background-color: transparent; border-radius: 8px; padding: 4px 12px; margin: 6px; font-weight: bold; }} QPushButton#sys_tray:hover {{ background-color: {HOVER_BG}; }}")
        self.bg_widget = QWidget(self); self.bg_widget.setObjectName("main_panel")
        self.main_layout = QHBoxLayout(self.bg_widget); self.main_layout.setContentsMargins(10, 0, 10, 0); self.main_layout.setSpacing(4)
        outer_layout = QVBoxLayout(self); outer_layout.setContentsMargins(0, 0, 0, 0); outer_layout.addWidget(self.bg_widget)

        self.btn_start = QPushButton("⊞ Wangert"); self.btn_start.setObjectName("start_btn"); self.btn_start.clicked.connect(self.toggle_start); self.main_layout.addWidget(self.btn_start)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.VLine); sep.setStyleSheet("color: rgba(255,255,255,0.1); margin: 12px 5px;"); self.main_layout.addWidget(sep)
        self.tasks_layout = QHBoxLayout(); self.tasks_layout.setContentsMargins(0,0,0,0); self.tasks_layout.setSpacing(2); self.main_layout.addLayout(self.tasks_layout); self.main_layout.addStretch()
        
        # SYS-TRAY BUTTONS
        self.btn_bat = QPushButton("") # Neuer Akku-Button
        self.btn_bat.setObjectName("sys_tray")
        self.main_layout.addWidget(self.btn_bat)

        self.btn_net = QPushButton("🌐"); self.btn_net.setObjectName("sys_tray"); self.btn_net.clicked.connect(self.toggle_net); self.main_layout.addWidget(self.btn_net)
        self.btn_ctrl = QPushButton("🎛️"); self.btn_ctrl.setObjectName("sys_tray"); self.btn_ctrl.clicked.connect(self.toggle_ctrl); self.main_layout.addWidget(self.btn_ctrl)
        self.btn_clock = QPushButton(); self.btn_clock.setObjectName("sys_tray"); self.btn_clock.clicked.connect(self.toggle_calendar); self.main_layout.addWidget(self.btn_clock)

        self.timer = QTimer(self); self.timer.timeout.connect(self.update_system); self.timer.start(1000); self.update_system()

    def update_system(self):
        self.btn_clock.setText(datetime.now().strftime("%H:%M\n%d.%m."))
        
        # 1. AKKU AKTUALISIEREN
        bat_info = get_battery_info()
        if bat_info:
            self.btn_bat.setText(bat_info)
            self.btn_bat.show()
        else:
            self.btn_bat.hide() # Unsichtbar wenn kein Akku da ist (z.B. in der VM)
        
        # 2. NETZWERK ERKENNUNG (Patched)
        try:
            route = subprocess.check_output(['ip', 'route']).decode('utf-8')
            if "default" in route:
                if "wlan" in route or "wlp" in route: self.btn_net.setText("📶")
                else: self.btn_net.setText("🔌")
            else: self.btn_net.setText("✈️")
        except: pass

        if getattr(self, 'is_menu_open', False): return
        try: output = subprocess.check_output(['wmctrl', '-lx']).decode('utf-8')
        except: output = ""
        
        pinned_apps = load_pinned()
        current_state = output + str(len(pinned_apps)) 
        if getattr(self, 'last_state', None) == current_state: return 
        self.last_state = current_state

        open_windows = []
        for line in output.strip().split('\n'):
            if not line: continue
            parts = line.split(maxsplit=4)
            if len(parts) >= 5:
                win_id, wm_class, win_title = parts[0], parts[2], parts[4]
                if "Wangert" not in wm_class and win_title != "Desktop":
                    open_windows.append((win_id, wm_class.split('.')[-1] if '.' in wm_class else wm_class, win_title))

        for i in reversed(range(self.tasks_layout.count())): 
            w = self.tasks_layout.itemAt(i).widget()
            if w: w.deleteLater()

        open_execs = [find_app_by_wmclass(w[1])["exec"] for w in open_windows if find_app_by_wmclass(w[1])]
        for app in pinned_apps:
            if app["exec"] not in open_execs: self.tasks_layout.addWidget(TaskButton(None, app["name"], "", self, True, app))
        for win_id, wm_class, win_title in open_windows:
            app_info = find_app_by_wmclass(wm_class)
            self.tasks_layout.addWidget(TaskButton(win_id, win_title, wm_class, self, (app_info and any(p["exec"] == app_info["exec"] for p in pinned_apps)), app_info))

    def toggle_start(self): self.menu_start.move(10, self.y() - self.menu_start.height() - 10); self.menu_start.show() if not self.menu_start.isVisible() else self.menu_start.hide()
    def toggle_calendar(self): self.menu_calendar.move(QApplication.primaryScreen().geometry().width() - self.menu_calendar.width() - 10, self.y() - self.menu_calendar.height() - 10); self.menu_calendar.show() if not self.menu_calendar.isVisible() else self.menu_calendar.hide()
    def toggle_ctrl(self): self.menu_ctrl.move(QApplication.primaryScreen().geometry().width() - self.menu_ctrl.width() - 120, self.y() - self.menu_ctrl.height() - 10); self.menu_ctrl.show() if not self.menu_ctrl.isVisible() else self.menu_ctrl.hide()
    def toggle_net(self): self.menu_net.move(QApplication.primaryScreen().geometry().width() - self.menu_net.width() - 160, self.y() - self.menu_net.height() - 10); self.menu_net.show() if not self.menu_net.isVisible() else self.menu_net.hide()

    def showEvent(self, event): self.setGeometry(0, QApplication.primaryScreen().geometry().height() - 50, QApplication.primaryScreen().geometry().width(), 50)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("WangertPanel_Ignore")
    app.setApplicationDisplayName("Wangert OS Taskbar")
    QIcon.setThemeName("Papirus")
    panel = WangertPanel()
    panel.show()
    sys.exit(app.exec())