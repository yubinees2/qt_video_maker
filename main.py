import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QSlider, QVBoxLayout,
    QHBoxLayout, QFileDialog, QTimeEdit
)
from PyQt5.QtCore import Qt, QTime
from pathlib import Path
import subprocess

plugin_path = Path("venv/lib/python3.9/site-packages/PyQt5/Qt5/plugins/platforms")
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(plugin_path.absolute())
class VideoCreator(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        # 레이아웃 설정
        layout = QVBoxLayout()

        # 이미지 파일 선택
        self.image_label = QLabel('Image File:')
        self.image_input = QLineEdit()
        self.image_button = QPushButton('Select Image')
        self.image_button.clicked.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_input)
        layout.addWidget(self.image_button)

        # 오디오 파일 선택
        self.audio_label = QLabel('Audio File:')
        self.audio_input = QLineEdit()
        self.audio_button = QPushButton('Select Audio')
        self.audio_button.clicked.connect(self.select_audio)

        layout.addWidget(self.audio_label)
        layout.addWidget(self.audio_input)
        layout.addWidget(self.audio_button)

        # 슬라이더와 시간 입력
        self.slider_label = QLabel('Audio Trim:')
        self.start_time_label = QLabel('Start Time:')
        self.end_time_label = QLabel('End Time:')
        self.start_time_input = QTimeEdit()
        self.start_time_input.setDisplayFormat("hh:mm:ss")
        self.end_time_input = QTimeEdit()
        self.end_time_input.setDisplayFormat("hh:mm:ss")
        self.slider_start = QSlider(Qt.Horizontal)
        self.slider_end = QSlider(Qt.Horizontal)
        self.slider_start.setEnabled(False)
        self.slider_end.setEnabled(False)
        self.start_time_input.setEnabled(False)
        self.end_time_input.setEnabled(False)

        self.slider_start.valueChanged.connect(self.update_start_time)
        self.slider_end.valueChanged.connect(self.update_end_time)

        layout.addWidget(self.slider_label)
        layout.addWidget(self.start_time_label)
        layout.addWidget(self.start_time_input)
        layout.addWidget(self.slider_start)
        layout.addWidget(self.end_time_label)
        layout.addWidget(self.end_time_input)
        layout.addWidget(self.slider_end)

        # 출력 파일 선택
        self.output_label = QLabel('Output File:')
        self.output_input = QLineEdit()
        self.output_button = QPushButton('Select Output')
        self.output_button.clicked.connect(self.select_output)

        layout.addWidget(self.output_label)
        layout.addWidget(self.output_input)
        layout.addWidget(self.output_button)

        # Submit 버튼
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)
        self.setWindowTitle('Video Creator')
        self.show()

    def select_image(self):
        image_file, _ = QFileDialog.getOpenFileName(self, 'Select Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if image_file:
            self.image_input.setText(image_file)

    def select_audio(self):
        audio_file, _ = QFileDialog.getOpenFileName(self, 'Select Audio File', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if audio_file:
            self.audio_input.setText(audio_file)
            self.slider_start.setEnabled(True)
            self.slider_end.setEnabled(True)
            self.start_time_input.setEnabled(True)
            self.end_time_input.setEnabled(True)

            # 오디오 파일 길이를 가져와 슬라이더 최대값 설정
            audio_duration = self.get_audio_duration(audio_file)
            self.slider_start.setMaximum(audio_duration)
            self.slider_end.setMaximum(audio_duration)
            self.slider_end.setValue(audio_duration)

    def select_output(self):
        output_file, _ = QFileDialog.getSaveFileName(self, 'Select Output File', '', 'Video Files (*.mp4)')
        if output_file:
            self.output_input.setText(output_file)

    def update_start_time(self):
        time_in_seconds = self.slider_start.value()
        self.start_time_input.setTime(QTime(0, 0, 0).addSecs(time_in_seconds))

    def update_end_time(self):
        time_in_seconds = self.slider_end.value()
        self.end_time_input.setTime(QTime(0, 0, 0).addSecs(time_in_seconds))

    def get_audio_duration(self, audio_file):
        command = [
            'ffmpeg', '-i', audio_file,
            '-f', 'null', '-'
        ]
        result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        duration_line = [line for line in result.stderr.splitlines() if 'Duration' in line]
        if duration_line:
            duration = duration_line[0].split(',')[0].split('Duration:')[1].strip()
            h, m, s = duration.split(':')
            total_seconds = int(h) * 3600 + int(m) * 60 + float(s)
            return int(total_seconds)
        return 0

    def submit(self):
        image_file = self.image_input.text()
        audio_file = self.audio_input.text()
        output_file = self.output_input.text()

        if not image_file or not audio_file or not output_file:
            print("All fields must be filled!")
            return

        start_time = self.start_time_input.time().toString("hh:mm:ss")
        end_time = self.end_time_input.time().toString("hh:mm:ss")

        command = [
            'ffmpeg',
            '-loop', '1',
            '-i', image_file,
            '-ss', start_time,
            '-to', end_time,
            '-i', audio_file,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-b:a', '192k',
            '-shortest',
            output_file
        ]

        subprocess.run(command, check=True)
        print(f"Video created at {output_file}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoCreator()
    sys.exit(app.exec_())
