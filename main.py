import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from main_window import MainWindow
from floating_window import FloatingWindow

def main():
    """主程序入口"""
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("密码管理器")
    app.setApplicationVersion("1.1.2")
    app.setOrganizationName("幽灵足迹")
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    # 设置全局样式
    app.setStyle("Fusion")
    
    # 创建主窗口
    main_window = MainWindow()
    
    # 创建悬浮窗口
    floating_window = FloatingWindow(main_window)
    
    # 设置悬浮窗口为应用程序的子窗口
    main_window.floating_window = floating_window
    
    # 显示主窗口
    main_window.show()
    
    # 启动应用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
