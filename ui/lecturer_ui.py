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

# CONFIG: Port 5001 sesuai app.py
BASE_URL = "http://127.0.0.1:5001"

class LecturerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Attendance - Bartın University")
        self.setFixedSize(1150, 750)
        
        # =========================================================
        # 🎨 STYLE: THE ULTIMATE BLUE AESTHETIC WITH VISUAL FIXES
        # =========================================================
        self.setStyleSheet("""
            QMainWindow { background-color: #F8FAFC; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #1E293B; }
            QFrame#Sidebar { background-color: #0F172A; border-radius: 0px; }
            QFrame#ContentCard { background-color: #ffffff; border: 1px solid #E2E8F0; border-radius: 24px; }
            QFrame#QRPlaceholder { background-color: #F8FAFC; border: 2px dashed #CBD5E1; border-radius: 20px; }
            QFrame#MetricCard { background-color: #F0F9FF; border: 1px solid #BAE6FD; border-radius: 16px; }
            
            /* Style Baru Login Page (Deep Navy) */
            QWidget#LoginPage { background-color: #0b1a58; }
            QLabel#LoginLabel, QLabel#IconLabel { color: white; background: transparent; }
            QPushButton#LoginBtn { background-color: #3b82f6; color: white; font-size: 16px; font-weight: bold; border-radius: 12px; padding: 12px; }
            QPushButton#LoginBtn:hover { background-color: #2563eb; }

            /* Warna Dropdown List */
            QComboBox { padding: 12px; background-color: #F1F5F9; border: 1px solid #E2E8F0; border-radius: 12px; color: #1E293B; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #ffffff; color: #1E293B; selection-background-color: #2563EB; selection-color: white; border: 1px solid #E2E8F0; border-radius: 8px; outline: none; }
            
            QPushButton { background-color: #2563EB; color: white; font-weight: 600; border-radius: 12px; padding: 14px; border: none; }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton#StopBtn { background-color: #EF4444; }
            QPushButton#StopBtn:hover { background-color: #DC2626; }
            QPushButton#SecondaryBtn { background-color: #E0F2FE; color: #0369A1; border: 1px solid #BAE6FD; }
            
            QLabel#SidebarName { color: #F8FAFC; font-size: 18px; font-weight: 700; }
            QLabel#StatValue { font-size: 82px; font-weight: 800; color: #2563EB; }
            QLabel#TimerLabel { font-size: 42px; font-weight: 700; color: #334155; font-family: 'Consolas', monospace; letter-spacing: 2px;}
            
            QProgressBar { background-color: #E2E8F0; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #2563EB; border-radius: 4px; }
            QProgressBar#ProgressUrgent::chunk { background-color: #EF4444; }

            /* 🔥 TAMPILAN PREMIUM UNTUK RECENT SCANS */
            QListWidget { 
                background-color: transparent; 
                border: none; 
                outline: none; 
            }
            QListWidget::item { 
                background-color: #ffffff; 
                border: 1px solid #E2E8F0; 
                border-left: 5px solid #10B981; /* Garis aksen Hijau Emerald ala sukses */
                border-radius: 10px; 
                padding: 12px 16px; 
                margin-bottom: 10px; 
                color: #0F172A; 
                font-weight: 600;
            }
            QListWidget::item:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
            QListWidget::item:selected { 
                background-color: #ECFDF5; 
                border: 1px solid #34D399; 
                border-left: 5px solid #059669;
                color: #065F46; 
            }
        """)

        self.session_id = None
        self.lecturer_id = None
        self.remaining_seconds = 300 
        self.last_hadir_count = 0 
        
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.init_login_page()
        self.init_dashboard_page()

    def apply_shadow(self, widget, blur=30, opacity=40, offset_y=10):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(blur)
        shadow.setXOffset(0)
        shadow.setYOffset(offset_y)
        shadow.setColor(QColor(0, 0, 0, opacity))
        widget.setGraphicsEffect(shadow)

    # =========================================================
    # 🎨 1. LOGIN PAGE
    # =========================================================
    def init_login_page(self):
        page = QWidget()
        page.setObjectName("LoginPage")

        layout = QVBoxLayout(page)
        # Menahan semua konten tepat di tengah layar
        layout.setAlignment(Qt.AlignCenter) 
        
        # Kontainer utama
        container = QWidget()
        container.setFixedWidth(320)
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(10)
        c_layout.setAlignment(Qt.AlignCenter) 

        # A. Judul "Teacher Login"
        title = QLabel("Teacher Login")
        title.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 20px; color: white;")
        title.setAlignment(Qt.AlignCenter)

        # B. Kotak Ikon Guru
        icon_frame = QFrame()
        icon_frame.setFixedSize(140, 160) 
        icon_frame.setStyleSheet("background-color: #3b82f6; border-radius: 20px;") 
        self.apply_shadow(icon_frame, blur=20, opacity=60)
        
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setAlignment(Qt.AlignCenter)
        icon_layout.setContentsMargins(15, 15, 15, 15) 

        # Lingkaran Putih
        icon_circle_frame = QFrame()
        icon_circle_frame.setFixedSize(80, 80) 
        icon_circle_frame.setStyleSheet("""
            background-color: white; 
            border-radius: 40px; 
        """)
        
        circle_layout = QVBoxLayout(icon_circle_frame)
        circle_layout.setAlignment(Qt.AlignCenter)
        circle_layout.setContentsMargins(5, 5, 5, 5) 

        self.icon_lbl = QLabel() 
        self.icon_lbl.setStyleSheet("background: transparent;")
        self.icon_lbl.setAlignment(Qt.AlignCenter)

        # Mencari path gambar dengan path absolut
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        asset_path = os.path.join(current_dir, '..', 'assets', 'teacher_icon.png')

        if os.path.exists(asset_path):
            pixmap = QPixmap(asset_path)
            scaled_icon = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_lbl.setPixmap(scaled_icon)
        else:
            self.icon_lbl.setText("👨‍🏫")
            self.icon_lbl.setStyleSheet("font-size: 45px; background: transparent; color: #1E293B;")

        circle_layout.addWidget(self.icon_lbl)
        
        # Teks "Teacher"
        icon_text = QLabel("Teacher")
        icon_text.setStyleSheet("font-size: 16px; font-weight: bold; background: transparent; color: white;")
        icon_text.setAlignment(Qt.AlignCenter)
        
        icon_layout.addWidget(icon_circle_frame, 0, Qt.AlignCenter)
        icon_layout.addSpacing(8) 
        icon_layout.addWidget(icon_text)
        
        icon_container = QHBoxLayout()
        icon_container.addStretch()
        icon_container.addWidget(icon_frame)
        icon_container.addStretch()

        # C. Input Username
        lbl_user = QLabel("Username")
        lbl_user.setStyleSheet("font-size: 14px; margin-top: 20px; color: white;")
        
        user_box = QFrame()
        user_box.setStyleSheet("background-color: white; border-radius: 10px;")
        user_layout = QHBoxLayout(user_box)
        user_layout.setContentsMargins(10, 2, 10, 2)
        
        icon_u = QLabel("👤")
        icon_u.setStyleSheet("color: black; font-size: 16px; background: transparent;")
        self.user_input = QLineEdit()
        self.user_input.setText("admin")
        self.user_input.setStyleSheet("background: transparent; border: none; color: black; font-size: 14px; padding: 8px;")
        
        user_layout.addWidget(icon_u)
        user_layout.addWidget(self.user_input)

        # D. Input Password
        lbl_pass = QLabel("Password")
        lbl_pass.setStyleSheet("font-size: 14px; margin-top: 10px; color: white;")
        
        pass_box = QFrame()
        pass_box.setStyleSheet("background-color: white; border-radius: 10px;")
        pass_layout = QHBoxLayout(pass_box)
        pass_layout.setContentsMargins(10, 2, 10, 2)
        
        icon_p = QLabel("🔑") 
        icon_p.setStyleSheet("color: black; font-size: 16px; background: transparent;")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setText("admin")
        self.pass_input.setStyleSheet("background: transparent; border: none; color: black; font-size: 14px; padding: 8px;")
        
        pass_layout.addWidget(icon_p)
        pass_layout.addWidget(self.pass_input)

        # E. Tombol Log in
        btn_login = QPushButton("Log in")
        btn_login.setObjectName("LoginBtn")
        btn_login.clicked.connect(self.handle_login)
        self.apply_shadow(btn_login, blur=15, opacity=50)

        # F. Tautan Forgot Password (Desain Modern dengan efek hover)
        lbl_forgot = QLabel("Forgot the password?")
        lbl_forgot.setStyleSheet("""
            QLabel {
                font-size: 12px; 
                color: #94a3b8; 
                margin-top: 15px;
            }
            QLabel:hover {
                color: white;
                text-decoration: underline; 
            }
        """)
        lbl_forgot.setAlignment(Qt.AlignCenter)
        lbl_forgot.setCursor(Qt.PointingHandCursor)

        # Menyusun semua komponen dari atas ke bawah
        c_layout.addWidget(title)
        c_layout.addLayout(icon_container)
        c_layout.addWidget(lbl_user)
        c_layout.addWidget(user_box)
        c_layout.addWidget(lbl_pass)
        c_layout.addWidget(pass_box)
        c_layout.addSpacing(20) 
        c_layout.addWidget(btn_login)
        c_layout.addWidget(lbl_forgot)

        layout.addWidget(container)
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
        # Tambahkan ini di bawah baris 312
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #e0f2fe; /* Warna biru muda dasar */
                color: #0c4a6e;            /* Warna teks */
                border-radius: 8px;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #bae6fd; /* 🔥 Warna sedikit lebih gelap saat kursor di atasnya */
            }
            QPushButton:pressed {
                background-color: #7dd3fc; /* 🔥 Feedback visual saat diklik */
            }
        """)
        self.btn_export.clicked.connect(self.download_excel_report)
        self.btn_export.hide()

        side_layout.addWidget(self.btn_start)
        side_layout.addWidget(self.btn_stop)
        side_layout.addSpacing(10)
        side_layout.addWidget(self.btn_export)

        # --- Content Area ---
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

        # --- Right Panel (Metrics) ---
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
        
        # Sembunyikan dashed border aneh bawaan PyQt saat item di-klik
        self.activity_list.setFocusPolicy(Qt.NoFocus) 
        
        stats_layout.addWidget(self.activity_list)
        stats_layout.addStretch()

        main_layout.addWidget(sidebar)
        main_layout.addLayout(content)
        main_layout.addWidget(stats_panel)

        self.stacked_widget.addWidget(self.dashboard_page)

    # =========================================================
    # ⚙️ LOGIC
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
        except:
            QMessageBox.critical(self, "Error", "Backend disconnected.\nPastikan app.py (port 5001) sudah jalan.")

    def start_attendance_session(self):
        c_id = self.course_box.currentData()
        try:
            res = requests.post(f"{BASE_URL}/api/session/start", 
                                json={"lecturer_id": self.lecturer_id, "course_id": c_id})
            if res.status_code == 201:
                self.session_id = res.json()['session_id']
                self.last_hadir_count = 0 
                self.lbl_hadir.setText("0")
                
                self.lbl_status.setText(f"🔴 LIVE: {self.course_box.currentText()}")
                self.lbl_status.setStyleSheet("font-size: 16px; color: #EF4444; font-weight: bold; letter-spacing: 0.5px;")
                self.progress_bar.setObjectName("") 
                self.progress_bar.setStyleSheet("/* reset */")
                
                self.activity_list.clear()
                
                self.btn_start.hide()
                self.btn_stop.show()
                self.btn_export.show()

                self.qr_timer = QTimer()
                self.qr_timer.timeout.connect(self.fetch_qr)
                self.qr_timer.start(30000) 

                self.stats_timer = QTimer()
                self.stats_timer.timeout.connect(self.refresh_stats)
                self.stats_timer.start(3000) # Dipercepat agar UI terasa instan

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

    # 🔥 LOGIKA PINTAR - TARIK NAMA & DESAIN ESTETIK
    def refresh_stats(self):
        try:
            res_live = requests.get(f"{BASE_URL}/api/attendance/live/{self.session_id}")
            
            if res_live.status_code == 200:
                live_data = res_live.json().get('data', [])
                current_hadir = len(live_data) 
                
                self.lbl_hadir.setText(str(current_hadir))
                
                if current_hadir > self.last_hadir_count:
                    if self.last_hadir_count == 0:
                        self.activity_list.clear()

                    diff = current_hadir - self.last_hadir_count
                    new_students = live_data[-diff:] 
                    
                    from datetime import datetime
                    for student in new_students:
                        nama = student.get('name', 'Unknown Student')
                        time_str = datetime.now().strftime("%H:%M:%S")
                        
                        # Format estetik untuk kartu list
                        item_text = f"✓  {nama.upper()}\n    Scanned at {time_str}"
                        self.activity_list.insertItem(0, item_text)
                        
                    self.last_hadir_count = current_hadir
        except: pass

    def download_excel_report(self):
        # 1. Buat objek MessageBox dulu (Jangan langsung panggil .warning)
        msg = QMessageBox(self) 
        
        # 2. 🔥 BERI STYLE HANYA PADA KOTAK PESAN INI SAJA (Bukan self)
        msg.setStyleSheet("background-color: #2b2b2b; color: white; QLabel { color: white; } QPushButton { background-color: #444; color: white; padding: 5px; min-width: 60px; }")

        if not hasattr(self, 'session_id') or self.session_id is None:
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Export Failed")
            msg.setText("No active session found. Please start a session first.")
            msg.exec()
            return

        try:
            res = requests.get(f"{BASE_URL}/api/report/export/{self.session_id}")
            
            if res.status_code == 200:
                content_dispo = res.headers.get('content-disposition')
                fn = content_dispo.split('filename=')[1].strip('"') if content_dispo else f"Report_{self.session_id}.xlsx"
                
                try:
                    with open(fn, "wb") as f: f.write(res.content)
                    
                    # Pesan Sukses
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Export Success")
                    msg.setText(f"Report saved successfully as:\n{fn}")
                    msg.exec() # Tampilkan pesan
                    
                    import os
                    os.startfile(os.getcwd())
                except PermissionError:
                    msg.setIcon(QMessageBox.Critical)
                    msg.setText("Gagal menyimpan! Tutup file Excel-nya dulu.")
                    msg.exec()
            else:
                msg.setIcon(QMessageBox.Warning)
                msg.setText(f"Server Error: {res.status_code}")
                msg.exec()
                
        except Exception as e:
            msg.setIcon(QMessageBox.Critical)
            msg.setText(f"Connection failed: {str(e)}")
            msg.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LecturerApp()
    window.show()
    sys.exit(app.exec())