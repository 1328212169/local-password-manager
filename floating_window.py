from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
                             QListWidgetItem, QPushButton, QLabel, QMessageBox, QApplication)
from PyQt6.QtCore import Qt, QTimer, QUrl, QPoint, QSize
from PyQt6.QtGui import QDesktopServices, QKeySequence, QShortcut

class FloatingWindow(QWidget):
    def __init__(self, parent=None):
        # 不设置父窗口，确保窗口独立于主窗口
        super().__init__()
        self.setWindowTitle("密码管理器 - 快速访问")
        self.resize(350, 400)  # 设置窗口尺寸为用户指定大小
        
        # 设置窗口标志
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)  # 始终置顶
        self.setWindowFlag(Qt.WindowType.Tool, True)  # 工具窗口，不在任务栏显示
        
        # 保存对主窗口的引用，用于获取数据
        self.main_window = parent
        
        # 快捷键对象
        self.show_shortcut = None
        self.shortcut_key = "Ctrl+Shift+X"
        
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
        
        # 安装事件过滤器，用于捕获全局键盘事件
        if QApplication.instance():
            QApplication.instance().installEventFilter(self)
        
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
        
        # 为按钮添加鼠标悬浮效果
        self.add_button_hover_effects()
        
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
        # 从设置中加载快捷键
        self.shortcut_key = "Ctrl+Shift+X"
        if self.main_window and hasattr(self.main_window, 'settings'):
            self.shortcut_key = self.main_window.settings.get("floating_window_shortcut", "Ctrl+Shift+X")
        
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
    
    def update_shortcut(self, shortcut_key):
        """更新快捷键设置"""
        # 更新快捷键
        self.shortcut_key = shortcut_key
    
    def eventFilter(self, obj, event):
        """事件过滤器，用于捕获全局键盘事件"""
        if event.type() == event.Type.KeyPress:
            # 构建当前按下的快捷键字符串
            modifiers = event.modifiers()
            key = event.key()
            
            # 忽略修饰键单独按下的情况
            if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
                return super().eventFilter(obj, event)
            
            # 构建快捷键字符串
            shortcut_parts = []
            if modifiers & Qt.KeyboardModifier.ControlModifier:
                shortcut_parts.append("Ctrl")
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                shortcut_parts.append("Shift")
            if modifiers & Qt.KeyboardModifier.AltModifier:
                shortcut_parts.append("Alt")
            if modifiers & Qt.KeyboardModifier.MetaModifier:
                shortcut_parts.append("Meta")
            
            # 添加按键名称
            key_name = QKeySequence(key).toString()
            if key_name:
                shortcut_parts.append(key_name)
            
            # 构建完整的快捷键字符串
            current_shortcut = "+".join(shortcut_parts)
            
            # 检查是否匹配设置的快捷键
            if current_shortcut == self.shortcut_key:
                self.toggle_visibility()
                return True
        
        return super().eventFilter(obj, event)
    
    def add_button_hover_effects(self):
        """为按钮添加鼠标悬浮效果"""
        # 为所有按钮添加事件处理器
        buttons = [self.fill_user_btn, self.fill_pass_btn, self.refresh_btn]
        
        for button in buttons:
            # 设置初始样式
            button.setStyleSheet(
                "QPushButton {\n"
                "    background-color: #ffffff;\n"
                "    border: 1px solid #bdbdbd;\n"
                "    border-radius: 4px;\n"
                "    padding: 6px 12px;\n"
                "    transition: all 0.2s ease;\n"
                "}\n"
                "QPushButton:hover {\n"
                "    background-color: #f0f0f0;\n"
                "    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);\n"
                "    transform: translateY(-2px);\n"
                "}\n"
            )
    
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
