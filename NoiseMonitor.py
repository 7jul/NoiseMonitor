import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # 添加这行导入

class NoiseMonitor:
    def __init__(self):
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
        
        # 创建GUI
        self.root = tk.Tk()
        self.root.title("自习时间环境音量评分")
        self.root.grid_rowconfigure(0, weight=1)  # 添加弹性行
        self.root.grid_columnconfigure(0, weight=1)  # 添加弹性列
        
        # 主容器使用grid布局
        main_frame = tk.Frame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(1, weight=1)  # 波形图区域弹性
        main_frame.grid_columnconfigure(0, weight=1)
        
        # 标题和按钮区域
        header_frame = tk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")
        
        # 先创建fig和ax
        self.fig, self.ax = plt.subplots(figsize=(8, 3))
        self.line, = self.ax.plot([], [], 'b-')
        self.ax.set_ylim(0, 80)
        self.ax.set_xlim(0, 100)
        self.ax.set_ylabel('分贝(dB)')
        
        # 然后再创建canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=main_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # 控制面板使用grid布局
        control_frame = tk.Frame(main_frame)
        control_frame.grid(row=2, column=0, sticky="ew", pady=14)
        
        # 修改标题字体
        title_label = tk.Label(
            main_frame,
            text="自习时间环境音量评分",
            font=('SimSong', 18, 'bold')
        )
        title_label.grid(row=0, column=0, pady=10)
        
        # 修改按钮字体
        self.start_btn = ttk.Button(
            control_frame, 
            text="开始计时", 
            command=self.toggle_monitoring,
            style='Large.TButton'
        )
        self.start_btn.grid(row=0, column=0, padx=5, sticky="w")
        
        # 修改结果标签字体
        self.result_label = tk.Label(
            control_frame,
            text="平均分贝: -- dB",
            font=('SimSong', 18)
        )
        self.result_label.grid(row=0, column=1, padx=5, sticky="w")
        
        # 添加大按钮样式
        style = ttk.Style()
        style.configure('Large.TButton', font=('SimSong', 18))
        
        # 动画更新
        self.ani = FuncAnimation(
            self.fig,
            self.update_plot,
            frames=None,
            interval=50,
            blit=True,
            cache_frame_data=False  # 添加此参数
        )
        
        # 添加版权信息
        copyright_label = tk.Label(
            main_frame,
            text="@天津市南开区南开小学-7jul",
            font=('SimSong', 14)
        )
        copyright_label.grid(row=3, column=0, pady=10)
        
    def calculate_db(self, data):
        # 计算RMS值并转换为分贝
        rms = np.sqrt(np.mean(np.square(data.astype(np.float32))))
        # 16位音频的最大值为32768，使用20*log10(rms/32768)计算相对分贝
        return 20 * np.log10(max(1e-10, rms/32768.0)) + 90  # 加上90dB偏移使静音时显示30dB左右
        
    def update_plot(self, frame):
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
            
        return self.line,
    
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
            self.start_btn.config(text="停止计时")
        else:
            # 停止监测并计算平均分贝
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                
            avg_db = np.mean(self.db_values) if self.db_values else 0
            duration = datetime.now() - self.start_time
            minutes = duration.seconds // 60
            seconds = duration.seconds % 60
            self.result_label.config(
                text=f"平均分贝: {avg_db:.1f} dB    持续时间: {minutes}分{seconds}秒"
            )
            self.is_monitoring = False
            self.start_btn.config(text="开始计时")
    
    def run(self):
        self.root.mainloop()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

if __name__ == "__main__":
    app = NoiseMonitor()
    app.run()