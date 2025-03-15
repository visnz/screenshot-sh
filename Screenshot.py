import sys
import subprocess
import json
import ctypes
import os

# 获取脚本所在目录
def get_script_dir():
    if getattr(sys, 'frozen', False):  # 打包后的情况
        return os.path.dirname(sys.executable)
    else:  # 脚本运行的情况
        return os.path.dirname(os.path.abspath(__file__))

# 安装依赖库
def install_dependencies():
    required_libraries = ["PyQt5", "Pillow", "opencv-python", "psutil", "pywin32", "moviepy"]
    for lib in required_libraries:
        try:
            __import__(lib)
        except ImportError:
            print(f"{lib} 未安装，正在安装...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

install_dependencies()

import time
from datetime import datetime
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFileDialog, QCheckBox
)
from PyQt5.QtCore import QTimer, QUrl
from PyQt5.QtGui import QDesktopServices
from PIL import ImageGrab
import cv2
import psutil
import win32gui
import win32process
from moviepy.editor import VideoFileClip  # 用于视频格式转换

class ScreenshotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.screenshot_interval = 5  # 默认截图间隔（秒）
        self.save_path = "C:/Multishot"  # 默认保存路径
        self.privacy_apps = ["WeChat.exe", "QQ.exe"]  # 隐私规避软件列表
        self.timer = QTimer()
        self.timer.timeout.connect(self.take_screenshot)
        self.is_screenshot_running = False  # 截图状态
        self.delete_after_convert = False  # 是否在转码后删除原图片
        self.fps = 30  # 默认帧速率
        self.script_dir = get_script_dir()  # 获取脚本所在目录
        self.config_file = os.path.join(self.script_dir, "config.json")  # 配置文件路径
        self.init_ui()
        self.load_config()  # 加载配置

    def init_ui(self):
        self.setWindowTitle("自动截图工具")
        self.setGeometry(100, 100, 600, 300)

        # 主布局
        main_layout = QVBoxLayout()

        # 状态标签
        self.status_label = QLabel("状态：空闲")
        main_layout.addWidget(self.status_label)

        # 截图间隔和保存路径
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel("截图间隔（秒）：")
        self.interval_input = QLineEdit(str(self.screenshot_interval))
        self.interval_input.textChanged.connect(self.update_playback_speed)  # 截图间隔变化时更新倍速
        interval_layout.addWidget(self.interval_label)
        interval_layout.addWidget(self.interval_input)
        main_layout.addLayout(interval_layout)

        path_layout = QHBoxLayout()
        self.path_label = QLabel("保存路径：")
        self.path_input = QLineEdit(self.save_path)
        self.path_input.setReadOnly(True)  # 设置为只读
        path_layout.addWidget(self.path_label)
        path_layout.addWidget(self.path_input)
        main_layout.addLayout(path_layout)

        # 左右两列布局
        bottom_layout = QHBoxLayout()

        # 左侧布局（文件夹相关和截图控制）
        left_layout = QVBoxLayout()
        self.browse_button = QPushButton("选择存储目录")
        self.browse_button.clicked.connect(self.browse_folder)
        left_layout.addWidget(self.browse_button)

        self.open_folder_button = QPushButton("打开存储目录")
        self.open_folder_button.clicked.connect(self.open_save_folder)
        left_layout.addWidget(self.open_folder_button)

        self.start_button = QPushButton("开始截图")
        self.start_button.clicked.connect(self.start_screenshot)
        left_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("停止截图")
        self.stop_button.clicked.connect(self.stop_screenshot)
        left_layout.addWidget(self.stop_button)

        # 右侧布局（转码相关）
        right_layout = QVBoxLayout()
        self.convert_button = QPushButton("转码")
        self.convert_button.clicked.connect(self.convert_screenshots)
        right_layout.addWidget(self.convert_button)

        fps_layout = QHBoxLayout()
        self.fps_label = QLabel("视频帧速率（FPS）：")
        self.fps_input = QLineEdit(str(self.fps))
        self.fps_input.textChanged.connect(self.update_playback_speed)  # 帧速率变化时更新倍速
        fps_layout.addWidget(self.fps_label)
        fps_layout.addWidget(self.fps_input)
        right_layout.addLayout(fps_layout)

        self.playback_speed_label = QLabel("播放倍速：1.0 倍")
        right_layout.addWidget(self.playback_speed_label)

        self.delete_checkbox = QCheckBox("转码后删除原图片")
        self.delete_checkbox.stateChanged.connect(self.toggle_delete_after_convert)
        right_layout.addWidget(self.delete_checkbox)

        # 将左右布局添加到主布局
        bottom_layout.addLayout(left_layout)
        bottom_layout.addLayout(right_layout)
        bottom_layout.setStretch(0, 1)  # 使左右两列宽度相等
        bottom_layout.setStretch(1, 1)
        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # 初始化倍速显示
        self.update_playback_speed()

    def browse_folder(self):
        """弹出文件夹选择对话框"""
        folder = QFileDialog.getExistingDirectory(self, "选择保存路径", self.save_path)
        if folder:
            self.save_path = folder
            self.path_input.setText(folder)

    def start_screenshot(self):
        self.screenshot_interval = int(self.interval_input.text())
        self.fps = int(self.fps_input.text())
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        self.timer.start(self.screenshot_interval * 1000)
        self.is_screenshot_running = True
        self.status_label.setText("状态：▶截图中……")
        self.save_config()  # 保存配置
        QMessageBox.information(self, "提示", "截图已开始！")
        self.minimize_window()  # 最小化窗口

    def minimize_window(self):
        """最小化窗口"""
        self.showMinimized()  # 最小化程序窗口
        # 最小化命令行窗口
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # 6 表示最小化

    def stop_screenshot(self):
        self.timer.stop()
        self.is_screenshot_running = False
        self.status_label.setText("状态：空闲")
        QMessageBox.information(self, "提示", "截图已停止！")

    def take_screenshot(self):
        if self.is_privacy_window_active():
            print("隐私窗口，跳过截图")
            return

        today_folder = os.path.join(self.save_path, datetime.now().strftime("%m-%d"))
        if not os.path.exists(today_folder):
            os.makedirs(today_folder)

        screenshot_name = f"screenshot-{datetime.now().strftime('%d-%H-%M-%S')}.jpg"
        screenshot_path = os.path.join(today_folder, screenshot_name)
        ImageGrab.grab().save(screenshot_path)
        print(f"截图成功：{screenshot_path}")

    def is_privacy_window_active(self):
        window = win32gui.GetForegroundWindow()
        tid, pid = win32process.GetWindowThreadProcessId(window)
        process = psutil.Process(pid)
        for app in self.privacy_apps:
            if app.lower() in process.name().lower():
                return True
        return False

    def convert_screenshots(self):
        """转码按钮点击事件"""
        if self.is_screenshot_running:
            self.stop_screenshot()  # 如果正在截图，则停止截图
        if not os.path.exists(self.save_path):
            QMessageBox.warning(self, "警告", "保存路径不存在！")
            return

        # 获取用户输入的帧速率
        try:
            self.fps = int(self.fps_input.text())
            if self.fps <= 0:
                raise ValueError("帧速率必须为正整数")
        except ValueError as e:
            QMessageBox.warning(self, "错误", f"帧速率无效：{e}")
            return

        # 遍历保存路径下的子文件夹
        for folder_name in os.listdir(self.save_path):
            folder_path = os.path.join(self.save_path, folder_name)
            if os.path.isdir(folder_path) and "（已转换）" not in folder_name:  # 跳过已转换的文件夹
                # 检查文件夹中是否有截图文件
                images = [img for img in os.listdir(folder_path) if img.endswith(".jpg")]
                if images:
                    print(f"正在处理文件夹：{folder_path}")
                    self.generate_video(folder_path)
                else:
                    print(f"文件夹 {folder_path} 中没有截图文件，跳过")

    def generate_video(self, folder_path):
        """生成视频"""
        images = [img for img in os.listdir(folder_path) if img.endswith(".jpg")]
        if not images:
            print("没有截图文件，跳过视频生成")
            return

        images.sort()
        image_paths = [os.path.join(folder_path, img) for img in images]

        # 生成 AVI 视频
        frame = cv2.imread(image_paths[0])
        height, width, layers = frame.shape
        avi_video_name = os.path.join(folder_path, f"{os.path.basename(folder_path)}.avi")
        video = cv2.VideoWriter(avi_video_name, cv2.VideoWriter_fourcc(*'DIVX'), self.fps, (width, height))
        for image in image_paths:
            video.write(cv2.imread(image))
        video.release()  # 释放文件句柄
        print(f"AVI 视频生成成功：{avi_video_name}")

        # 转换为高质量 MOV 格式（使用 libx264 编码）
        base_name = os.path.basename(folder_path)
        mov_video_name = os.path.join(self.save_path, f"{base_name}.mov")
        counter = 1
        while os.path.exists(mov_video_name):
            mov_video_name = os.path.join(self.save_path, f"{base_name}（{counter}）.mov")
            counter += 1
        self.convert_to_high_quality_mov(avi_video_name, mov_video_name)
        print(f"高质量 MOV 视频生成成功：{mov_video_name}")

        # 删除 AVI 文件
        try:
            os.remove(avi_video_name)
            print(f"已删除 AVI 文件：{avi_video_name}")
        except PermissionError:
            print(f"无法删除 AVI 文件：{avi_video_name}，文件可能被占用")

        # 如果勾选了“转码后删除原图片”，则删除原图片
        if self.delete_after_convert:
            for image in image_paths:
                try:
                    os.remove(image)
                except PermissionError:
                    print(f"无法删除图片：{image}，文件可能被占用")
            print(f"已删除原图片：{folder_path}")
        else:
            # 将文件夹重命名为“日期+（已转换）”
            new_folder_name = f"{os.path.basename(folder_path)}（已转换）"
            new_folder_path = os.path.join(self.save_path, new_folder_name)
            if os.path.exists(new_folder_path):
                # 如果目标文件夹已存在，则将新截图文件移动到已存在的文件夹中
                for image in image_paths:
                    try:
                        shutil.move(image, new_folder_path)
                    except PermissionError:
                        print(f"无法移动图片：{image}，文件可能被占用")
                    except FileNotFoundError:
                        print(f"文件无法找到：{image}")
                print(f"已将新截图文件移动到：{new_folder_path}")
            else:
                # 如果目标文件夹不存在，则直接重命名
                os.rename(folder_path, new_folder_path)
                print(f"文件夹已重命名为：{new_folder_name}")

    def convert_to_high_quality_mov(self, input_video, output_video):
        """
        使用 moviepy 将视频转换为高质量 MOV 格式（libx264 编码）
        """
        try:
            clip = VideoFileClip(input_video)  # 从 AVI 文件读取
            clip.write_videofile(
                output_video,
                codec="libx264",  # 使用 libx264 编码
                bitrate="500M",   # 设置比特率为 500 Mbps
                fps=self.fps,     # 使用用户设置的帧速率
                preset="ultrafast",  # 编码速度（ultrafast 最快，veryslow 最慢但质量最高）
                threads=4         # 使用多线程加速
            )
        except Exception as e:
            print(f"视频转换失败：{e}")

    def toggle_delete_after_convert(self, state):
        """切换是否在转码后删除原图片"""
        self.delete_after_convert = state == 2  # 2 表示勾选状态

    def open_save_folder(self):
        """打开保存目录"""
        if os.path.exists(self.save_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.save_path))
        else:
            QMessageBox.warning(self, "警告", "保存路径不存在！")

    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.screenshot_interval = config.get("screenshot_interval", 5)
                self.save_path = config.get("save_path", "C:/Multishot")
                self.fps = config.get("fps", 30)
                # 更新 UI 控件的值
                self.interval_input.setText(str(self.screenshot_interval))
                self.path_input.setText(self.save_path)
                self.fps_input.setText(str(self.fps))
                self.update_playback_speed()  # 更新倍速显示

    def save_config(self):
        """保存配置文件"""
        config = {
            "screenshot_interval": self.screenshot_interval,
            "save_path": self.save_path,
            "fps": self.fps
        }
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def update_playback_speed(self):
        """更新播放倍速显示"""
        try:
            interval = float(self.interval_input.text())
            fps = float(self.fps_input.text())
            if interval <= 0 or fps <= 0:
                raise ValueError("截图间隔和帧速率必须为正数")
            playback_speed = interval * fps
            self.playback_speed_label.setText(f"播放倍速：{playback_speed:.1f} 倍")
        except ValueError:
            self.playback_speed_label.setText("播放倍速：无效输入")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScreenshotApp()
    window.show()
    sys.exit(app.exec_())