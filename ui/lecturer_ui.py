import sys
import os
import requests
import time
import qrcode
from io import BytesIO
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QMessageBox, QStackedWidget, 
                             QFrame, QComboBox, QGraphicsDropShadowEffect, QProgressBar,
                             QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QImage, QColor

BASE_URL = "http://127.0.0.1:5001"

class LecturerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance - Bartın University")
        self.setFixedSize(1150, 750)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #F8FAFC; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #1E293B; }
            QFrame#Sidebar { background-color: #0F172A; border-radius: 0px; }
            QFrame#ContentCard { background-color: #ffffff; border: 1px solid #E2E8F0; border-radius: 24px; }
            QFrame#QRPlaceholder { background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; }
            QFrame#MetricCard { background-color: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 16px; }
            
            QListWidget { background-color: transparent; border: none; outline: none; }
            QListWidget::item { background-color: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; padding: 12px; margin-bottom: 8px; color: #334155; }
            QListWidget::item:selected { background-color: #E0F2FE; border: 1px solid #7DD3FC; color: #0369A1; }

            QLineEdit, QComboBox { padding: 12px; background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 12px; color: #1E293B; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #ffffff; color: #1E293B; selection-background-color: #2563EB; selection-color: white; border: 1px solid #E2E8F0; border-radius: 8px; outline: none; }
            
            QPushButton { background-color: #2563EB; color: white; font-weight: 600; border-radius: 12px; padding: 14px; border: none; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton#StopBtn { background-color: #EF4444; }
            QPushButton#StopBtn:hover { background-color: #DC2626; }
            QPushButton#SecondaryBtn { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
            
            QLabel#SidebarName { color: #F8FAFC; font-size: 18px; font-weight: 700; }
            QLabel#TimerLabel { font-size: 42px; font-weight: 700; color: #334155; font-family: 'Consolas', monospace; letter-spacing: 2px;}
            
            QProgressBar { background-color: #E2E8F0; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #2563EB; border-radius: 4px; }
            QProgressBar#ProgressUrgent::chunk { background-color: #EF4444; }
        """)

        self.session_id = None
        self.lecturer_id = None
        self.remaining_seconds = 300 
        self.last_hadir_count = 0 
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_login_page()
        self.init_dashboard_page()

    def apply_shadow(self, widget, blur=30, opacity=30):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setXOffset(0)
        shadow.setYOffset(10)
        shadow.setColor(QColor(0, 0, 0, opacity))
        widget.setGraphicsEffect(shadow)

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

    def init_dashboard_page(self):
        self.dashboard_page = QWidget()
        main_layout = QHBoxLayout(self.dashboard_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # KIRI: SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(270)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(30, 50, 30, 30)

        avatar_layout = QHBoxLayout()
        self.avatar = QLabel("RY")
        self.avatar.setFixedSize(80, 80)
        self.avatar.setAlignment(Qt.AlignCenter)
        self.avatar.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; font-size: 28px; border-radius: 40px;")
        avatar_layout.addStretch()
        avatar_layout.addWidget(self.avatar)
        avatar_layout.addStretch()
        
        self.lbl_welcome = QLabel("Welcome Back,")
        self.lbl_welcome.setStyleSheet("color: #94A3B8; font-size: 13px; margin-top: 10px;")
        self.lbl_welcome.setAlignment(Qt.AlignCenter)

        self.lbl_name = QLabel("Loading...")
        self.lbl_name.setObjectName("SidebarName")
        self.lbl_name.setAlignment(Qt.AlignCenter)

        side_layout.addLayout(avatar_layout)
        side_layout.addWidget(self.lbl_welcome)
        side_layout.addWidget(self.lbl_name)
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

        # TENGAH: CONTENT
        content = QVBoxLayout()
        content.setContentsMargins(60, 50, 60, 50)
        
        self.lbl_status = QLabel("🟢 System Idle")
        self.lbl_status.setStyleSheet("font-size: 16px; color: #64748B; font-weight: 600; letter-spacing: 0.5px;")
        self.lbl_status.setAlignment(Qt.AlignCenter)

        self.qr_card_container = QFrame()
        self.qr_card_container.setObjectName("ContentCard")
        self.qr_card_container.setFixedSize(440, 440)
        self.apply_shadow(self.qr_card_container)
        
        qr_layout = QVBoxLayout(self.qr_card_container)
        qr_layout.setContentsMargins(20, 20, 20, 20)

        self.qr_display = QLabel()
        self.qr_display.setObjectName("QRPlaceholder")
        self.qr_display.setText("📷\n\nSESSION CLOSED")
        self.qr_display.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 16px;")
        self.qr_display.setAlignment(Qt.AlignCenter)
        qr_layout.addWidget(self.qr_display)

        self.lbl_session_clock = QLabel("00:00")
        self.lbl_session_clock.setObjectName("TimerLabel")
        self.lbl_session_clock.setAlignment(Qt.AlignCenter)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 300)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedSize(200, 8)
        
        prog_layout = QHBoxLayout()
        prog_layout.addStretch()
        prog_layout.addWidget(self.progress_bar)
        prog_layout.addStretch()

        lbl_clock_sub = QLabel("SESSION TIME REMAINING")
        lbl_clock_sub.setStyleSheet("font-size: 10px; color: #94A3B8; font-weight: bold; letter-spacing: 1.5px;")
        lbl_clock_sub.setAlignment(Qt.AlignCenter)

        content.addWidget(self.lbl_status)
        content.addStretch()
        content.addWidget(self.qr_card_container, 0, Qt.AlignCenter)
        content.addSpacing(25)
        content.addWidget(self.lbl_session_clock)
        content.addLayout(prog_layout)
        content.addSpacing(5)
        content.addWidget(lbl_clock_sub)
        content.addStretch()

        # KANAN: STATISTIK & ACTIVITY LOG
        stats_panel = QFrame()
        stats_panel.setFixedWidth(290)
        stats_panel.setStyleSheet("background-color: #ffffff; border-left: 1px solid #E2E8F0;")
        stats_layout = QVBoxLayout(stats_panel)
        stats_layout.setContentsMargins(30, 40, 30, 40)

        current_date = datetime.now().strftime("%A, %d %b %Y")
        lbl_date = QLabel(current_date)
        lbl_date.setStyleSheet("color: #94A3B8; font-size: 12px; font-weight: 600;")
        lbl_date.setAlignment(Qt.AlignRight)
        stats_layout.addWidget(lbl_date)
        stats_layout.addSpacing(20)

        metric_card = QFrame()
        metric_card.setObjectName("MetricCard")
        metric_card.setFixedHeight(120)
        m_layout = QVBoxLayout(metric_card)
        m_layout.setContentsMargins(20, 15, 20, 15)
        
        lbl_metric_title = QLabel("STUDENTS PRESENT")
        lbl_metric_title.setStyleSheet("color: #0284C7; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        
        self.lbl_hadir = QLabel("0")
        self.lbl_hadir.setStyleSheet("font-size: 56px; font-weight: 800; color: #0369A1;")
        
        m_layout.addWidget(lbl_metric_title)
        m_layout.addWidget(self.lbl_hadir)
        stats_layout.addWidget(metric_card)
        stats_layout.addSpacing(25)

        lbl_act_title = QLabel("RECENT SCANS")
        lbl_act_title.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        stats_layout.addWidget(lbl_act_title)
        stats_layout.addSpacing(10)
        
        self.activity_list = QListWidget()
        self.activity_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.activity_list.setWordWrap(True)
        self.activity_list.insertItem(0, "System offline. No recent activity.")
        stats_layout.addWidget(self.activity_list)

        main_layout.addWidget(sidebar)
        main_layout.addLayout(content)
        main_layout.addWidget(stats_panel)

        self.stacked_widget.addWidget(self.dashboard_page)

    # =========================================================
    # LOGIC
    # =========================================================
    def handle_login(self):
        user = self.user_input.text()
        pw = self.pass_input.text()
        try:
            res = requests.post(f"{BASE_URL}/api/lecturer/login", json={"username": user, "password": pw})
            if res.status_code == 200:
                data = res.json()
                self.lecturer_id = data['id']
                
                full_name = data['name']
                self.lbl_name.setText(full_name)
                
                name_parts = full_name.split()
                if len(name_parts) >= 2:
                    initials = name_parts[0][0] + name_parts[-1][0]
                else:
                    initials = full_name[:2]
                self.avatar.setText(initials.upper())

                self.course_box.clear()
                for c in data.get('courses', []):
                    self.course_box.addItem(c['name'], c['id'])
                self.stacked_widget.setCurrentIndex(1)
            else:
                QMessageBox.warning(self, "Failed", "Check credentials")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Backend disconnected.\nPastikan app.py sudah jalan.\nError detail: {e}")

    def start_attendance_session(self):
        c_id = self.course_box.currentData()
        try:
            res = requests.post(f"{BASE_URL}/api/session/start", json={"lecturer_id": self.lecturer_id, "course_id": c_id})
            if res.status_code == 201:
                self.session_id = res.json()['session_id']
                self.last_hadir_count = 0 
                self.lbl_hadir.setText("0")
                
                self.lbl_status.setText(f"🔴 LIVE: {self.course_box.currentText()}")
                self.lbl_status.setStyleSheet("font-size: 16px; color: #EF4444; font-weight: bold; letter-spacing: 0.5px;")
                self.progress_bar.setObjectName("") 
                self.progress_bar.setStyleSheet("/* reset */")
                
                self.activity_list.clear()
                self.activity_list.insertItem(0, "Session started. Waiting for students...")
                
                self.btn_start.hide()
                self.btn_stop.show()
                self.btn_export.show()

                self.qr_timer = QTimer()
                self.qr_timer.timeout.connect(self.fetch_qr)
                self.qr_timer.start(30000) 

                self.stats_timer = QTimer()
                self.stats_timer.timeout.connect(self.refresh_stats)
                self.stats_timer.start(5000)

                self.remaining_seconds = 300 
                self.progress_bar.setValue(300)
                self.lbl_session_clock.setText("05:00")
                self.lbl_session_clock.setStyleSheet("font-size: 42px; font-weight: 700; color: #334155; font-family: 'Consolas', monospace;")
                
                self.clock_timer = QTimer()
                self.clock_timer.timeout.connect(self.update_clock)
                self.clock_timer.start(1000)
                
                self.qr_display.setObjectName("")
                self.qr_display.setStyleSheet("")
                QTimer.singleShot(1000, self.fetch_qr) 
        except:
            QMessageBox.warning(self, "Error", "Failed to start")

    def stop_attendance_session(self):
        if hasattr(self, 'qr_timer'): self.qr_timer.stop()
        if hasattr(self, 'stats_timer'): self.stats_timer.stop()
        if hasattr(self, 'clock_timer'): self.clock_timer.stop()
        
        self.qr_display.setPixmap(QPixmap())
        self.qr_display.setObjectName("QRPlaceholder")
        self.qr_display.setText("📷\n\nSESSION CLOSED")
        self.qr_display.setStyleSheet("color: #94A3B8; font-weight: bold; font-size: 16px;")
        
        self.lbl_status.setText("🟢 System Idle")
        self.lbl_status.setStyleSheet("font-size: 16px; color: #64748B; font-weight: 600; letter-spacing: 0.5px;")
        
        self.activity_list.clear()
        self.activity_list.insertItem(0, "🔒 Session officially closed. No active scans.")
        
        self.lbl_session_clock.setText("00:00")
        self.lbl_session_clock.setStyleSheet("font-size: 42px; font-weight: 700; color: #334155; font-family: 'Consolas', monospace;")
        self.progress_bar.setValue(0)
        
        self.btn_stop.hide()
        self.btn_start.show()

    def update_clock(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            m, s = divmod(self.remaining_seconds, 60)
            self.lbl_session_clock.setText(f"{m:02d}:{s:02d}")
            self.progress_bar.setValue(self.remaining_seconds) 
            
            if self.remaining_seconds == 30:
                self.lbl_session_clock.setStyleSheet("font-size: 42px; font-weight: 700; color: #EF4444; font-family: 'Consolas', monospace;")
                self.progress_bar.setObjectName("ProgressUrgent")
                self.progress_bar.setStyleSheet("/* update */")
        else:
            self.stop_attendance_session()
            QMessageBox.warning(self, "Time's Up", "The 5-minute attendance window has ended.")

    def fetch_qr(self):
        try:
            res = requests.get(f"{BASE_URL}/api/session/{self.session_id}/current-qr")
            if res.status_code == 200:
                token_str = res.json().get('token')
                qr_img = qrcode.make(token_str)
                buf = BytesIO()
                qr_img.save(buf, format="PNG")
                
                qimage = QImage.fromData(buf.getvalue())
                pixmap = QPixmap.fromImage(qimage).scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.qr_display.setPixmap(pixmap)
        except: pass

    def refresh_stats(self):
        try:
            # 1. Cek jumlah kehadiran
            res_stats = requests.get(f"{BASE_URL}/api/stats/lecturer/{self.session_id}")
            if res_stats.status_code == 200:
                current_hadir = res_stats.json()['data']['statistik']['hadir']
                
                # 2. Jika ada mahasiswa baru yang absen
                if current_hadir > self.last_hadir_count:
                    diff = current_hadir - self.last_hadir_count
                    
                    # 3. Panggil fungsi Live buatan Afif untuk tarik NAMA
                    res_live = requests.get(f"{BASE_URL}/api/attendance/live/{self.session_id}")
                    if res_live.status_code == 200:
                        live_data = res_live.json().get('data', [])
                        
                        # Ambil data mahasiswa terbaru
                        new_students = live_data[-diff:]
                        
                        from datetime import datetime
                        for student in new_students:
                            nama = student.get('name', 'Unknown')
                            time_str = datetime.now().strftime("%H:%M:%S")
                            
                            item_text = f"👤 {nama}\n🕒 {time_str}"
                            self.activity_list.insertItem(0, item_text)
                    
                    self.last_hadir_count = current_hadir
                    
                self.lbl_hadir.setText(str(current_hadir))
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