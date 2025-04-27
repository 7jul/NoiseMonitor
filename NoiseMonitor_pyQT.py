from PyQt5.QtCore import Qt  # 添加这行导入
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton)
from PyQt5.QtCore import QTimer
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from datetime import datetime
import sys

class NoiseMonitorQt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("自习时间环境音量评分")
        
        # 音频参数
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        
        # 初始化音频流
        self.p = pyaudio.PyAudio()
        self.stream = None
        
        # 评分数据
        self.start_time = None
        self.db_values = []
        self.is_monitoring = False
        
        # 创建主界面
        self.init_ui()
        
    def init_ui(self):
        # 主窗口布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # 标题
        title_label = QLabel("自习时间环境音量评分")
        title_label.setStyleSheet("font: bold 14pt 'Microsoft YaHei'")
        layout.addWidget(title_label, alignment=Qt.AlignCenter)
        
        # 波形图
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_ylim(0, 80)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylabel('分贝(dB)')
        
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始计时")
        self.start_btn.setStyleSheet("font: 14pt 'Microsoft YaHei'")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        control_layout.addWidget(self.start_btn)
        
        # 添加重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setStyleSheet("font: 14pt 'Microsoft YaHei'")
        self.reset_btn.clicked.connect(self.reset_monitoring)
        control_layout.addWidget(self.reset_btn)

        self.result_label = QLabel("平均分贝: -- dB")
        self.result_label.setStyleSheet("font: 14pt 'Microsoft YaHei'")
        control_layout.addWidget(self.result_label)
        
        layout.addLayout(control_layout)
        
        # 版权信息
        copyright_label = QLabel("@天津市南开区南开小学-7jul")
        copyright_label.setStyleSheet("font: 12pt")
        layout.addWidget(copyright_label, alignment=Qt.AlignCenter)
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(50)
        
    def calculate_db(self, data):
        rms = np.sqrt(np.mean(np.square(data.astype(np.float32))))
        return 20 * np.log10(max(1e-10, rms/32768.0)) + 60
        
    def update_plot(self):
        if self.stream and self.is_monitoring:
            data = np.frombuffer(
                self.stream.read(self.CHUNK, exception_on_overflow=False),
                dtype=np.int16
            )
            db = self.calculate_db(data)
            self.db_values.append(db)
            
            # 更新波形图
            x_data = np.linspace(0, 100, len(self.db_values[-100:]))
            self.line.set_data(x_data, self.db_values[-100:])
            self.ax.relim()
            self.ax.autoscale_view()
            self.canvas.draw()
        
    def toggle_monitoring(self):
        if not self.is_monitoring:
            # 开始监测
            self.stream = self.p.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            self.start_time = datetime.now()
            self.db_values = []
            self.is_monitoring = True
            self.start_btn.setText("停止计时")
        else:
            # 停止监测
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                
            avg_db = np.mean(self.db_values) if self.db_values else 0
            duration = datetime.now() - self.start_time
            minutes = duration.seconds // 60
            seconds = duration.seconds % 60
            self.result_label.setText(
                f"平均分贝: {avg_db:.1f} dB    持续时间: {minutes}分{seconds}秒"
            )
            self.is_monitoring = False
            self.start_btn.setText("开始计时")
    
    def reset_monitoring(self):
        """重置监测数据"""
        if self.is_monitoring:
            self.toggle_monitoring()  # 如果正在监测，先停止
        
        # 重置数据
        self.db_values = []
        self.start_time = None
        
        # 重置波形图
        self.line.set_data([], [])
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()
        
        # 重置显示
        self.result_label.setText("平均分贝: -- dB")
        self.start_btn.setText("开始计时")
    
    def closeEvent(self, event):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NoiseMonitorQt()
    window.show()
    sys.exit(app.exec_())