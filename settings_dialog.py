from PyQt6.QtWidgets import (QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QSpinBox, QCheckBox, QPushButton, QLineEdit,
                             QGroupBox, QGridLayout, QTabWidget, QMessageBox,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string
from datetime import datetime, timedelta

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        self.verification_code = ""
        self.code_expiry = None
        
        self.init_ui()
    
    def load_settings(self) -> dict:
        """加载设置"""
        default_settings = {
            "auto_lock_time": 5,  # 分钟
            "lock_on_minimize": True,
            "theme": "light",
            "email": "",
            "email_password": "",  # 加密存储
            "floating_window_shortcut": "Ctrl+Shift+X"  # 悬浮窗口快捷键
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return {**default_settings, **json.load(f)}
            except:
                return default_settings
        return default_settings
    
    def save_settings(self):
        """保存设置"""
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 安全设置
        self.security_tab = QWidget()
        self.init_security_tab()
        self.tab_widget.addTab(self.security_tab, "安全设置")
        
        # 外观设置
        self.appearance_tab = QWidget()
        self.init_appearance_tab()
        self.tab_widget.addTab(self.appearance_tab, "外观设置")
        
        # 邮箱设置
        self.email_tab = QWidget()
        self.init_email_tab()
        self.tab_widget.addTab(self.email_tab, "邮箱设置")
        
        # 文本导入
        self.text_import_tab = QWidget()
        self.init_text_import_tab()
        self.tab_widget.addTab(self.text_import_tab, "文本导入")
        
        main_layout.addWidget(self.tab_widget)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.accept)
        
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
    
    def init_security_tab(self):
        """初始化安全设置标签页"""
        layout = QVBoxLayout()
        
        # 自动锁定设置
        lock_group = QGroupBox("自动锁定")
        lock_layout = QVBoxLayout()
        
        # 闲置时间
        idle_layout = QHBoxLayout()
        idle_label = QLabel("闲置时间：")
        self.idle_spinbox = QSpinBox()
        self.idle_spinbox.setRange(1, 60)
        self.idle_spinbox.setValue(self.settings["auto_lock_time"])
        idle_unit = QLabel("分钟")
        idle_layout.addWidget(idle_label)
        idle_layout.addWidget(self.idle_spinbox)
        idle_layout.addWidget(idle_unit)
        idle_layout.addStretch()
        lock_layout.addLayout(idle_layout)
        
        # 最小化到托盘时锁定
        self.lock_on_minimize_check = QCheckBox("最小化到系统托盘时自动锁定")
        self.lock_on_minimize_check.setChecked(self.settings["lock_on_minimize"])
        lock_layout.addWidget(self.lock_on_minimize_check)
        
        lock_group.setLayout(lock_layout)
        layout.addWidget(lock_group)
        
        # 主密码设置
        password_group = QGroupBox("主密码设置")
        password_layout = QVBoxLayout()
        
        # 更改主密码按钮
        self.change_password_btn = QPushButton("更改主密码")
        self.change_password_btn.clicked.connect(self.change_master_password)
        password_layout.addWidget(self.change_password_btn)
        
        # 手动锁定按钮
        self.lock_now_btn = QPushButton("立即锁定应用")
        self.lock_now_btn.clicked.connect(self.lock_now)
        password_layout.addWidget(self.lock_now_btn)
        
        # 批量导出按钮
        self.batch_export_btn = QPushButton("批量导出密码")
        self.batch_export_btn.clicked.connect(self.batch_export_passwords)
        password_layout.addWidget(self.batch_export_btn)
        
        # 邮箱绑定状态提示
        email_status = QLabel(f"邮箱绑定状态：{'已绑定' if self.settings['email'] else '未绑定'}")
        email_status.setStyleSheet(f"color: {'green' if self.settings['email'] else 'red'}")
        password_layout.addWidget(email_status)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        layout.addStretch()
        self.security_tab.setLayout(layout)
    
    def init_appearance_tab(self):
        """初始化外观设置标签页"""
        layout = QVBoxLayout()
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QVBoxLayout()
        
        self.theme_group = QButtonGroup()
        
        self.light_theme_radio = QRadioButton("浅色主题")
        self.dark_theme_radio = QRadioButton("深色主题")
        
        self.theme_group.addButton(self.light_theme_radio, 0)
        self.theme_group.addButton(self.dark_theme_radio, 1)
        
        if self.settings["theme"] == "light":
            self.light_theme_radio.setChecked(True)
        else:
            self.dark_theme_radio.setChecked(True)
        
        theme_layout.addWidget(self.light_theme_radio)
        theme_layout.addWidget(self.dark_theme_radio)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 快捷键设置
        shortcut_group = QGroupBox("快捷键设置")
        shortcut_layout = QVBoxLayout()
        
        # 悬浮窗口快捷键
        shortcut_row = QHBoxLayout()
        shortcut_label = QLabel("悬浮窗唤起快捷键：")
        self.shortcut_edit = QLineEdit()
        self.shortcut_edit.setText(self.settings["floating_window_shortcut"])
        self.shortcut_edit.setPlaceholderText("例如：Ctrl+Shift+X")
        # 启用键盘事件捕获
        self.shortcut_edit.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.shortcut_edit.keyPressEvent = self.capture_shortcut
        shortcut_row.addWidget(shortcut_label)
        shortcut_row.addWidget(self.shortcut_edit)
        shortcut_layout.addLayout(shortcut_row)
        
        # 快捷键操作按钮
        button_row = QHBoxLayout()
        self.reset_shortcut_btn = QPushButton("重置默认")
        self.reset_shortcut_btn.clicked.connect(self.reset_shortcut)
        self.clear_shortcut_btn = QPushButton("清空")
        self.clear_shortcut_btn.clicked.connect(self.clear_shortcut)
        button_row.addWidget(self.reset_shortcut_btn)
        button_row.addWidget(self.clear_shortcut_btn)
        button_row.addStretch()
        shortcut_layout.addLayout(button_row)
        
        # 快捷键提示
        shortcut_tip = QLabel("提示：按下想要设置的快捷键组合，例如 Ctrl+Shift+X")
        shortcut_tip.setStyleSheet("font-size: 10px; color: #666666;")
        shortcut_layout.addWidget(shortcut_tip)
        
        shortcut_group.setLayout(shortcut_layout)
        layout.addWidget(shortcut_group)
        
        layout.addStretch()
        self.appearance_tab.setLayout(layout)
    
    def init_email_tab(self):
        """初始化邮箱设置标签页"""
        layout = QVBoxLayout()
        
        # 邮箱绑定
        email_group = QGroupBox("邮箱绑定（仅用于重置主密码）")
        email_layout = QGridLayout()
        
        # QQ邮箱
        email_label = QLabel("QQ邮箱：")
        self.email_lineedit = QLineEdit()
        self.email_lineedit.setText(self.settings["email"])
        email_layout.addWidget(email_label, 0, 0)
        email_layout.addWidget(self.email_lineedit, 0, 1, 1, 2)
        
        # 授权码
        password_label = QLabel("授权码：")
        self.password_lineedit = QLineEdit()
        self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_lineedit.setText(self.settings["email_password"])
        email_layout.addWidget(password_label, 1, 0)
        email_layout.addWidget(self.password_lineedit, 1, 1, 1, 2)
        
        # 显示密码
        self.show_password_check = QCheckBox("显示授权码")
        self.show_password_check.stateChanged.connect(self.toggle_password_visibility)
        email_layout.addWidget(self.show_password_check, 2, 1)
        
        # 验证邮箱
        self.verify_email_btn = QPushButton("验证邮箱")
        self.verify_email_btn.clicked.connect(self.verify_email)
        email_layout.addWidget(self.verify_email_btn, 3, 0)
        
        # 解绑邮箱
        self.unbind_email_btn = QPushButton("解绑邮箱")
        self.unbind_email_btn.clicked.connect(self.unbind_email)
        email_layout.addWidget(self.unbind_email_btn, 3, 1)
        
        email_group.setLayout(email_layout)
        layout.addWidget(email_group)
        
        layout.addStretch()
        self.email_tab.setLayout(layout)
    
    def toggle_password_visibility(self, state):
        """切换授权码显示/隐藏状态"""
        if state == Qt.CheckState.Checked.value:
            self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.password_lineedit.setEchoMode(QLineEdit.EchoMode.Password)
    
    def verify_email(self):
        """验证邮箱"""
        email = self.email_lineedit.text().strip()
        password = self.password_lineedit.text().strip()
        
        if not email or not password:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请输入邮箱和授权码")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 生成验证码
        self.verification_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.code_expiry = datetime.now() + timedelta(minutes=5)
        
        # 发送验证码
        if self.send_verification_email(email, password, self.verification_code):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("提示")
            msg_box.setText(f"验证码已发送到您的邮箱，5分钟内有效")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            
            # 显示验证码输入框
            self.code_dialog = QDialog(self)
            self.code_dialog.setWindowTitle("验证邮箱")
            self.code_dialog.setFixedSize(300, 150)
            
            code_layout = QVBoxLayout()
            code_label = QLabel("请输入收到的验证码：")
            self.code_lineedit = QLineEdit()
            self.code_lineedit.setPlaceholderText("6位数字验证码")
            
            code_btn_layout = QHBoxLayout()
            ok_btn = QPushButton("确定")
            ok_btn.clicked.connect(self.check_verification_code)
            cancel_btn = QPushButton("取消")
            cancel_btn.clicked.connect(self.code_dialog.reject)
            
            code_btn_layout.addStretch()
            code_btn_layout.addWidget(ok_btn)
            code_btn_layout.addWidget(cancel_btn)
            
            code_layout.addWidget(code_label)
            code_layout.addWidget(self.code_lineedit)
            code_layout.addLayout(code_btn_layout)
            
            self.code_dialog.setLayout(code_layout)
            if self.code_dialog.exec() == QDialog.DialogCode.Accepted:
                self.settings["email"] = email
                self.settings["email_password"] = password
                self.save_settings()
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("成功")
                msg_box.setText("邮箱绑定成功")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText("发送验证码失败，请检查邮箱和授权码是否正确")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def send_verification_email(self, to_email: str, password: str, code: str) -> bool:
        """发送验证邮件"""
        try:
            # QQ邮箱SMTP服务器设置
            smtp_server = "smtp.qq.com"
            smtp_port = 587
            from_email = to_email
            
            # 创建邮件
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = "密码管理器 - 主密码重置验证码"
            
            body = f"""您的密码管理器主密码重置验证码是：

{code}

验证码有效期为5分钟，请尽快使用。

请勿将此验证码泄露给他人！
"""
            
            msg.attach(MIMEText(body, "plain", "utf-8"))
            
            # 发送邮件
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(from_email, password)
            server.send_message(msg)
            server.quit()
            
            return True
        except Exception as e:
            print(f"发送邮件失败：{e}")
            return False
    
    def check_verification_code(self):
        """检查验证码"""
        input_code = self.code_lineedit.text().strip()
        
        if not input_code:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请输入验证码")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        if datetime.now() > self.code_expiry:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("验证码已过期")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            self.code_dialog.reject()
            return
        
        if input_code == self.verification_code:
            self.code_dialog.accept()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("验证码错误")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def unbind_email(self):
        """解绑邮箱"""
        if not self.settings["email"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("当前未绑定邮箱")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认解绑")
        msg_box.setText("确定要解绑邮箱吗？解绑后将无法通过邮箱重置主密码。")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮
        ok_button = msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        
        msg_box.exec()
        
        if msg_box.clickedButton() == ok_button:
            self.settings["email"] = ""
            self.settings["email_password"] = ""
            self.email_lineedit.clear()
            self.password_lineedit.clear()
            self.save_settings()
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("成功")
            msg_box.setText("邮箱已解绑")
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def init_text_import_tab(self):
        """初始化文本导入标签页"""
        layout = QVBoxLayout()
        
        # 导入按钮
        import_btn = QPushButton("导入TXT到数据库")
        import_btn.clicked.connect(self.import_txt_to_database)
        import_btn.setFixedSize(200, 40)
        
        # 居中布局
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(import_btn)
        center_layout.addStretch()
        
        layout.addStretch()
        layout.addLayout(center_layout)
        layout.addStretch()
        
        self.text_import_tab.setLayout(layout)
    
    def change_master_password(self):
        """更改主密码"""
        # 检查是否绑定邮箱
        if not self.settings["email"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("未绑定QQ邮箱，无法更改主密码")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
            return
        
        # 调用父窗口的主密码更改方法
        if hasattr(self.parent(), 'change_master_password'):
            self.parent().change_master_password()
        else:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("无法调用主密码更改功能")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.exec()
    
    def lock_now(self):
        """立即锁定应用"""
        # 调用父窗口的锁定方法
        if hasattr(self.parent(), 'lock_app'):
            self.parent().lock_app()
            self.accept()  # 关闭设置对话框
        else:
            QMessageBox.warning(self, "警告", "无法调用应用锁定功能")
    
    def accept(self):
        """保存设置并关闭对话框"""
        # 更新设置
        self.settings["auto_lock_time"] = self.idle_spinbox.value()
        self.settings["lock_on_minimize"] = self.lock_on_minimize_check.isChecked()
        
        # 更新主题
        if self.light_theme_radio.isChecked():
            self.settings["theme"] = "light"
        else:
            self.settings["theme"] = "dark"
        
        # 更新快捷键设置
        self.settings["floating_window_shortcut"] = self.shortcut_edit.text()
        
        self.save_settings()
        super().accept()
    
    def get_settings(self) -> dict:
        """返回当前设置"""
        return self.settings
    
    def import_txt_to_database(self):
        """导入TXT文件到数据库"""
        from PyQt6.QtWidgets import QFileDialog
        import uuid
        from datetime import datetime
        
        # 1. 弹出文件选择对话框
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("选择TXT文件")
        file_dialog.setNameFilter("文本文件 (*.txt)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec() != QFileDialog.DialogCode.Accepted:
            return
        
        selected_file = file_dialog.selectedFiles()[0]
        
        try:
            # 2. 调用txt_converter.py解析文件
            from txt_converter import parse_input_file
            websites = parse_input_file(selected_file)
            
            if not websites:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("提示")
                msg_box.setText("未解析到任何账号密码记录")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
                return
            
            # 3. 存入本地数据库
            success_count = 0
            error_count = 0
            error_reasons = []
            
            for website in websites:
                try:
                    # 生成唯一ID
                    entry_id = str(uuid.uuid4())
                    
                    # 构建条目
                    entry = {
                        'id': entry_id,
                        'website_name': website.get('name', ''),
                        'url': website.get('url', ''),
                        'username': website.get('username', ''),
                        'password': website.get('password', ''),
                        'note': website.get('note', ''),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # 调用父窗口的方法添加条目
                    if hasattr(self.parent(), 'entries') and hasattr(self.parent(), 'entries_order'):
                        self.parent().entries[entry_id] = entry
                        self.parent().entries_order.append(entry_id)
                        success_count += 1
                    else:
                        raise Exception("无法访问数据库")
                    
                except Exception as e:
                    error_count += 1
                    error_reasons.append(str(e))
            
            # 保存数据库
            if hasattr(self.parent(), 'save_db'):
                self.parent().save_db()
            
            # 4. 操作反馈
            if error_count == 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("成功")
                msg_box.setText(f"导入完成！共成功导入{success_count}条账号密码记录到数据库")
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
            elif success_count == 0:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("错误")
                msg_box.setText(f"导入失败：{'; '.join(error_reasons[:3])}")
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
            else:
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("部分成功")
                msg_box.setText(f"导入完成！成功导入{success_count}条，失败{error_count}条，失败原因：{'; '.join(error_reasons[:3])}")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                msg_box.exec()
            
            # 刷新主窗口表格
            if hasattr(self.parent(), 'refresh_table'):
                self.parent().refresh_table()
                
        except Exception as e:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("错误")
            msg_box.setText(f"导入失败：{str(e)}")
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            msg_box.exec()
    
    def reset_shortcut(self):
        """重置默认快捷键"""
        self.shortcut_edit.setText("Ctrl+Shift+X")
    
    def clear_shortcut(self):
        """清空快捷键"""
        self.shortcut_edit.clear()
    
    def capture_shortcut(self, event):
        """捕获用户按下的快捷键组合"""
        modifiers = event.modifiers()
        key = event.key()
        
        # 忽略修饰键单独按下的情况
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return
        
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
        
        # 更新输入框
        if shortcut_parts:
            self.shortcut_edit.setText("+".join(shortcut_parts))
    
    def send_reset_code(self) -> bool:
        """发送重置主密码的验证码"""
        if not self.settings["email"] or not self.settings["email_password"]:
            return False
        
        # 生成验证码
        self.verification_code = ''.join(secrets.choice(string.digits) for _ in range(6))
        self.code_expiry = datetime.now() + timedelta(minutes=5)
        
        return self.send_verification_email(
            self.settings["email"], 
            self.settings["email_password"], 
            self.verification_code
        )
    
    def verify_reset_code(self, code: str) -> bool:
        """验证重置主密码的验证码"""
        if not code or datetime.now() > self.code_expiry:
            return False
        
        return code == self.verification_code
    
    def batch_export_passwords(self):
        """批量导出密码"""
        # 弹出密码验证对话框
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
        
        class PasswordVerifyDialog(QDialog):
            def __init__(self, parent=None):
                super().__init__(parent)
                self.setWindowTitle("验证主密码")
                self.setFixedSize(300, 150)
                self.setModal(True)
                
                self.password = ""
                self.init_ui()
            
            def init_ui(self):
                layout = QVBoxLayout()
                
                label = QLabel("请输入主密码以验证身份：")
                layout.addWidget(label)
                
                self.password_input = QLineEdit()
                self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
                self.password_input.setPlaceholderText("输入主密码")
                layout.addWidget(self.password_input)
                
                button_layout = QHBoxLayout()
                self.ok_btn = QPushButton("确定")
                self.ok_btn.clicked.connect(self.accept)
                self.cancel_btn = QPushButton("取消")
                self.cancel_btn.clicked.connect(self.reject)
                
                button_layout.addStretch()
                button_layout.addWidget(self.ok_btn)
                button_layout.addWidget(self.cancel_btn)
                
                layout.addLayout(button_layout)
                self.setLayout(layout)
            
            def accept(self):
                self.password = self.password_input.text().strip()
                if not self.password:
                    QMessageBox.warning(self, "警告", "请输入主密码")
                    return
                super().accept()
        
        # 显示验证对话框
        verify_dialog = PasswordVerifyDialog(self)
        if verify_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        password = verify_dialog.password
        
        # 验证主密码
        if hasattr(self.parent(), 'verify_master_password'):
            if not self.parent().verify_master_password(password):
                QMessageBox.warning(self, "错误", "主密码错误，导出失败")
                return
        else:
            QMessageBox.warning(self, "错误", "无法验证主密码")
            return
        
        # 执行导出
        if hasattr(self.parent(), 'export_passwords'):
            self.parent().export_passwords()
        else:
            QMessageBox.warning(self, "错误", "无法执行导出操作")
