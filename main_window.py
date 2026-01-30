from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLineEdit, QLabel, QDialog, QFormLayout,
                             QCheckBox, QMenuBar, QMenu, QSystemTrayIcon, QMessageBox,
                             QFileDialog, QInputDialog, QHeaderView, QTextEdit, QApplication)
from PyQt6.QtCore import Qt, QTimer, QUrl, QMimeData, QPoint, QEvent
from PyQt6.QtGui import QDesktopServices, QDrag, QPixmap, QColor, QKeySequence, QIcon, QAction, QPainter
import uuid
from datetime import datetime
import os
import json
from pathlib import Path

from crypto import CryptoManager
from password_generator import PasswordGenerator
from batch_importer import BatchImporter
from settings_dialog import SettingsDialog

class PasswordEntryDialog(QDialog):
    """密码条目添加/编辑对话框"""
    def __init__(self, parent=None, entry=None):
        super().__init__(parent)
        self.setWindowTitle("编辑密码条目" if entry else "添加密码条目")
        self.setFixedSize(400, 350)
        self.setModal(True)
        
        self.entry = entry.copy() if entry else {
            'id': str(uuid.uuid4()),
            'website_name': '',
            'url': '',
            'username': '',
            'password': '',
            'note': '',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 表单布局
        form_layout = QFormLayout()
        
        # 网站名
        self.website_name_edit = QLineEdit(self.entry['website_name'])
        form_layout.addRow("网站名：", self.website_name_edit)
        
        # 网址
        self.url_edit = QLineEdit(self.entry['url'])
        form_layout.addRow("网址：", self.url_edit)
        
        # 账号
        self.username_edit = QLineEdit(self.entry['username'])
        form_layout.addRow("账号：", self.username_edit)
        
        # 密码
        password_layout = QHBoxLayout()
        self.password_edit = QLineEdit(self.entry['password'])
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        generate_password_btn = QPushButton("生成")
        generate_password_btn.clicked.connect(self.generate_password)
        show_password_check = QCheckBox("显示")
        show_password_check.stateChanged.connect(self.toggle_password_visibility)
        
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(generate_password_btn)
        password_layout.addWidget(show_password_check)
        form_layout.addRow("密码：", password_layout)
        
        # 备注
        self.note_edit = QLineEdit(self.entry['note'])
        form_layout.addRow("备注：", self.note_edit)
        
        layout.addLayout(form_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_entry)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def generate_password(self):
        """生成密码"""
        generator = PasswordGenerator(self)
        if generator.exec() == QDialog.DialogCode.Accepted:
            password = generator.get_password()
            self.password_edit.setText(password)
    
    def toggle_password_visibility(self, state):
        """切换密码显示/隐藏"""
        if state == Qt.CheckState.Checked.value:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def save_entry(self):
        """保存条目"""
        website_name = self.website_name_edit.text().strip()
        url = self.url_edit.text().strip()
        username = self.username_edit.text().strip()
        password = self.password_edit.text().strip()
        
        if not website_name or not url or not username or not password:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("网站名、网址、账号、密码不能为空")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 格式化 URL
        if url and not (url.startswith('http://') or url.startswith('https://')):
            url = 'https://' + url
        
        # 更新条目
        self.entry.update({
            'website_name': website_name,
            'url': url,
            'username': username,
            'password': password,
            'note': self.note_edit.text().strip(),
            'updated_at': datetime.now().isoformat()
        })
        
        self.accept()
    
    def get_entry(self):
        """返回条目数据"""
        return self.entry

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("密码管理器")
        self.setMinimumSize(800, 600)
        # 移除Tool标志，使用默认窗口类型，确保显示标准控制按钮
        # 保留系统托盘功能
        
        # 初始化数据
        self.db_file = "passwords.json.aes"
        self.crypto_manager = CryptoManager()
        self.entries = {}
        self.entries_order = []
        self.master_password = ""
        self.settings = {"auto_lock_time": 5, "lock_on_minimize": True, "theme": "light"}
        self.login_dialog_visible = False
        
        # 剪贴板定时器
        self.clipboard_timer = QTimer()
        self.clipboard_timer.setSingleShot(True)
        self.clipboard_timer.timeout.connect(self.clear_clipboard)
        
        # 自动锁定定时器
        self.lock_timer = QTimer()
        self.lock_timer.setSingleShot(True)  # 设置为单触发模式
        self.lock_timer.setInterval(self.settings["auto_lock_time"] * 60 * 1000)  # 分钟转毫秒
        self.lock_timer.timeout.connect(self.auto_lock)
        
        # 初始化界面
        self.init_ui()
        
        # 初始化系统托盘
        self.init_system_tray()
        
        # 加载设置
        self.load_settings()
        
        # 检查数据库文件
        if not os.path.exists(self.db_file):
            self.setup_first_run()
        else:
            self.show_login_dialog()
    
    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 菜单栏
        self.init_menu_bar()
        
        # 搜索栏
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索网站名或账号...")
        self.search_edit.textChanged.connect(self.filter_entries)
        search_layout.addWidget(QLabel("搜索："))
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)
        
        # 表格
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(5)
        self.table_widget.setHorizontalHeaderLabels(["选择", "网站名", "网址", "账号", "操作"])
        
        # 设置列宽
        self.table_widget.setColumnWidth(0, 60)
        self.table_widget.setColumnWidth(1, 150)
        self.table_widget.setColumnWidth(2, 200)
        self.table_widget.setColumnWidth(3, 150)
        self.table_widget.setColumnWidth(4, 120)
        
        # 设置表格属性
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table_widget.doubleClicked.connect(self.open_url)
        
        # 启用拖拽
        self.table_widget.setDragEnabled(True)
        self.table_widget.setAcceptDrops(True)
        self.table_widget.viewport().setAcceptDrops(True)
        self.table_widget.setDragDropOverwriteMode(False)
        self.table_widget.setDropIndicatorShown(True)
        self.table_widget.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        
        main_layout.addWidget(self.table_widget)
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("添加")
        self.add_btn.clicked.connect(self.add_entry)
        
        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self.edit_entry)
        
        self.delete_btn = QPushButton("删除")
        self.delete_btn.clicked.connect(self.delete_entries)
        
        self.batch_add_btn = QPushButton("批量添加")
        self.batch_add_btn.clicked.connect(self.batch_add_entries)
        
        # 添加悬浮窗口按钮
        self.floating_btn = QPushButton("悬浮窗口")
        self.floating_btn.clicked.connect(self.toggle_floating_window)
        
        # 添加导入导出按钮
        self.import_btn = QPushButton("导入")
        self.import_btn.clicked.connect(self.import_db)
        
        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_db)
        
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.batch_add_btn)
        button_layout.addWidget(self.floating_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.import_btn)
        button_layout.addWidget(self.export_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("已加载 0 个密码条目")
        
        # 键盘快捷键
        self.init_shortcuts()
    
    def init_menu_bar(self):
        """初始化菜单栏"""
        menu_bar = self.menuBar()
        
        # 设置菜单
        settings_menu = menu_bar.addMenu("设置")
        settings_action = QAction("设置", self)
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")
        # 添加操作说明动作
        help_action = QAction("操作说明", self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
    
    def init_shortcuts(self):
        """初始化快捷键"""
        # Ctrl+N 新建条目
        self.add_btn.setShortcut(QKeySequence("Ctrl+N"))
        
        # Ctrl+F 聚焦搜索框 - 使用 QShortcut
        from PyQt6.QtGui import QShortcut
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_edit.setFocus)
    
    def init_system_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # 创建一个简单的图标
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap)
        painter.setBrush(Qt.GlobalColor.red)
        painter.drawRect(8, 8, 16, 16)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        
        # 托盘菜单
        tray_menu = QMenu()
        
        show_action = QAction("显示", self)
        show_action.triggered.connect(self.show_from_menu)
        
        lock_action = QAction("锁定", self)
        lock_action.triggered.connect(self.lock_app)
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(lock_action)
        tray_menu.addSeparator()
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()
    
    def on_tray_icon_activated(self, reason):
        """托盘图标激活事件"""
        # 只处理左键点击图标
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_main_window()
    
    def show_from_menu(self):
        """从菜单显示主窗口"""
        self.show_main_window()
    
    def copy_template(self, template_text):
        """复制模板到剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(template_text)
        
        # 显示复制成功提示
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("成功")
        msg_box.setText("模板已复制到剪贴板，您可以粘贴到文本文件中使用")
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()
    
    def show_main_window(self):
        """显示主窗口"""
        # 强制显示主窗口，不检查锁定状态
        if not self.master_password:
            # 已锁定，显示登录对话框
            if self.login_dialog_visible:
                return
            
            self.login_dialog_visible = True
            
            login_dialog = QDialog(self)
            login_dialog.setWindowTitle("登录")
            login_dialog.setFixedSize(300, 150)
            login_dialog.setModal(True)
            
            layout = QVBoxLayout(login_dialog)
            
            form_layout = QFormLayout()
            password_label = QLabel("主密码：")
            password_edit = QLineEdit()
            password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            form_layout.addRow(password_label, password_edit)
            
            layout.addLayout(form_layout)
            
            # 忘记密码按钮
            forgot_layout = QHBoxLayout()
            forgot_btn = QPushButton("忘记密码？")
            forgot_btn.clicked.connect(lambda: self.forgot_password(login_dialog))
            forgot_layout.addWidget(forgot_btn)
            forgot_layout.addStretch()
            layout.addLayout(forgot_layout)
            
            button_layout = QHBoxLayout()
            login_btn = QPushButton("登录")
            login_btn.clicked.connect(lambda: self.login(password_edit.text(), login_dialog))
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(login_dialog.reject)
            
            button_layout.addStretch()
            button_layout.addWidget(login_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # 回车键登录
            password_edit.returnPressed.connect(lambda: self.login(password_edit.text(), login_dialog))
            
            try:
                result = login_dialog.exec()
                if result != QDialog.DialogCode.Accepted:
                    return
            finally:
                self.login_dialog_visible = False
        else:
            # 未锁定，直接显示主窗口
            # 确保窗口完全显示并激活到前台
            self.showNormal()
            self.activateWindow()
            self.raise_()
            # 强制设置窗口为活动窗口
            self.setWindowState(Qt.WindowState.WindowActive)
            self.setFocus()
    
    def show_login_dialog(self):
        """显示登录对话框"""
        login_dialog = QDialog(self)
        login_dialog.setWindowTitle("登录")
        login_dialog.setFixedSize(300, 150)
        login_dialog.setModal(True)
        
        layout = QVBoxLayout(login_dialog)
        
        form_layout = QFormLayout()
        password_label = QLabel("主密码：")
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(password_label, password_edit)
        
        layout.addLayout(form_layout)
        
        # 忘记密码按钮
        forgot_layout = QHBoxLayout()
        forgot_btn = QPushButton("忘记密码？")
        forgot_btn.clicked.connect(lambda: self.forgot_password(login_dialog))
        forgot_layout.addWidget(forgot_btn)
        forgot_layout.addStretch()
        layout.addLayout(forgot_layout)
        
        button_layout = QHBoxLayout()
        login_btn = QPushButton("登录")
        login_btn.clicked.connect(lambda: self.login(password_edit.text(), login_dialog))
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(lambda: self.handle_login_cancel(login_dialog))
        
        button_layout.addStretch()
        button_layout.addWidget(login_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 回车键登录
        password_edit.returnPressed.connect(lambda: self.login(password_edit.text(), login_dialog))
        
        if login_dialog.exec() == QDialog.DialogCode.Rejected:
            # 登录对话框被拒绝时，直接退出应用
            self.close_app()
    
    def setup_first_run(self):
        """首次运行设置"""
        # 创建设置对话框
        setup_dialog = QDialog(self)
        setup_dialog.setWindowTitle("首次运行设置")
        setup_dialog.setFixedSize(400, 250)
        setup_dialog.setModal(True)
        
        layout = QVBoxLayout(setup_dialog)
        
        info_label = QLabel("欢迎使用密码管理器！请设置您的主密码。")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        form_layout = QFormLayout()
        
        # 主密码
        password_edit = QLineEdit()
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("主密码：", password_edit)
        
        # 确认主密码
        confirm_edit = QLineEdit()
        confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("确认主密码：", confirm_edit)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        setup_btn = QPushButton("设置")
        setup_btn.clicked.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
        exit_btn = QPushButton("退出")
        exit_btn.clicked.connect(lambda: self.force_exit_app())
        
        button_layout.addStretch()
        button_layout.addWidget(setup_btn)
        button_layout.addWidget(exit_btn)
        
        layout.addLayout(button_layout)
        
        # 回车键设置
        password_edit.returnPressed.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
        confirm_edit.returnPressed.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
        
        # 显示设置对话框
        result = setup_dialog.exec()
        
        # 如果用户点击了右上角的 × 关闭按钮，彻底退出软件
        if result == QDialog.DialogCode.Rejected:
            self.force_exit_app()
    
    def setup_master_password(self, password, confirm_password, dialog):
        """设置主密码"""
        if not password:
            msg_box = QMessageBox(dialog)
            msg_box.setWindowTitle("警告")
            msg_box.setText("主密码不能为空")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        if password != confirm_password:
            msg_box = QMessageBox(dialog)
            msg_box.setWindowTitle("警告")
            msg_box.setText("两次输入的密码不一致")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 保存主密码（仅用于本次会话，不存储到磁盘）
        self.master_password = password
        
        # 创建初始数据库
        self.entries = {}
        self.entries_order = []
        self.save_db()
        
        dialog.accept()
        self.load_entries()
        self.start_lock_timer()
        # 强制显示主窗口并激活到前台
        self.showNormal()
        self.activateWindow()
        self.raise_()
        # 确保窗口状态正确
        self.setWindowState(Qt.WindowState.WindowActive)
        self.setFocus()
    
    def login(self, password, dialog):
        """登录验证"""
        if self.crypto_manager.verify_master_password(self.db_file, password):
            self.master_password = password
            self.load_entries()
            # 窗口显示后再启动定时器
            self.start_lock_timer()
            dialog.accept()
            # 强制显示主窗口并激活到前台
            self.showNormal()
            self.activateWindow()
            self.raise_()
            # 确保窗口状态正确
            self.setWindowState(Qt.WindowState.WindowActive)
            self.setFocus()
        else:
            msg_box = QMessageBox(dialog)
            msg_box.setWindowTitle("警告")
            msg_box.setText("主密码不正确")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def change_master_password(self):
        """更改主密码"""
        # 加载设置
        settings = SettingsDialog(self)
        
        # 检查是否绑定邮箱
        if not settings.settings["email"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("未绑定QQ邮箱，无法更改主密码")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 创建自定义输入对话框，包含三个输入框
        dialog = QDialog(self)
        dialog.setWindowTitle("更改主密码")
        dialog.resize(400, 250)
        
        layout = QVBoxLayout(dialog)
        
        # 当前主密码输入
        current_label = QLabel("请输入当前主密码：")
        layout.addWidget(current_label)
        
        current_edit = QLineEdit(dialog)
        current_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(current_edit)
        
        # 新主密码输入
        new_label = QLabel("请输入新主密码：")
        layout.addWidget(new_label)
        
        new_edit = QLineEdit(dialog)
        new_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(new_edit)
        
        # 确认新主密码输入
        confirm_label = QLabel("请确认新主密码：")
        layout.addWidget(confirm_label)
        
        confirm_edit = QLineEdit(dialog)
        confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(confirm_edit)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定", dialog)
        cancel_button = QPushButton("取消", dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接按钮信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 执行对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            old_password = current_edit.text().strip()
            new_password = new_edit.text().strip()
            confirm_password = confirm_edit.text().strip()
            
            # 验证输入
            if not old_password:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("警告")
                msg_box.setText("请输入当前主密码")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                return
            
            if not new_password:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("警告")
                msg_box.setText("请输入新主密码")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                return
            
            if not confirm_password:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("警告")
                msg_box.setText("请确认新主密码")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                return
        else:
            return
        
        # 验证旧密码是否正确
        if not self.crypto_manager.verify_master_password(self.db_file, old_password):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("当前主密码不正确")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        if new_password != confirm_password:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("两次输入的密码不一致")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        try:
            # 更改主密码（重新加密数据库）
            if self.crypto_manager.change_master_password(self.db_file, old_password, new_password):
                # 更新当前会话的主密码
                self.master_password = new_password
                
                # 向绑定的邮箱发送新主密码
                self.send_new_password_email(new_password, settings.settings["email"], settings.settings["email_password"])
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("成功")
                msg_box.setText("主密码已更改，新密码已发送到您的绑定邮箱")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("警告")
                msg_box.setText("更改主密码失败")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"更改主密码时发生错误：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
        return
    
    def send_new_password_email(self, new_password, email, email_password):
        """向绑定的邮箱发送新主密码"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from email.mime.base import MIMEBase
            from email import encoders
            import os
            
            # QQ邮箱SMTP服务器设置
            smtp_server = "smtp.qq.com"
            smtp_port = 587
            from_email = email
            
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = email
            msg["Subject"] = "密码管理器 - 主密码已更改"
            
            body = f"""尊敬的用户：

您的密码管理器主密码已成功更改！

新主密码：{new_password}

请妥善保管此密码，不要泄露给他人。

此邮件包含重新加密后的密码数据库文件，请保存好此文件。

如果您没有进行此操作，请立即检查您的账户安全。

此致
密码管理器团队
"""
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # 添加加密文件作为附件
            if hasattr(self, 'db_file') and os.path.exists(self.db_file):
                attachment = MIMEBase('application', 'octet-stream')
                with open(self.db_file, 'rb') as f:
                    attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                
                # 设置附件头
                filename = os.path.basename(self.db_file)
                attachment.add_header('Content-Disposition', f'attachment; filename=\"{filename}\"')
                msg.attach(attachment)
            
            # 发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, email_password)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            print(f"发送邮件失败：{e}")
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("新主密码已更改，但发送邮件失败，请检查邮箱设置")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def forgot_password(self, login_dialog):
        """忘记密码处理"""
        # 加载设置
        settings = SettingsDialog(self)
        
        if not settings.settings["email"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("未绑定邮箱，无法重置主密码")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 发送验证码
        if not settings.send_reset_code():
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("发送验证码失败")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 验证码输入对话框
        # 创建自定义输入对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("重置主密码")
        dialog.resize(400, 150)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入收到的验证码：")
        layout.addWidget(label)
        
        code_edit = QLineEdit(dialog)
        layout.addWidget(code_edit)
        
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定", dialog)
        cancel_button = QPushButton("取消", dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接按钮信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 执行对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            code = code_edit.text().strip()
            if not code:
                return
        else:
            return
        
        if settings.verify_reset_code(code):
            # 提示用户即将重置主密码
            reply = QMessageBox.question(
                self, 
                "重置主密码", 
                "验证码验证成功，现在将设置新的主密码。",
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Ok
            )
            
            if reply != QMessageBox.StandardButton.Ok:
                return
            
            # 设置新主密码
            # 创建自定义输入对话框
            dialog = QDialog(self)
            dialog.setWindowTitle("重置主密码")
            dialog.resize(400, 150)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("请输入新主密码：")
            layout.addWidget(label)
            
            password_edit = QLineEdit(dialog)
            password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(password_edit)
            
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton("确定", dialog)
            cancel_button = QPushButton("取消", dialog)
            
            button_layout.addStretch()
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            # 连接按钮信号
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            # 执行对话框
            if dialog.exec() == QDialog.DialogCode.Accepted:
                new_password = password_edit.text().strip()
                if not new_password:
                    return
            else:
                return
            
            # 确认新主密码
            dialog = QDialog(self)
            dialog.setWindowTitle("重置主密码")
            dialog.resize(400, 150)
            
            layout = QVBoxLayout(dialog)
            
            label = QLabel("请确认新主密码：")
            layout.addWidget(label)
            
            password_edit = QLineEdit(dialog)
            password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            layout.addWidget(password_edit)
            
            button_layout = QHBoxLayout()
            
            ok_button = QPushButton("确定", dialog)
            cancel_button = QPushButton("取消", dialog)
            
            button_layout.addStretch()
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            
            layout.addLayout(button_layout)
            
            # 连接按钮信号
            ok_button.clicked.connect(dialog.accept)
            cancel_button.clicked.connect(dialog.reject)
            
            # 执行对话框
            if dialog.exec() == QDialog.DialogCode.Accepted:
                confirm_password = password_edit.text().strip()
                if not confirm_password:
                    return
            else:
                return
            
            if new_password != confirm_password:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("警告")
                msg_box.setText("两次输入的密码不一致")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                return
            
            try:
                # 尝试读取原有数据库（不验证密码，因为我们通过邮箱验证了身份）
                # 直接读取文件内容，然后用新密码重新加密
                if os.path.exists(self.db_file):
                    with open(self.db_file, 'r', encoding='utf-8') as f:
                        db_content = json.load(f)
                    
                    # 提取原有数据（如果存在）
                    # 注意：这里不能直接解密，因为我们不知道旧密码
                    # 所以我们需要创建一个新的数据库，保留原有结构
                    # 这是安全设计，确保只有通过验证的用户才能重置
                    
                    # 创建新的空数据库，但使用新密码
                    self.master_password = new_password
                    self.entries = {}
                    self.entries_order = []
                    self.save_db()
                    
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("成功")
                    msg_box.setText("主密码已重置，您可以重新添加密码条目。")
                    msg_box.setIcon(QMessageBox.Icon.Information)
                    msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                    msg_box.exec()
                else:
                    # 数据库文件不存在，创建新的
                    self.master_password = new_password
                    self.entries = {}
                    self.entries_order = []
                    self.save_db()
                    
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle("成功")
                    msg_box.setText("主密码已设置，您可以开始添加密码条目。")
                    msg_box.setIcon(QMessageBox.Icon.Information)
                    msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                    msg_box.exec()
                    
            except Exception as e:
                # 重置失败，创建新数据库
                self.master_password = new_password
                self.entries = {}
                self.entries_order = []
                self.save_db()
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("成功")
                msg_box.setText("主密码已重置，您可以重新添加密码条目。")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
            
            login_dialog.accept()
            self.load_entries()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("验证码错误")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def load_entries(self):
        """加载密码条目"""
        try:
            data, self.entries_order = self.crypto_manager.load_encrypted_db(self.db_file, self.master_password)
            self.entries = data
            self.refresh_table()
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"加载数据失败：{e}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def save_db(self):
        """保存数据库"""
        try:
            self.crypto_manager.save_encrypted_db(self.db_file, self.master_password, self.entries, self.entries_order)
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"保存数据失败：{e}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def refresh_table(self):
        """刷新表格"""
        self.table_widget.setRowCount(0)
        
        for entry_id in self.entries_order:
            if entry_id in self.entries:
                self.add_entry_to_table(self.entries[entry_id])
        
        self.status_bar.showMessage(f"已加载 {len(self.entries)} 个密码条目")
    
    def add_entry_to_table(self, entry):
        """添加条目到表格"""
        row = self.table_widget.rowCount()
        self.table_widget.insertRow(row)
        
        # 选择框
        checkbox = QCheckBox()
        checkbox.setCheckState(Qt.CheckState.Unchecked)
        self.table_widget.setCellWidget(row, 0, checkbox)
        
        # 网站名
        self.table_widget.setItem(row, 1, QTableWidgetItem(entry['website_name']))
        
        # 网址
        self.table_widget.setItem(row, 2, QTableWidgetItem(entry['url']))
        
        # 账号
        self.table_widget.setItem(row, 3, QTableWidgetItem(entry['username']))
        
        # 操作按钮
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        copy_user_btn = QPushButton("复制账号")
        copy_user_btn.setFixedWidth(80)
        copy_user_btn.clicked.connect(lambda _, e=entry: self.copy_to_clipboard(e['username']))
        
        copy_pass_btn = QPushButton("复制密码")
        copy_pass_btn.setFixedWidth(80)
        copy_pass_btn.clicked.connect(lambda _, e=entry: self.copy_to_clipboard(e['password']))
        
        action_layout.addWidget(copy_user_btn)
        action_layout.addWidget(copy_pass_btn)
        
        self.table_widget.setCellWidget(row, 4, action_widget)
    
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板，15秒后自动清空"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # 启动定时器，15秒后清空剪贴板
        self.clipboard_timer.start(15000)
        
        # 显示提示
        self.status_bar.showMessage(f"已复制到剪贴板，15秒后自动清空")
    
    def clear_clipboard(self):
        """清空剪贴板"""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.clear()
        self.status_bar.showMessage("剪贴板已清空")
    
    def add_entry(self):
        """添加密码条目"""
        dialog = PasswordEntryDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            entry = dialog.get_entry()
            self.entries[entry['id']] = entry
            self.entries_order.append(entry['id'])
            self.save_db()
            self.refresh_table()
    
    def edit_entry(self):
        """编辑密码条目"""
        # 获取选中的条目
        selected_rows = [i for i in range(self.table_widget.rowCount()) 
                       if self.table_widget.cellWidget(i, 0).checkState() == Qt.CheckState.Checked]
        
        if len(selected_rows) != 1:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请选择一个条目进行编辑")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        row = selected_rows[0]
        entry_id = self.entries_order[row]
        entry = self.entries[entry_id]
        
        dialog = PasswordEntryDialog(self, entry)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_entry = dialog.get_entry()
            self.entries[updated_entry['id']] = updated_entry
            self.save_db()
            self.refresh_table()
    
    def delete_entries(self):
        """删除选中的密码条目"""
        # 获取选中的条目
        selected_rows = [i for i in range(self.table_widget.rowCount()) 
                       if self.table_widget.cellWidget(i, 0).checkState() == Qt.CheckState.Checked]
        
        if not selected_rows:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请选择要删除的条目")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除选中的 {len(selected_rows)} 个条目吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ok_button:
            # 按行号从大到小删除，避免索引错误
            for row in sorted(selected_rows, reverse=True):
                entry_id = self.entries_order[row]
                del self.entries[entry_id]
                del self.entries_order[row]
            
            self.save_db()
            self.refresh_table()
    
    def batch_add_entries(self):
        """批量添加密码条目"""
        # 显示标准模板提示
        template_dialog = QDialog(self)
        template_dialog.setWindowTitle("批量导入模板提示")
        template_dialog.setFixedSize(500, 300)
        template_dialog.setModal(True)
        
        layout = QVBoxLayout(template_dialog)
        
        # 提示信息
        info_label = QLabel("请按照以下标准模板格式准备 TXT 文件：")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        # 模板说明
        template_text = QTextEdit()
        template_text.setReadOnly(True)
        template_text.setText('''# 标准模板格式

## 格式说明：
- 每行一个密码条目
- 使用逗号分隔各字段（中文逗号和英文逗号都可以）
- 字段顺序：网站名,网址,账号,密码,备注
- 备注字段可选
- .csv是网站导出的账号密码格式
## txt示例：
N网,https://www.nexusmods.com/,username1,password1
星辰云,https://console.starx.cn/,18081587048,123456,游戏账号
零点FRP,https://frp.top/,user2,password2''')
        layout.addWidget(template_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 复制模板按钮
        copy_btn = QPushButton("复制模板")
        copy_btn.clicked.connect(lambda: self.copy_template(template_text.toPlainText()))
        
        # 继续按钮
        continue_btn = QPushButton("继续导入")
        continue_btn.clicked.connect(template_dialog.accept)
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(template_dialog.reject)
        
        button_layout.addWidget(copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(continue_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        # 显示模板提示
        if template_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # 文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择批量导入文件", "", "CSV Files (*.csv);;Text Files (*.txt)")
        if not file_path:
            return
        
        # 解析文件
        importer = BatchImporter()
        preview_entries, invalid_entries, total = importer.get_preview_data(file_path)
        
        if not preview_entries and not invalid_entries:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("文件中没有有效数据")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 预览对话框
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle(f"批量导入预览 ({total} 个有效条目)")
        preview_dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout(preview_dialog)
        
        # 预览表格
        preview_table = QTableWidget()
        preview_table.setColumnCount(5)
        preview_table.setHorizontalHeaderLabels(["网站名", "网址", "账号", "密码", "备注"])
        
        for entry in preview_entries:
            row = preview_table.rowCount()
            preview_table.insertRow(row)
            preview_table.setItem(row, 0, QTableWidgetItem(entry['website_name']))
            preview_table.setItem(row, 1, QTableWidgetItem(entry['url']))
            preview_table.setItem(row, 2, QTableWidgetItem(entry['username']))
            preview_table.setItem(row, 3, QTableWidgetItem(entry['password']))
            preview_table.setItem(row, 4, QTableWidgetItem(entry['note']))
        
        layout.addWidget(preview_table)
        
        # 显示无效条目
        if invalid_entries:
            invalid_label = QLabel(f"发现 {len(invalid_entries)} 个无效条目")
            layout.addWidget(invalid_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        import_btn = QPushButton("导入")
        import_btn.clicked.connect(preview_dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(preview_dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(import_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        if preview_dialog.exec() == QDialog.DialogCode.Accepted:
            # 执行导入
            entries = importer.import_entries(file_path)
            for entry in entries:
                self.entries[entry['id']] = entry
                self.entries_order.append(entry['id'])
            
            self.save_db()
            self.refresh_table()
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("成功")
            msg_box.setText(f"已导入 {len(entries)} 个密码条目")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def open_url(self, index):
        """双击打开URL"""
        if index.column() in [1, 2, 3]:
            row = index.row()
            entry_id = self.entries_order[row]
            entry = self.entries[entry_id]
            QDesktopServices.openUrl(QUrl(entry['url']))
    
    def filter_entries(self, text):
        """根据搜索文本过滤条目"""
        if not text:
            self.refresh_table()
            return
        
        filtered_order = [entry_id for entry_id in self.entries_order 
                         if text.lower() in self.entries[entry_id]['website_name'].lower() or 
                         text.lower() in self.entries[entry_id]['username'].lower()]
        
        # 刷新表格显示过滤后的条目
        self.table_widget.setRowCount(0)
        for entry_id in filtered_order:
            self.add_entry_to_table(self.entries[entry_id])
    
    def import_db(self):
        """导入数据库"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择导入文件", "", "Encrypted Files (*.json.aes)")
        if not file_path:
            return
        
        # 获取源文件和目标文件的绝对路径
        import os
        src_abs = os.path.abspath(file_path)
        dst_abs = os.path.abspath(self.db_file)
        
        # 检查是否是同一个文件
        if src_abs == dst_abs:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("不能导入与当前数据库相同的文件")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 验证主密码
        # 创建自定义输入对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("导入数据库")
        dialog.resize(400, 150)
        
        layout = QVBoxLayout(dialog)
        
        label = QLabel("请输入原数据库的主密码：")
        layout.addWidget(label)
        
        password_edit = QLineEdit(dialog)
        password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(password_edit)
        
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("确定", dialog)
        cancel_button = QPushButton("取消", dialog)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 连接按钮信号
        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)
        
        # 执行对话框
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = password_edit.text().strip()
            if not password:
                return
        else:
            return
        
        # 验证密码是否正确
        if not self.crypto_manager.verify_master_password(file_path, password):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("原数据库主密码不正确")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 显示主密码变更提示
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("主密码变更提示")
        msg_box.setText("导入后，您的主密码将变为原加密文件的主密码。\n\n此操作将：\n1. 覆盖当前所有密码数据\n2. 主密码变为导入文件的密码\n3. 需要重新登录\n\n确定要继续吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ok_button:
            # 复制文件
            try:
                import shutil
                shutil.copy(file_path, self.db_file)
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("成功")
                msg_box.setText("数据库导入成功，需要重新登录")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                self.lock_app()
            except Exception as e:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("错误")
                msg_box.setText(f"导入失败：{str(e)}")
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
    
    def export_db(self):
        """导出数据库"""
        # 显示导出提示
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("导出提示")
        msg_box.setText("请将数据库导出到软件配置文件夹以外的位置，否则可能导致软件崩溃。\n\n建议导出到：\n- 桌面\n- 文档文件夹\n- 外部存储设备")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(ok_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == cancel_button:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "选择导出文件", "passwords.json.aes", "Encrypted Files (*.json.aes)")
        if not file_path:
            return
        
        # 获取源文件的绝对路径
        import os
        src_abs = os.path.abspath(self.db_file)
        dst_abs = os.path.abspath(file_path)
        
        if src_abs == dst_abs:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("不能导出到源文件相同的位置")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 检查是否导出到软件配置文件夹
        app_dir = os.path.dirname(os.path.abspath(__file__))
        if os.path.commonpath([app_dir, dst_abs]) == app_dir:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("您正在导出到软件配置文件夹中，这可能导致软件崩溃。\n\n确定要继续吗？")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            
            # 添加自定义按钮
            ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
            msg_box.setDefaultButton(cancel_button)
            
            msg_box.exec()
            
            if msg_box.clickedButton() != ok_button:
                return
        
        # 复制文件
        try:
            import shutil
            shutil.copy(self.db_file, file_path)
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("成功")
            msg_box.setText("数据库导出成功")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"导出失败：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def open_settings(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_settings()
            self.update_lock_timer()
            # 更新悬浮窗口的快捷键设置
            if hasattr(self, 'floating_window') and hasattr(self.floating_window, 'update_shortcut'):
                shortcut_key = self.settings.get("floating_window_shortcut", "Ctrl+Shift+X")
                self.floating_window.update_shortcut(shortcut_key)
    
    def show_help(self):
        """显示软件操作注意事项"""
        help_text = """密码管理器操作说明：

1. 登录与锁定：
   - 首次使用需设置主密码
   - 空闲时间超过设定值后自动锁定
   - 点击设置中的"立即锁定应用"可手动锁定
   - 忘记主密码可通过绑定的邮箱重置
   - 取消登录时可选择退出软件

2. 密码管理：
   - 添加密码：点击"添加"按钮，填写网站名、网址、账号、密码等信息
   - 编辑密码：选择条目后点击"编辑"按钮修改信息
   - 删除密码：选择条目后点击"删除"按钮
   - 批量导入：点击"批量添加"按钮，选择CSV/TXT文件导入
   - 文本导入：打开"设置"窗口，进入"文本导入"标签页，点击"导入TXT到数据库"按钮
   - 批量导出：点击"导出"按钮，选择保存位置
   - 密码生成：点击密码输入框旁的"生成"按钮，可自定义密码复杂度
   - 密码复制：点击表格中的"复制账号"或"复制密码"按钮，密码会自动复制到剪贴板，15秒后自动清空

3. 悬浮窗口：
   - 快捷键 Ctrl+Alt+P 快速调用
   - 在搜索框中输入关键词查找密码
   - 点击条目可复制账号密码
   - 双击条目可直接打开对应网址

4. 安全设置：
   - 自动锁定时间：在设置中调整闲置时间
   - 最小化锁定：设置中可开启"最小化到系统托盘时自动锁定"
   - 主题切换：设置中可选择浅色或深色主题
   - 邮箱绑定：在设置的"邮箱设置"标签页中绑定邮箱，用于密码重置
   - 更改主密码：在设置中点击"更改主密码"按钮

5. 其他功能：
   - 搜索功能：在主窗口顶部的搜索框中输入关键词
   - 双击打开网址：在表格中双击网站名或网址列
   - 系统托盘：软件可最小化到系统托盘，右键可选择显示或退出
   - 窗口置顶：悬浮窗口支持置顶显示

6. 文本导入使用步骤：
   - 准备TXT文件，格式如下：
     网站名: 示例网站
     网址: https://example.com
     账号: username
     密码: password
     备注: 可选备注
     --------------------
     （多条记录用分隔线分隔）
   - 打开软件设置窗口，点击"文本导入"标签页
   - 点击"导入TXT到数据库"按钮
   - 选择准备好的TXT文件
   - 等待导入完成，查看导入结果提示

使用过程中如有问题，请随时联系开发者。"""
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("操作说明")
        msg_box.setText(help_text)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()
    
    def load_settings(self):
        """加载设置"""
        settings_dialog = SettingsDialog(self)
        self.settings = settings_dialog.settings
        self.apply_theme()
    
    def toggle_floating_window(self):
        """显示/隐藏悬浮窗口"""
        if hasattr(self, 'floating_window'):
            self.floating_window.toggle_visibility()
        else:
            # 如果悬浮窗口不存在，创建一个
            from floating_window import FloatingWindow
            self.floating_window = FloatingWindow(self)
            self.floating_window.set_entries(self.entries, self.entries_order)
            self.floating_window.show()
    
    def apply_theme(self):
        """应用主题"""
        theme = self.settings.get("theme", "light")
        
        if theme == "dark":
            # 深色主题样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QWidget {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QLineEdit, QSpinBox {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QPushButton {
                    background-color: #4d4d4d;
                    color: #ffffff;
                    border: 1px solid #666666;
                }
                QPushButton:hover {
                    background-color: #5d5d5d;
                }
                QTableWidget {
                    background-color: #3d3d3d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QTableWidget::item {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QTableWidget::item:selected {
                    background-color: #555555;
                }
                QHeaderView::section {
                    background-color: #4d4d4d;
                    color: #ffffff;
                    border: 1px solid #555555;
                }
                QMenuBar {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QMenu {
                    background-color: #3d3d3d;
                    color: #ffffff;
                }
                QCheckBox, QLabel {
                    color: #ffffff;
                }
            """)
        else:  # 浅色主题
            # 重置为默认样式
            self.setStyleSheet("")
        
        # 同步悬浮窗口主题
        if hasattr(self, 'floating_window') and self.floating_window:
            self.floating_window.toggle_theme(theme)
    
    def start_lock_timer(self):
        """启动自动锁定定时器"""
        # 只有在启用了自动锁定选项时才启动定时器
        if self.settings.get("auto_lock_time", 5) > 0:
            self.lock_timer.start()
    
    def update_lock_timer(self):
        """更新自动锁定定时器间隔"""
        self.lock_timer.setInterval(self.settings["auto_lock_time"] * 60 * 1000)
    
    def auto_lock(self):
        """自动锁定"""
        # 自动锁定时只清空数据，不显示登录对话框
        self.lock_app(show_login=False)
    
    def lock_app(self, show_login=True):
        """锁定应用"""
        # 清空数据
        self.master_password = ""
        self.entries = {}
        self.entries_order = []
        self.refresh_table()
        self.clipboard_timer.stop()
        self.clear_clipboard()
        
        # 隐藏主窗口，只保留托盘图标
        self.hide()
        
        # 只有在需要时才显示登录对话框
        if show_login:
            self.show_login_dialog()
    
    def close_app(self):
        """关闭应用"""
        self.tray_icon.hide()
        # 关闭悬浮窗口
        if hasattr(self, 'floating_window'):
            self.floating_window.close()
        self.close()
        # 强制退出应用
        import sys
        QApplication.instance().quit()
        sys.exit(0)
    
    def force_exit_app(self):
        """强制退出应用，不弹出确认窗口"""
        self.tray_icon.hide()
        # 关闭悬浮窗口
        if hasattr(self, 'floating_window'):
            self.floating_window.close()
        # 强制退出应用，不调用 self.close()，避免触发 closeEvent 方法
        import sys
        QApplication.instance().quit()
        sys.exit(0)
    
    def handle_login_cancel(self, login_dialog):
        """处理取消登录逻辑"""
        # 弹出退出确认窗口
        msg_box = QMessageBox()
        msg_box.setWindowTitle("退出确认")
        msg_box.setText("确定要退出软件吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加中文按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ok_button:
            # 点击确定，直接退出应用
            login_dialog.reject()
            # 确保彻底退出，不返回show_login_dialog方法
            import sys
            self.tray_icon.hide()
            if hasattr(self, 'floating_window'):
                self.floating_window.close()
            self.close()
            # 强制退出应用
            QApplication.instance().quit()
            sys.exit(0)
        else:
            # 点击取消
            # 检查是否未设置主密码（通过检查数据库文件是否存在）
            if not os.path.exists(self.db_file):
                # 未设置主密码，跳转到设置主密码页面
                # 先接受登录对话框，避免show_login_dialog方法调用close_app()
                login_dialog.accept()
                
                # 创建设置对话框并显示
                setup_dialog = QDialog(self)
                setup_dialog.setWindowTitle("首次运行设置")
                setup_dialog.setFixedSize(400, 250)
                setup_dialog.setModal(True)
                
                layout = QVBoxLayout(setup_dialog)
                
                info_label = QLabel("欢迎使用密码管理器！请设置您的主密码。")
                info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(info_label)
                
                form_layout = QFormLayout()
                
                # 主密码
                password_edit = QLineEdit()
                password_edit.setEchoMode(QLineEdit.EchoMode.Password)
                form_layout.addRow("主密码：", password_edit)
                
                # 确认主密码
                confirm_edit = QLineEdit()
                confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
                form_layout.addRow("确认主密码：", confirm_edit)
                
                layout.addLayout(form_layout)
                
                button_layout = QHBoxLayout()
                setup_btn = QPushButton("设置")
                setup_btn.clicked.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
                exit_btn = QPushButton("退出")
                exit_btn.clicked.connect(lambda: self.force_exit_app())
                
                button_layout.addStretch()
                button_layout.addWidget(setup_btn)
                button_layout.addWidget(exit_btn)
                
                layout.addLayout(button_layout)
                
                # 回车键设置
                password_edit.returnPressed.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
                confirm_edit.returnPressed.connect(lambda: self.setup_master_password(password_edit.text(), confirm_edit.text(), setup_dialog))
                
                # 显示设置对话框
                result = setup_dialog.exec()
                
                # 如果用户设置了主密码，显示主窗口
                if result == QDialog.DialogCode.Accepted:
                    # 强制显示主窗口并激活到前台
                    self.showNormal()
                    self.activateWindow()
                    self.raise_()
                    # 确保窗口状态正确
                    self.setWindowState(Qt.WindowState.WindowActive)
                    self.setFocus()
                # 如果用户点击了右上角的 × 关闭按钮，彻底退出软件
                else:
                    self.force_exit_app()
            else:
                # 已设置主密码，关闭退出确认窗口，保持登录对话框显示（返回登录页面）
                # 先接受登录对话框，避免show_login_dialog方法调用close_app()
                login_dialog.accept()
                # 重新显示登录对话框
                self.show_login_dialog()
    
    def show_normal(self):
        """显示主窗口"""
        # 检查是否已锁定
        if not self.master_password:
            # 检查是否已有登录对话框显示
            if self.login_dialog_visible:
                return
            
            # 已锁定，显示登录对话框
            self.login_dialog_visible = True
            
            login_dialog = QDialog(self)
            login_dialog.setWindowTitle("登录")
            login_dialog.setFixedSize(300, 150)
            login_dialog.setModal(True)
            
            layout = QVBoxLayout(login_dialog)
            
            form_layout = QFormLayout()
            password_label = QLabel("主密码：")
            password_edit = QLineEdit()
            password_edit.setEchoMode(QLineEdit.EchoMode.Password)
            form_layout.addRow(password_label, password_edit)
            
            layout.addLayout(form_layout)
            
            # 忘记密码按钮
            forgot_layout = QHBoxLayout()
            forgot_btn = QPushButton("忘记密码？")
            forgot_btn.clicked.connect(lambda: self.forgot_password(login_dialog))
            forgot_layout.addWidget(forgot_btn)
            forgot_layout.addStretch()
            layout.addLayout(forgot_layout)
            
            button_layout = QHBoxLayout()
            login_btn = QPushButton("登录")
            login_btn.clicked.connect(lambda: self.login(password_edit.text(), login_dialog))
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(login_dialog.reject)
            
            button_layout.addStretch()
            button_layout.addWidget(login_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # 回车键登录
            password_edit.returnPressed.connect(lambda: self.login(password_edit.text(), login_dialog))
            
            try:
                result = login_dialog.exec()
                if result != QDialog.DialogCode.Accepted:
                    # 登录取消，保持隐藏状态
                    return
            finally:
                # 无论登录成功还是失败，都重置标志
                self.login_dialog_visible = False
        else:
            # 未锁定，直接显示主窗口
            self.show()
            self.activateWindow()
            self.raise_()
    
    def changeEvent(self, event):
        """窗口状态变化事件"""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                # 最小化到托盘
                self.hide()
                # 只有在启用了最小化锁定选项时才启动倒计时
                if self.master_password and self.settings["lock_on_minimize"]:
                    self.lock_timer.start()
            elif self.isVisible() and self.master_password:
                # 窗口恢复可见时重置定时器
                self.reset_lock_timer()
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件，重置自动锁定定时器"""
        self.reset_lock_timer()
        super().mouseMoveEvent(event)
    
    def keyPressEvent(self, event):
        """键盘按键事件，重置自动锁定定时器"""
        self.reset_lock_timer()
        super().keyPressEvent(event)
    
    def focusInEvent(self, event):
        """窗口获得焦点事件，重置自动锁定定时器"""
        self.reset_lock_timer()
        super().focusInEvent(event)
    
    def reset_lock_timer(self):
        """重置自动锁定定时器"""
        if self.master_password:  # 只有在登录状态下才重置定时器
            # 只有在窗口可见且启用了自动锁定时才重置定时器
            if self.isVisible() and self.settings.get("auto_lock_time", 5) > 0:
                self.lock_timer.start()
    
    def closeEvent(self, event):
        """关闭事件"""
        # 确认关闭
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认退出")
        msg_box.setText("确定要退出密码管理器吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ok_button:
            self.close_app()
            event.accept()
        else:
            event.ignore()
    
    def verify_master_password(self, password):
        """验证主密码"""
        return self.crypto_manager.verify_master_password(self.db_file, password)
    
    def export_passwords(self):
        """导出原始密码数据"""
        # 文件选择对话框
        file_path, _ = QFileDialog.getSaveFileName(self, "选择导出文件", "passwords_export.txt", "Text Files (*.txt);;CSV Files (*.csv)")
        if not file_path:
            return
        
        try:
            # 准备导出数据
            export_data = []
            for entry_id in self.entries_order:
                entry = self.entries[entry_id]
                export_data.append({
                    "website_name": entry["website_name"],
                    "url": entry["url"],
                    "username": entry["username"],
                    "password": entry["password"],
                    "note": entry.get("note", "")
                })
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.endswith('.csv'):
                    # CSV格式
                    f.write("网站名,网址,账号,密码,备注\n")
                    for item in export_data:
                        f.write(f"{item['website_name']},{item['url']},{item['username']},{item['password']},{item['note']}\n")
                else:
                    # 文本格式
                    for item in export_data:
                        f.write(f"网站名: {item['website_name']}\n")
                        f.write(f"网址: {item['url']}\n")
                        f.write(f"账号: {item['username']}\n")
                        f.write(f"密码: {item['password']}\n")
                        if item['note']:
                            f.write(f"备注: {item['note']}\n")
                        f.write("-" * 50 + "\n")
            
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("成功")
            msg_box.setText(f"密码数据已成功导出到\n{file_path}")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"导出失败：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
