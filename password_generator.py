from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QCheckBox, QPushButton, QLineEdit,
                             QGroupBox, QGridLayout, QApplication)
from PyQt6.QtCore import Qt
import secrets
import string

class PasswordGenerator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("密码生成器")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        self.generated_password = ""
        
        self.init_ui()
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 长度设置
        length_layout = QHBoxLayout()
        length_label = QLabel("密码长度：")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setRange(8, 64)
        self.length_spinbox.setValue(16)
        length_layout.addWidget(length_label)
        length_layout.addWidget(self.length_spinbox)
        length_layout.addStretch()
        main_layout.addLayout(length_layout)
        
        # 字符类型选择
        char_group = QGroupBox("字符类型")
        char_layout = QGridLayout()
        
        self.uppercase_check = QCheckBox("大写字母 (A-Z)")
        self.uppercase_check.setChecked(True)
        self.lowercase_check = QCheckBox("小写字母 (a-z)")
        self.lowercase_check.setChecked(True)
        self.digits_check = QCheckBox("数字 (0-9)")
        self.digits_check.setChecked(True)
        self.symbols_check = QCheckBox("符号 (!@#$%^&*()_+-=[]{}|;:,.<>?)")
        self.symbols_check.setChecked(True)
        
        char_layout.addWidget(self.uppercase_check, 0, 0)
        char_layout.addWidget(self.lowercase_check, 1, 0)
        char_layout.addWidget(self.digits_check, 0, 1)
        char_layout.addWidget(self.symbols_check, 1, 1)
        char_group.setLayout(char_layout)
        main_layout.addWidget(char_group)
        
        # 高级选项
        advanced_layout = QHBoxLayout()
        self.exclude_similar_check = QCheckBox("排除易混淆字符 (0O1lI)")
        advanced_layout.addWidget(self.exclude_similar_check)
        advanced_layout.addStretch()
        main_layout.addLayout(advanced_layout)
        
        # 密码显示
        password_layout = QHBoxLayout()
        self.password_lineedit = QLineEdit()
        self.password_lineedit.setReadOnly(True)
        self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_lineedit.setMinimumHeight(30)
        
        self.show_password_check = QCheckBox("显示密码")
        self.show_password_check.stateChanged.connect(self.toggle_password_visibility)
        
        password_layout.addWidget(self.password_lineedit)
        password_layout.addWidget(self.show_password_check)
        main_layout.addLayout(password_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("生成密码")
        self.generate_btn.clicked.connect(self.generate_password)
        
        self.copy_btn = QPushButton("复制到剪贴板")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(self.generate_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.ok_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # 初始生成密码
        self.generate_password()
    
    def toggle_password_visibility(self, state):
        """切换密码显示/隐藏状态"""
        if state == Qt.CheckState.Checked.value:
            self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def generate_password(self):
        """生成随机密码"""
        # 获取字符集
        chars = ""
        
        if self.uppercase_check.isChecked():
            chars += string.ascii_uppercase
        if self.lowercase_check.isChecked():
            chars += string.ascii_lowercase
        if self.digits_check.isChecked():
            chars += string.digits
        if self.symbols_check.isChecked():
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
        # 排除易混淆字符
        if self.exclude_similar_check.isChecked():
            chars = chars.translate(str.maketrans('', '', '0O1lI'))
        
        # 确保至少有一种字符类型被选中
        if not chars:
            self.password_lineedit.setText("请至少选择一种字符类型")
            return
        
        # 生成密码
        length = self.length_spinbox.value()
        password = ''.join(secrets.choice(chars) for _ in range(length))
        
        self.generated_password = password
        self.password_lineedit.setText(password)
    
    def copy_to_clipboard(self):
        """复制密码到剪贴板"""
        if self.generated_password:
            clipboard = self.parent().clipboard() if self.parent() else QApplication.clipboard()
            clipboard.setText(self.generated_password)
    
    def get_password(self):
        """返回生成的密码"""
        return self.generated_password
