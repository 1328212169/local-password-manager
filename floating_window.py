from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QTimer, QUrl, QPoint, QSize
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut

class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        # 设置父窗口，避免关闭时触发应用程序退出
        super().__init__(parent)
        self.setWindowTitle("密码管理器 - 快速访问")
        self.resize(350, 400)  # 设置窗口尺寸为用户指定大小
        
        # 保留置顶属性，但确保窗口可以正常接收事件
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
        # 设置为普通窗口，确保可以正常接收用户输入
        self.setWindowFlag(Qt.WindowType.Window)
        
        # 保存对主窗口的引用，用于获取数据
        self.main_window = parent
        
        # 移除半透明背景，使用系统默认背景
        
        # 初始化数据
        self.entries = {}
        self.entries_order = []
        self.filtered_entries = []
        
        # 剪贴板定时器
        self.clipboard_timer = QTimer()
        self.clipboard_timer.setSingleShot(True)
        self.clipboard_timer.timeout.connect(self.clear_clipboard)
        
        # 初始化界面
        self.init_ui()
        
        # 初始化全局快捷键
        self.init_shortcuts()
        
        # 默认隐藏
        self.hide()
    
    def init_ui(self):
        """初始化界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 移除自定义样式，使用系统默认窗口样式
        self.setStyleSheet("")
        
        # 移除自定义标题栏，使用系统标准标题栏
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索网站名或账号...")
        self.search_edit.textChanged.connect(self.filter_entries)
        # 设置搜索框样式，使用更深的边框颜色
        self.search_edit.setStyleSheet("""
            QLineEdit {
                border: 1px solid #bdbdbd;
            }
        """)
        search_layout.addWidget(QLabel("搜索："))
        search_layout.addWidget(self.search_edit)
        main_layout.addLayout(search_layout)
        
        # 列表
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.open_website)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        main_layout.addWidget(self.list_widget)
        
        # 当前选中的条目
        self.current_entry = None
        
        # 按钮栏
        button_layout = QHBoxLayout()
        
        self.fill_user_btn = QPushButton("填充账号")
        self.fill_user_btn.clicked.connect(self.fill_username)
        
        self.fill_pass_btn = QPushButton("填充密码")
        self.fill_pass_btn.clicked.connect(self.fill_password)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_entries)
        
        button_layout.addWidget(self.fill_user_btn)
        button_layout.addWidget(self.fill_pass_btn)
        button_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(button_layout)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("font-size: 10px; color: #666666;")
        main_layout.addWidget(self.status_label)
    
    def init_shortcuts(self):
        """初始化快捷键"""
        # 全局快捷键 Ctrl+Alt+P 显示/隐藏窗口
        self.show_shortcut = QShortcut(QKeySequence("Ctrl+Alt+P"), self)
        self.show_shortcut.activated.connect(self.toggle_visibility)
        
        # ESC 键隐藏窗口
        self.hide_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.hide_shortcut.activated.connect(self.hide)
        
        # Ctrl+F 聚焦搜索框
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.search_edit.setFocus)
    
    def toggle_visibility(self):
        """切换窗口显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.search_edit.setFocus()
            self.refresh_entries()
    
    def set_entries(self, entries, entries_order):
        """设置密码条目数据"""
        self.entries = entries
        self.entries_order = entries_order
        self.filter_entries(self.search_edit.text())
    
    def filter_entries(self, text):
        """根据搜索文本过滤条目"""
        self.list_widget.clear()
        self.filtered_entries = []
        
        if not text:
            # 显示所有条目
            for entry_id in self.entries_order:
                if entry_id in self.entries:
                    self.add_entry_to_list(self.entries[entry_id])
        else:
            # 过滤条目
            for entry_id in self.entries_order:
                entry = self.entries.get(entry_id)
                if entry and (
                    text.lower() in entry['website_name'].lower() or 
                    text.lower() in entry['username'].lower()
                ):
                    self.add_entry_to_list(entry)
        
        # 更新状态
        self.status_label.setText(f"找到 {self.list_widget.count()} 个匹配项")
    
    def add_entry_to_list(self, entry):
        """添加条目到列表"""
        item = QListWidgetItem()
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        
        # 为条目添加样式，使其看起来像独立的卡片
        item_widget.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border: 1px solid #bdbdbd;
                border-radius: 4px;
            }
        """)
        
        website_label = QLabel(f"<b>{entry['website_name']}</b>")
        website_label.setStyleSheet("font-size: 14px;")  # 增大字体，确保清晰可见
        
        username_label = QLabel(f"账号: {entry['username']}")
        username_label.setStyleSheet("font-size: 12px; color: #666666;")  # 增大字体，确保清晰可见
        
        item_layout.addWidget(website_label)
        item_layout.addWidget(username_label)
        item_layout.setContentsMargins(12, 12, 12, 12)  # 增加边距，提升可读性
        
        # 为条目设置合适的高度和间距
        item.setSizeHint(item_widget.sizeHint() + QSize(0, 8))
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, item_widget)
        
        # 存储条目数据
        item.setData(Qt.ItemDataRole.UserRole, entry)
        self.filtered_entries.append(entry)
    
    def on_item_clicked(self, item):
        """列表项点击事件"""
        self.current_entry = item.data(Qt.ItemDataRole.UserRole)
    
    def fill_username(self):
        """填充账号（复制到剪贴板）"""
        if self.current_entry:
            username = self.current_entry['username']
            self.copy_to_clipboard(username)
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先选择一个条目")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.setParent(None)
            msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()
    
    def fill_password(self):
        """填充密码（复制到剪贴板）"""
        if self.current_entry:
            password = self.current_entry['password']
            self.copy_to_clipboard(password)
        else:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先选择一个条目")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.setParent(None)
            msg_box.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
            msg_box.exec()
    
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板，15秒后自动清空"""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        
        # 启动定时器，15秒后清空剪贴板
        self.clipboard_timer.start(15000)
        
        # 显示提示
        self.status_label.setText(f"已复制到剪贴板，15秒后自动清空")
    
    def clear_clipboard(self):
        """清空剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.clear()
        self.status_label.setText("剪贴板已清空")
    
    def open_website(self, item):
        """双击打开网站"""
        entry = item.data(Qt.ItemDataRole.UserRole)
        if entry and entry['url']:
            QDesktopServices.openUrl(QUrl(entry['url']))
    
    def refresh_entries(self):
        """刷新条目数据"""
        # 从主窗口获取最新数据
        if self.main_window:
            self.entries = self.main_window.entries
            self.entries_order = self.main_window.entries_order
            self.filter_entries(self.search_edit.text())
            self.status_label.setText("数据已刷新")
    
    # 移除自定义鼠标拖动事件，使用系统标准窗口拖动功能
    
    def show(self):
        """显示窗口，居中屏幕"""
        super().show()
        # 调整窗口位置到屏幕中央
        screen = self.screen().geometry()
        window = self.geometry()
        x = (screen.width() - window.width()) // 2
        y = (screen.height() - window.height()) // 2
        self.move(x, y)
    
    def toggle_theme(self, theme):
        """切换主题"""
        # 使用系统默认样式，不需要手动设置样式表
        pass
    
    def closeEvent(self, event):
        """关闭事件，只隐藏窗口，不关闭应用"""
        self.hide()
        event.ignore()
