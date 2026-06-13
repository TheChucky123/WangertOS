import sys, os, subprocess
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFrame)
from PyQt6.QtCore import Qt

class WangertUpdater(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Wangert OS Update Center")
        self.setFixedSize(450, 350)
        self.setStyleSheet("""
            QWidget { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', Arial; font-size: 14px; }
            QLabel#title { font-size: 20px; font-weight: bold; color: #89b4fa; padding-bottom: 10px; }
            QLabel#desc { color: #a6adc8; padding-bottom: 20px; }
            QPushButton { background-color: #313244; border: 1px solid #45475a; border-radius: 8px; padding: 15px; font-weight: bold; font-size: 14px; text-align: left; }
            QPushButton:hover { background-color: #45475a; border: 1px solid #89b4fa; }
            QPushButton#main_btn { background-color: #a6e3a1; color: #11111b; text-align: center; }
            QPushButton#main_btn:hover { background-color: #94e2d5; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("🔄 Update Center")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Halte Wangert OS auf dem neuesten Stand.\nInstalliere Sicherheitsupdates und neue System-Features.")
        desc.setObjectName("desc")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc)

        # Button 1: Normale System-Updates
        btn_sys = QPushButton("📦 1. App- und Sicherheits-Updates installieren")
        # Öffnet das Terminal, führt apt aus und wartet am Ende auf Tastendruck
        cmd_sys = 'terminator -e "echo \'Suche nach Updates...\'; sudo apt update && sudo apt upgrade -y; echo \'\n✅ Updates abgeschlossen! Drücke ENTER zum Schließen.\'; read"'
        btn_sys.clicked.connect(lambda: os.system(cmd_sys))
        layout.addWidget(btn_sys)

        layout.addSpacing(10)

        # Button 2: Wangert OS System-Code Updates (Via GitHub)
        btn_os = QPushButton("✨ 2. Wangert OS Kern-Update suchen")
        # HIER KOMMT SPÄTER DEIN GITHUB-LINK REIN! 
        # Aktuell ist es ein Platzhalter, der zeigt, wie es funktioniert.
        cmd_os = 'terminator -e "echo \'Verbinde mit Wangert Servern...\'; sleep 2; echo \'Lade neueste Features herunter...\'; sleep 2; echo \'\nDu bist auf dem neuesten Stand!\'; echo \'Drücke ENTER zum Schließen.\'; read"'
        btn_os.clicked.connect(lambda: os.system(cmd_os))
        layout.addWidget(btn_os)

        layout.addStretch()

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #45475a; border: none; max-height: 1px;")
        layout.addWidget(line)
        
        layout.addSpacing(10)

        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.close)
        btn_close.setStyleSheet("background-color: transparent; border: none; text-align: center; color: #f38ba8;")
        layout.addWidget(btn_close)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("WangertUpdater")
    window = WangertUpdater()
    window.show()
    sys.exit(app.exec())
