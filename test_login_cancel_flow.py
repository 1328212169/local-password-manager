#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：测试登录取消流程
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 创建主窗口实例
    main_window = MainWindow()
    
    # 打印初始状态
    print(f"初始状态 - master_password: '{main_window.master_password}'")
    print(f"初始状态 - db_file exists: {main_window.db_file}")
    
    # 启动应用
    sys.exit(app.exec())
