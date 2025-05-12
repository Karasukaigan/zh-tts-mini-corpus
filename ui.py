import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QMessageBox,
    QLabel, QPushButton, QProgressBar, QComboBox, QGridLayout, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QFont, QAction, QDesktopServices
from PyQt6.QtMultimedia import QMediaRecorder, QAudioInput, QMediaFormat, QMediaCaptureSession
from PyQt6.QtMultimedia import QMediaDevices, QMediaPlayer, QAudioOutput
import os
from pyqtgraph import PlotWidget
import numpy as np
from scipy.io import wavfile
import src.tools as tools
import src.output as output_tool

wav_output_path = "wav"
corpus_file_path = "corpus/zh_corpus_v1.json"

class SentenceBrowser(QMainWindow):
    def __init__(self):
        """初始化窗口"""
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setWindowTitle("音频录制器")
        self.setGeometry(100, 100, 1500, 600)

        # 录音初始化
        self.is_recording = False
        self.current_index = 0
        self.recorder = QMediaRecorder()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        print(f"当前音频输出设备: {self.audio_output.device().description()}")

        # 设置媒体会话
        self.capture_session = QMediaCaptureSession()
        self.capture_session.setRecorder(self.recorder)
        self.media_player.setAudioOutput(self.audio_output)

        # 音频输入设备
        self.audio_devices = QMediaDevices.audioInputs()
        if self.audio_devices:
            self.audio_input = QAudioInput(self.audio_devices[0])
            self.capture_session.setAudioInput(self.audio_input)
            print(f"当前音频输入设备: {self.audio_devices[0].description()}")
        else:
            print("[警告] 没有找到可用的音频输入设备")
            self.audio_input = None

        # 确保输出目录存在
        os.makedirs(wav_output_path, exist_ok=True)
        
        # 加载句子数据
        self.sentences = tools.load_sentences(corpus_file_path)
        if not self.sentences:
            sys.exit(1)
        self.keys = list(self.sentences.keys())
        
        # UI初始化
        self.center_window()
        self.init_menu()
        self.init_ui()
        self.apply_style()

    def center_window(self):
        """将窗口移动到屏幕中心"""
        self.move(self.screen().availableGeometry().center() - self.rect().center())
           
    def init_menu(self):
        """初始化菜单栏"""
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu("文件")

        open_dir_action = QAction("打开音频目录", self)
        open_dir_action.triggered.connect(self.open_audio_directory)
        file_menu.addAction(open_dir_action)

        clear_audio_action = QAction("清空已录制音频", self)
        clear_audio_action.triggered.connect(self.clear_recordings)
        file_menu.addAction(clear_audio_action)

        organize_action = QAction("保存到项目目录", self)
        organize_action.triggered.connect(self.organize_training_data)
        file_menu.addAction(organize_action)

        open_project_dir_action = QAction("打开项目目录", self)
        open_project_dir_action.triggered.connect(self.open_project_directory)
        file_menu.addAction(open_project_dir_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu("帮助")

        github_action = QAction("打开GitHub", self)
        github_action.triggered.connect(lambda: QDesktopServices.openUrl(
            QUrl("https://github.com/Karasukaigan/zh-tts-mini-corpus")
        ))
        help_menu.addAction(github_action)

        about_action = QAction("关于", self)
        about_action.triggered.connect(lambda: self.show_about_dialog())
        help_menu.addAction(about_action)

    def open_audio_directory(self):
        """打开音频文件所在目录"""
        tools.open_directory(wav_output_path)

    def clear_recordings(self):
        """清空已录制的音频文件"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认清空音频")
        msg_box.setText("确定要删除所有已录制的音频文件吗？此操作不可恢复。")
        confirm_button = msg_box.addButton("确认", QMessageBox.ButtonRole.AcceptRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(cancel_button)
        msg_box.exec()
        if msg_box.clickedButton() == confirm_button:
            output_dir = os.path.abspath(wav_output_path)
            if self.is_recording:
                self.stop_recording()
            self.media_player.stop()
            self.media_player.setSource(QUrl())
            for file in os.listdir(output_dir):
                file_path = os.path.join(output_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"无法删除文件 {file_path}: {e}")
            self.restart_application()

    def organize_training_data(self):
        """调用 output_tool.main() 来整理训练集"""
        project_name = self.project_name_edit.text().strip()
        if not project_name:
            project_name = "default"
        output_tool.main(tools.make_valid_filename(project_name), corpus_file_path, wav_output_path, -40, 500, 0)
        tools.open_directory(f'projects/{project_name}')

    def open_project_directory(self):
        """打开项目目录"""
        tools.open_directory("projects")

    def restart_application(self):
        """重启应用程序"""
        QApplication.quit()
        os.system(sys.executable + ' "' + os.path.abspath(sys.argv[0]) + '"')

    def show_about_dialog(self):
        """显示关于对话框"""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.NoIcon)
        msg_box.setWindowTitle("关于")
        html_text = """
<h2>音频录制器</h2>
<p>一个用于声音克隆文本集音频录制的工具。</p>
<p>版本: 1.0.0</p>
<p>作者: <a href="https://space.bilibili.com/2838092" style="text-decoration: none; color: #fff">鸦无量</a></p>
<p>贡献者:</p>
<ul>
    <li>暂无</li>
</ul>
<p>本软件遵循MIT许可证。</p>
"""
        msg_box.setTextFormat(Qt.TextFormat.RichText)
        msg_box.setText(html_text)
        ok_button = msg_box.addButton("确认", QMessageBox.ButtonRole.AcceptRole)
        msg_box.exec()
    
    def init_ui(self):
        """初始化界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # 项目名称输入框
        self.project_name_edit = QLineEdit(placeholderText="请输入项目名称")
        layout.addWidget(self.project_name_edit)

        # 录音设备下拉框
        self.device_combo = QComboBox()
        self.device_combo.addItems([device.description() for device in self.audio_devices])
        self.device_combo.currentIndexChanged.connect(self.change_audio_device)
        layout.addWidget(self.device_combo)
        
        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)
        
        # 进度文本
        self.progress_label = QLabel("", alignment=Qt.AlignmentFlag.AlignRight)
        self.progress_label.setFixedHeight(20)
        layout.addWidget(self.progress_label)
        
        # 句子显示区域
        self.key_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.key_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        
        self.sentence_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.sentence_label.setFont(QFont("Segoe UI", 20))
        self.sentence_label.setWordWrap(True)
        self.sentence_label.setMargin(20)
        
        layout.addStretch(1)
        layout.addWidget(self.key_label)
        layout.addWidget(self.sentence_label)
        layout.addStretch(1)

        # 音频统计信息标签
        self.audio_info_label = QLabel("", alignment=Qt.AlignmentFlag.AlignLeft)
        self.audio_info_label.setFixedHeight(18)
        self.audio_info_label.setContentsMargins(5, 0, 0, 0)
        layout.addWidget(self.audio_info_label)

        # 波形图
        self.waveform_plot = PlotWidget()
        layout.addWidget(self.waveform_plot)
        
        # 按钮区域
        button_layout = QGridLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        self.prev_button = QPushButton("上一句 (←)")
        self.prev_button.clicked.connect(self.show_previous)
        
        self.record_button = QPushButton("开始录制 (R)")
        self.record_button.clicked.connect(self.toggle_recording)

        self.play_button = QPushButton("试听音频 (P)")
        self.play_button.clicked.connect(self.play_audio)
        self.play_button.setEnabled(False)  # 默认禁用，只有录音完成后才启用
        
        self.next_button = QPushButton("下一句 (→)")
        self.next_button.clicked.connect(self.show_next)
        
        button_layout.addWidget(self.prev_button, 0, 0)
        button_layout.addWidget(self.record_button, 0, 1)
        button_layout.addWidget(self.play_button, 0, 2)
        button_layout.addWidget(self.next_button, 0, 3)

        button_layout.setColumnStretch(0, 1)
        button_layout.setColumnStretch(1, 1)
        button_layout.setColumnStretch(2, 1)
        button_layout.setColumnStretch(3, 1)
        
        layout.addLayout(button_layout)
        
        # 显示第一句
        self.update_display()

    def plot_waveform(self, file_path):
        """绘制波形图"""
        if not os.path.exists(file_path):
            return self.clear_waveform()

        sample_rate, data = wavfile.read(file_path)
        data = data[:, 0] if len(data.shape) > 1 else data  # 单声道处理
        original_dtype = data.dtype

        # 数据标准化
        data = data.astype(np.float64)
        if np.issubdtype(original_dtype, np.integer):
            data /= np.iinfo(original_dtype).max

        # 计算RMS值（平均音量）
        window_size = max(1, int(sample_rate * 0.01))  # 10ms窗口
        window = np.ones(window_size) / window_size
        rms = np.sqrt(np.convolve(data ** 2, window, 'same'))

        # dBFS转换
        epsilon = 1e-10
        rms = np.maximum(rms, epsilon)
        data_db = 20 * np.log10(rms)
        data_db = np.minimum(data_db, 0.0) # 将最大值限制在0dBFS

        # 统计信息
        filtered_data_db = data_db[data_db >= -30] # 过滤掉-30dB以下的数据（视为静音）
        avg_volume = np.mean(filtered_data_db) if len(filtered_data_db) > 0 else -float('inf')
        max_volume = np.max(filtered_data_db) if len(filtered_data_db) > 0 else -float('inf')

        # 绘图
        self.waveform_plot.clear()
        duration = len(data) / sample_rate  # 音频总时长(秒)
        time_axis = np.linspace(0, duration, len(data))
        self.waveform_plot.plot(time_axis, data_db, pen='b')
        self.waveform_plot.setLabels(left='Amplitude (dBFS)', bottom='Time (s)')
        self.waveform_plot.setTitle("Waveform in dBFS")
        self.waveform_plot.setXRange(0, duration)

        # 更新音频信息标签
        audio_info_text = (
            f"总时长: {duration:.2f} s | 采样率: {sample_rate} Hz | "
            f"平均音量: {avg_volume:.2f} dB | 最大音量: {max_volume:.2f} dB"
        )
        self.audio_info_label.setText(audio_info_text)
    
    def clear_waveform(self):
        """
        清空当前的波形图并重置音频信息标签。
        """
        self.waveform_plot.clear()
        self.audio_info_label.setText("")

    def keyPressEvent(self, event):
        """
        键盘按键事件处理函数，用于响应用户的快捷键操作。
        
        支持以下快捷键功能：
            - 左箭头（←）: 显示上一句待录音文本。
            - 右箭头（→）: 显示下一句待录音文本。
            - R 键      : 开始或停止录音操作。
            - P 键      : 播放当前句子对应的已录制音频文件。

        如果按下的是未绑定的功能键，则调用父类的 keyPressEvent 方法进行默认处理。

        参数:
            event (QKeyEvent): 包含按键信息的事件对象。
        """
        if event.key() == Qt.Key.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key.Key_R:
            self.toggle_recording()
        elif event.key() == Qt.Key.Key_P:
            self.play_audio()
        else:
            super().keyPressEvent(event)

    def change_audio_device(self, index):
        """切换音频设备"""
        if index < 0 or index >= len(self.audio_devices):
            return
        self.current_device_index = index
        selected_device = self.audio_devices[index]
        if self.audio_input:
            self.capture_session.setAudioInput(QAudioInput(selected_device))
            print(f"已切换到音频输入设备: {selected_device.description()}")

    def toggle_recording(self):
        """切换录制状态"""
        self.stop_recording() if self.is_recording else self.start_recording()

    def start_recording(self):
        """开始录制"""
        if not self.keys or not self.audio_input:
            return
        
        output_dir = os.path.abspath(wav_output_path)
        os.makedirs(output_dir, exist_ok=True)
            
        current_key = self.keys[self.current_index]
        output_file = os.path.join(output_dir, f"{current_key}.wav")
        
        # 设置录音格式
        format = QMediaFormat()
        format.setFileFormat(QMediaFormat.FileFormat.Wave)
        self.recorder.setMediaFormat(format)
        self.recorder.setOutputLocation(QUrl.fromLocalFile(output_file))
        
        self.recorder.record()
        self.is_recording = True
        self.record_button.setText("停止录制 (R)")
        
    def stop_recording(self):
        """停止录制"""
        self.recorder.stop()
        self.is_recording = False
        self.record_button.setText("开始录制 (R)")
        QTimer.singleShot(500, self.update_display)  # 500毫秒后执行
        
    def play_audio(self):
        """播放音频"""
        if not self.keys:
            return
        current_key = self.keys[self.current_index]
        audio_file = os.path.join(wav_output_path, f"{current_key}.wav")
        if not os.path.exists(audio_file):
            print(f"[错误] 音频文件 {audio_file} 不存在")
            return
        if self.is_recording:
            self.stop_recording()
        self.media_player.stop()    
        self.media_player.setSource(QUrl.fromLocalFile(audio_file))
        self.media_player.play()
        
    def apply_style(self):
        """应用样式"""
        style_file = "src/style.qss"
        with open(style_file, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())
    
    def update_display(self):
        """更新页面"""
        if not self.keys:
            return
            
        current_key = self.keys[self.current_index]
        self.key_label.setText(current_key)
        self.sentence_label.setText(self.sentences[current_key])
        
        # 更新进度
        progress = (self.current_index + 1) / len(self.keys) * 100
        self.progress_bar.setValue(int(progress))
        self.progress_label.setText(f"{self.current_index + 1}/{len(self.keys)}")
        
        # 更新按钮状态
        self.prev_button.setEnabled(self.current_index > 0)
        self.next_button.setEnabled(self.current_index < len(self.keys) - 1)

        # 如果正在录音，停止当前录音
        if self.is_recording:
            self.stop_recording()

        # 检查是否存在对应的音频文件
        audio_file = os.path.join(wav_output_path, f"{current_key}.wav")
        self.play_button.setEnabled(os.path.exists(audio_file))
        self.plot_waveform(audio_file)
        
    def show_previous(self):
        """显示上一个句子"""
        self.current_index = max(0, self.current_index - 1)
        self.update_display()

    def show_next(self):
        """显示下一个句子"""
        self.current_index = min(len(self.keys) - 1, self.current_index + 1)
        self.update_display()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SentenceBrowser()
    window.show()
    sys.exit(app.exec())