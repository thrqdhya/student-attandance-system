import sys
import requests
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox, QStackedWidget, 
                             QFrame, QComboBox, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QColor

# CONFIG: Port 5001 sesuai app.py
BASE_URL = "http://127.0.0.1:5001"

class LecturerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance - Bartın University")
        self.setFixedSize(1150, 750)
        
        # =========================================================
        # 🎨 STYLE: THE ULTIMATE BLUE AESTHETIC
        # =========================================================
        self.setStyleSheet("""
            QMainWindow { background-color: #F8FAFC; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #1E293B; }
            
            /* Sidebar - Deep Navy Blue */
            QFrame#Sidebar {
                background-color: #0F172A;
                border-radius: 0px;
            }
            
            /* Main Content Cards */
            QFrame#ContentCard {
                background-color: #ffffff;
                border: 1px solid #E2E8F0;
                border-radius: 24px;
            }
            
            /* Inputs & Dropdown */
            QLineEdit, QComboBox {
                padding: 12px;
                background-color: #F1F5F9;
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                color: #1E293B;
            }
            QComboBox::drop-down { border: none; }

            /* Buttons - Royal & Sky Blue Combinations */
            QPushButton {
                background-color: #2563EB; /* Royal Blue */
                color: white;
                font-weight: 600;
                border-radius: 12px;
                padding: 14px;
                border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            
            QPushButton#StopBtn { 
                background-color: #EF4444; /* Aesthetic Red */
            }
            QPushButton#StopBtn:hover { background-color: #DC2626; }
            
            QPushButton#SecondaryBtn {
                background-color: #E0F2FE; /* Light Sky Blue */
                color: #0369A1;
                border: 1px solid #BAE6FD;
            }
            
            QLabel#SidebarName { color: #F8FAFC; font-size: 18px; font-weight: 700; }
            QLabel#SidebarSub { color: #94A3B8; font-size: 12px; }
            QLabel#StatValue { font-size: 82px; font-weight: 800; color: #2563EB; }
            QLabel#TimerLabel { font-size: 38px; font-weight: 700; color: #334155; font-family: 'Consolas', monospace; }
        """)

        self.session_id = None
        self.lecturer_id = None
        self.elapsed_seconds = 0
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_login_page()
        self.init_dashboard_page()

    def apply_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, 40))
        widget.setGraphicsEffect(shadow)

    # =========================================================
    # 1. LOGIN PAGE
    # =========================================================
    def init_login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignCenter)

        login_card = QFrame()
        login_card.setFixedSize(400, 520)
        login_card.setObjectName("ContentCard")
        self.apply_shadow(login_card)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setContentsMargins(50, 50, 50, 50)
        card_layout.setSpacing(18)

        brand = QLabel("Lecturer Portal")
        brand.setStyleSheet("font-size: 26px; font-weight: bold; color: #2563EB; margin-bottom: 20px;")
        brand.setAlignment(Qt.AlignCenter)

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.user_input.setText("admin")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setText("admin")

        btn_login = QPushButton("Log In")
        btn_login.clicked.connect(self.handle_login)

        card_layout.addWidget(brand)
        card_layout.addWidget(self.user_input)
        card_layout.addWidget(self.pass_input)
        card_layout.addWidget(btn_login)
        card_layout.addStretch()

        layout.addWidget(login_card)
        self.stacked_widget.addWidget(page)

    # =========================================================
    # 2. DASHBOARD PAGE
    # =========================================================
    def init_dashboard_page(self):
        self.dashboard_page = QWidget()
        main_layout = QHBoxLayout(self.dashboard_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Aesthetic Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(30, 50, 30, 30)

        # Profile Circle
        self.avatar = QLabel("RY")
        self.avatar.setFixedSize(60, 60)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; font-size: 20px; border-radius: 30px;")
        
        self.lbl_name = QLabel("Welcome")
        self.lbl_name.setObjectName("SidebarName")
        
        lbl_role = QLabel("Faculty Member")
        lbl_role.setObjectName("SidebarSub")

        side_layout.addWidget(self.avatar)
        side_layout.addSpacing(10)
        side_layout.addWidget(self.lbl_name)
        side_layout.addWidget(lbl_role)
        side_layout.addSpacing(40)

        side_layout.addWidget(QLabel("SELECT COURSE", styleSheet="color: #64748B; font-size: 10px; font-weight: bold; letter-spacing: 1px;"))
        self.course_box = QComboBox()
        side_layout.addWidget(self.course_box)

        side_layout.addStretch()

        self.btn_start = QPushButton("Start Session")
        self.btn_start.clicked.connect(self.start_attendance_session)
        
        self.btn_stop = QPushButton("Stop Session")
        self.btn_stop.setObjectName("StopBtn")
        self.btn_stop.clicked.connect(self.stop_attendance_session)
        self.btn_stop.hide()

        self.btn_export = QPushButton("Export to Excel")
        self.btn_export.setObjectName("SecondaryBtn")
        self.btn_export.clicked.connect(self.download_excel_report)
        self.btn_export.hide()

        side_layout.addWidget(self.btn_start)
        side_layout.addWidget(self.btn_stop)
        side_layout.addSpacing(10)
        side_layout.addWidget(self.btn_export)

        # --- Content Area ---
        content = QVBoxLayout()
        content.setContentsMargins(60, 60, 60, 60)
        
        self.lbl_status = QLabel("System idle")
        self.lbl_status.setStyleSheet("font-size: 18px; color: #94A3B8; font-weight: 500;")
        self.lbl_status.setAlignment(Qt.AlignCenter)

        # QR Display Card
        self.qr_card = QFrame()
        self.qr_card.setObjectName("ContentCard")
        self.qr_card.setFixedSize(420, 420)
        self.apply_shadow(self.qr_card)
        
        qr_layout = QVBoxLayout(self.qr_card)
        self.qr_display = QLabel("READY TO START")
        self.qr_display.setStyleSheet("color: #CBD5E1;")
        self.qr_display.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_display)

        # Elapsed Session Timer
        timer_box = QVBoxLayout()
        timer_box.setSpacing(5)
        self.lbl_session_clock = QLabel("00:00")
        self.lbl_session_clock.setObjectName("TimerLabel")
        self.lbl_session_clock.setAlignment(Qt.AlignCenter)
        
        lbl_clock_sub = QLabel("ELAPSED SESSION TIME")
        lbl_clock_sub.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: bold; letter-spacing: 1px;")
        lbl_clock_sub.setAlignment(Qt.AlignCenter)

        content.addWidget(self.lbl_status)
        content.addStretch()
        content.addWidget(self.qr_card, 0, Qt.AlignCenter)
        content.addSpacing(30)
        content.addWidget(self.lbl_session_clock)
        content.addWidget(lbl_clock_sub)
        content.addStretch()

        # --- Right Panel (Live Metrics) ---
        stats_panel = QFrame()
        stats_panel.setFixedWidth(280)
        stats_panel.setStyleSheet("background-color: #ffffff; border-left: 1px solid #E2E8F0;")
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(40, 60, 40, 40)

        stats_layout.addWidget(QLabel("LIVE ATTENDANCE", styleSheet="font-weight: bold; color: #64748B; font-size: 11px;"))
        self.lbl_hadir = QLabel("0")
        self.lbl_hadir.setObjectName("StatValue")
        stats_layout.addWidget(self.lbl_hadir)
        stats_layout.addWidget(QLabel("Students Present", styleSheet="color: #94A3B8; font-size: 14px;"))
        stats_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addLayout(content)
        main_layout.addWidget(stats_panel)

        self.stacked_widget.addWidget(self.dashboard_page)

    # =========================================================
    # ⚙️ LOGIC PERBAIKAN
    # =========================================================
    def handle_login(self):
        user = self.user_input.text()
        pw = self.pass_input.text()
        try:
            res = requests.post(f"{BASE_URL}/api/lecturer/login", json={"username": user, "password": pw})
            if res.status_code == 200:
                data = res.json()
                self.lecturer_id = data['id']
                self.lbl_name.setText(data['name'])
                self.course_box.clear()
                for c in data.get('courses', []):
                    self.course_box.addItem(c['name'], c['id'])
                self.stacked_widget.setCurrentIndex(1)
            else:
                QMessageBox.warning(self, "Failed", "Check credentials")
        except:
            QMessageBox.critical(self, "Error", "Backend disconnected")

    def start_attendance_session(self):
        c_id = self.course_box.currentData()
        try:
            res = requests.post(f"{BASE_URL}/api/session/start", 
                                json={"lecturer_id": self.lecturer_id, "course_id": c_id})
            if res.status_code == 201:
                self.session_id = res.json()['session_id']
                self.lbl_status.setText(f"Active Session: {self.course_box.currentText()}")
                
                self.btn_start.hide()
                self.btn_stop.show()
                self.btn_export.show()

                # --- 30s QR Refresh ---
                self.qr_timer = QTimer()
                self.qr_timer.timeout.connect(self.fetch_qr)
                self.qr_timer.start(30000) 

                # --- 5s Stats Refresh ---
                self.stats_timer = QTimer()
                self.stats_timer.timeout.connect(self.refresh_stats)
                self.stats_timer.start(5000)

                # --- 1s Session Clock ---
                self.elapsed_seconds = 0
                self.clock_timer = QTimer()
                self.clock_timer.timeout.connect(self.update_clock)
                self.clock_timer.start(1000)
                
                # 🔥 FIX CRITICAL: Beri jeda 500ms agar Backend selesai memproses file
                QTimer.singleShot(500, self.fetch_qr) 
        except:
            QMessageBox.warning(self, "Error", "Failed to start")

    def stop_attendance_session(self):
        """Menghentikan semua proses visual sesi"""
        if hasattr(self, 'qr_timer'): self.qr_timer.stop()
        if hasattr(self, 'stats_timer'): self.stats_timer.stop()
        if hasattr(self, 'clock_timer'): self.clock_timer.stop()
        
        self.qr_display.setPixmap(QPixmap())
        self.qr_display.setText("SESSION STOPPED")
        self.lbl_status.setText("Attendance closed")
        self.lbl_session_clock.setText("00:00")
        
        self.btn_stop.hide()
        self.btn_start.show()

    def update_clock(self):
        self.elapsed_seconds += 1
        m, s = divmod(self.elapsed_seconds, 60)
        self.lbl_session_clock.setText(f"{m:02d}:{s:02d}")

    def fetch_qr(self):
        try:
            response = requests.get(f"{BASE_URL}/qr-live", stream=True)
            if response.status_code == 200:
                qimage = QImage.fromData(response.content)
                pixmap = QPixmap.fromImage(qimage).scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_display.setPixmap(pixmap)
                self.qr_display.setText("")
        except: pass

    def refresh_stats(self):
        try:
            res = requests.get(f"{BASE_URL}/api/stats/lecturer/{self.session_id}")
            if res.status_code == 200:
                self.lbl_hadir.setText(str(res.json()['data']['statistik']['hadir']))
        except: pass

    def download_excel_report(self):
        try:
            res = requests.get(f"{BASE_URL}/api/report/export/{self.session_id}")
            if res.status_code == 200:
                fn = f"Attendance_Report_{self.session_id}.xlsx"
                with open(fn, "wb") as f: f.write(res.content)
                os.startfile(os.getcwd())
        except: pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LecturerApp()
    window.show()
    sys.exit(app.exec())