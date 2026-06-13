import sys, os, subprocess, json
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QGridLayout, QTabWidget, QSlider, QCheckBox)
from PyQt6.QtCore import Qt

CONFIG_DIR = os.path.expanduser("~/.config/wangert_os")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

class WangertSettings(QWidget):
    def __init__(self):
        super().__init__()
        # Standardwerte
        self.cfg = {"chameleon": True, "alpha_panel": 65, "alpha_menu": 90}
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.cfg.update(json.load(f))
            except: pass
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Wangert OS Einstellungen")
        self.setFixedSize(600, 450)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; font-size: 14px; }
            QTabWidget::pane { border: 1px solid #45475a; border-radius: 8px; }
            QTabBar::tab { background: #313244; padding: 10px 20px; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected { background: #89b4fa; color: #11111b; font-weight: bold; }
            QPushButton.action-btn { background-color: #a6e3a1; color: #11111b; border-radius: 6px; padding: 12px; font-weight: bold; font-size: 14px; }
            QPushButton.action-btn:hover { background-color: #94e2d5; }
            QPushButton.tool-btn { background-color: #313244; border-radius: 8px; padding: 15px; text-align: left; font-size: 14px; }
            QPushButton.tool-btn:hover { background-color: #45475a; border: 1px solid #89b4fa; }
            QSlider::groove:horizontal { border-radius: 4px; height: 8px; background: #45475a; }
            QSlider::handle:horizontal { background: #89b4fa; width: 16px; margin: -4px 0; border-radius: 8px; }
        """)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()

        # TAB 1: Wangert OS Design
        tab_design = QWidget()
        d_layout = QVBoxLayout(tab_design)

        self.chk_cham = QCheckBox("🎨 Chameleon Design (Farbe automatisch aus Hintergrundbild saugen)")
        self.chk_cham.setChecked(self.cfg["chameleon"])
        d_layout.addWidget(self.chk_cham)

        d_layout.addSpacing(20)
        
        lbl_panel = QLabel(f"Taskleisten-Transparenz: {self.cfg['alpha_panel']}%")
        self.sld_panel = QSlider(Qt.Orientation.Horizontal)
        self.sld_panel.setRange(10, 100)
        self.sld_panel.setValue(self.cfg["alpha_panel"])
        self.sld_panel.valueChanged.connect(lambda v: lbl_panel.setText(f"Taskleisten-Transparenz: {v}%"))
        d_layout.addWidget(lbl_panel)
        d_layout.addWidget(self.sld_panel)

        d_layout.addSpacing(20)
        
        lbl_menu = QLabel(f"Menü-Transparenz (Startmenü/Kalender): {self.cfg['alpha_menu']}%")
        self.sld_menu = QSlider(Qt.Orientation.Horizontal)
        self.sld_menu.setRange(10, 100)
        self.sld_menu.setValue(self.cfg["alpha_menu"])
        self.sld_menu.valueChanged.connect(lambda v: lbl_menu.setText(f"Menü-Transparenz (Startmenü/Kalender): {v}%"))
        d_layout.addWidget(lbl_menu)
        d_layout.addWidget(self.sld_menu)

        d_layout.addStretch()
        btn_save = QPushButton("💾 Speichern & Taskleiste neu laden")
        btn_save.setProperty("class", "action-btn")
        btn_save.clicked.connect(self.save_and_apply)
        d_layout.addWidget(btn_save)

        tabs.addTab(tab_design, "✨ Design")

        # TAB 2: System Tools
        tab_sys = QWidget()
        s_layout = QGridLayout(tab_sys)

        def create_tool(icon, title, cmd):
            btn = QPushButton(f"{icon}  {title}")
            btn.setProperty("class", "tool-btn")
            btn.clicked.connect(lambda: subprocess.Popen(cmd.split()))
            return btn

        s_layout.addWidget(create_tool("🌐", "Netzwerk", "nm-connection-editor"), 0, 0)
        s_layout.addWidget(create_tool("🔊", "Audio", "pavucontrol"), 0, 1)
        s_layout.addWidget(create_tool("🖥️", "Monitore", "arandr"), 1, 0)
        s_layout.addWidget(create_tool("🎨", "Fenster-Inhalt", "lxappearance"), 1, 1)
        s_layout.addWidget(create_tool("🪟", "Fenster-Rahmen", "obconf"), 2, 0)
        s_layout.addWidget(create_tool("🖼️", "Hintergrund", "nitrogen"), 2, 1)
        tabs.addTab(tab_sys, "⚙️ System-Tools")

        layout.addWidget(tabs)

    def save_and_apply(self):
        # Speichert die Einstellungen
        self.cfg["chameleon"] = self.chk_cham.isChecked()
        self.cfg["alpha_panel"] = self.sld_panel.value()
        self.cfg["alpha_menu"] = self.sld_menu.value()

        if not os.path.exists(CONFIG_DIR): os.makedirs(CONFIG_DIR)
            
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.cfg, f)

        # Startet die Taskleiste blitzschnell neu, um die Farben zu übernehmen
        os.system("pkill -f wangert_panel.py")
        subprocess.Popen(["python3", "/opt/wangert_os/wangert_panel.py"])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("WangertSettings")
    app.setApplicationDisplayName("Wangert OS Einstellungen")
    window = WangertSettings()
    window.show()
    sys.exit(app.exec())
