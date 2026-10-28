from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QApplication)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
import json
import re
import urllib.request

# GitHub 仓库信息（用于检查更新）
GITHUB_REPO = "1328212169/local-password-manager"
RELEASES_PAGE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def parse_version(version_str: str) -> tuple:
    """将 'v1.2.3' / '1.2.3' 解析为 (1, 2, 3) 元组用于版本比较"""
    nums = re.findall(r'\d+', version_str)
    return tuple(int(n) for n in nums) if nums else (0,)


class UpdateCheckThread(QThread):
    """后台更新检查线程，避免阻塞界面"""
    result = pyqtSignal(dict)  # {"ok": bool, "tag": str, "url": str}

    def run(self):
        try:
            req = urllib.request.Request(
                API_URL,
                headers={
                    "User-Agent": "password-manager-update-checker",
                    "Accept": "application/vnd.github+json"
                }
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            self.result.emit({
                "ok": True,
                "tag": data.get("tag_name", ""),
                "url": data.get("html_url", RELEASES_PAGE_URL)
            })
        except Exception:
            self.result.emit({"ok": False, "tag": "", "url": RELEASES_PAGE_URL})


class AboutDialog(QDialog):
    """关于对话框：显示版本信息并检查更新"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于 密码管理器")
        self.setFixedSize(420, 300)
        self.setModal(True)

        self.current_version = QApplication.instance().applicationVersion() or "1.2.3"
        self.latest_url = RELEASES_PAGE_URL
        self.check_thread = None

        self.init_ui()
        self.finished.connect(self._cleanup_thread)
        self.check_for_updates()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # 软件名称
        title_label = QLabel("密码管理器")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 当前版本
        version_label = QLabel(f"当前版本：v{self.current_version}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(version_label)

        # 软件信息
        info_label = QLabel("一个安全、易用的本地密码管理工具\n\n开发者：幽灵足迹\n许可证：MIT")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(info_label)

        main_layout.addStretch()

        # 更新检查状态
        self.status_label = QLabel("正在检查更新...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # 按钮栏
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("前往下载最新版本")
        self.download_btn.setVisible(False)
        self.download_btn.clicked.connect(self.open_download_page)

        self.recheck_btn = QPushButton("重新检查")
        self.recheck_btn.clicked.connect(self.check_for_updates)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.accept)

        button_layout.addWidget(self.download_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.recheck_btn)
        button_layout.addWidget(self.close_btn)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def check_for_updates(self):
        """在后台线程中检查是否有新版本"""
        if self.check_thread is not None and self.check_thread.isRunning():
            return

        self.status_label.setText("正在检查更新...")
        self.download_btn.setVisible(False)
        self.recheck_btn.setEnabled(False)

        thread = UpdateCheckThread()
        self.check_thread = thread
        thread.result.connect(self.on_check_result)
        thread.finished.connect(self.on_check_finished)
        thread.finished.connect(thread.deleteLater)  # 线程对象自我清理
        thread.start()

    def on_check_finished(self):
        self.recheck_btn.setEnabled(True)
        self.check_thread = None

    def on_check_result(self, result: dict):
        if not result["ok"]:
            self.status_label.setText("检查更新失败，请检查网络后重试")
            return

        latest_version = result["tag"].lstrip("vV")
        if not latest_version:
            self.status_label.setText("检查更新失败，请稍后重试")
            return

        self.latest_url = result["url"] or RELEASES_PAGE_URL

        if parse_version(latest_version) > parse_version(self.current_version):
            self.status_label.setText(f"发现新版本：v{latest_version}，建议下载更新！")
            self.download_btn.setVisible(True)
        else:
            self.status_label.setText("当前已是最新版本")

    def open_download_page(self):
        """用默认浏览器打开最新版本下载页"""
        QDesktopServices.openUrl(QUrl(self.latest_url))

    def _cleanup_thread(self):
        """对话框关闭（确定/取消/X）时断开信号并等待后台线程结束，
        避免线程回调已销毁的对象，或进程退出时线程仍在运行导致崩溃。
        （请求最多 8 秒超时，通常 1 秒内完成）"""
        thread = self.check_thread
        self.check_thread = None
        if thread is not None:
            try:
                thread.result.disconnect(self.on_check_result)
                thread.finished.disconnect(self.on_check_finished)
            except TypeError:
                pass
            if thread.isRunning():
                thread.wait(9000)
