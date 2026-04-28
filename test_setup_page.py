#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试脚本：单独打开设置主密码页面
"""

import sys
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow

if __name__ == "__main__":
    # 创建应用实例
    app = QApplication(sys.argv)
    
    # 创建主窗口实例
    main_window = MainWindow()
    
    # 直接调用 setup_first_run 方法打开设置主密码页面
    main_window.setup_first_run()
    
    # 退出应用
    sys.exit(app.exec())
