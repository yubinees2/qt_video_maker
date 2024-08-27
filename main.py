import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider, QVBoxLayout,
    QFileDialog, QTimeEdit, QCheckBox
)
from PyQt5.QtCore import Qt, QTime
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from pathlib import Path
import subprocess

plugin_path = Path("venv/lib/python3.9/site-packages/PyQt5/Qt5/plugins")
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
        self.image_text = QLabel('No file selected')
        self.image_button = QPushButton('Select Image')
        self.image_button.clicked.connect(self.select_image)

        layout.addWidget(self.image_label)
        layout.addWidget(self.image_text)
        layout.addWidget(self.image_button)

        # 오디오 파일 선택
        self.audio_label = QLabel('Audio File:')
        self.audio_text = QLabel('No file selected')
        self.audio_button = QPushButton('Select Audio')
        self.audio_button.clicked.connect(self.select_audio)

        layout.addWidget(self.audio_label)
        layout.addWidget(self.audio_text)
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
        self.output_text = QLabel('No file selected')
        self.output_button = QPushButton('Select Output')
        self.output_button.clicked.connect(self.select_output)

        layout.addWidget(self.output_label)
        layout.addWidget(self.output_text)
        layout.addWidget(self.output_button)

        # 이미지 효과 옵션
        self.wobble_checkbox = QCheckBox("Enable Wobble Effect")
        self.dim_checkbox = QCheckBox("Enable Dim Effect")
        layout.addWidget(self.wobble_checkbox)
        layout.addWidget(self.dim_checkbox)

        # Submit 버튼
        self.submit_button = QPushButton('Submit')
        self.submit_button.clicked.connect(self.submit)
        layout.addWidget(self.submit_button)

        # 오디오 플레이어 설정
        self.media_player = QMediaPlayer()
        self.media_player.positionChanged.connect(self.update_slider_on_playback)

        self.setLayout(layout)
        self.setWindowTitle('Video Creator')
        self.show()

    def select_image(self):
        image_file, _ = QFileDialog.getOpenFileName(self, 'Select Image File', '', 'Images (*.png *.jpg *.jpeg)')
        if image_file:
            self.image_text.setText(image_file)

    def select_audio(self):
        audio_file, _ = QFileDialog.getOpenFileName(self, 'Select Audio File', '', 'Audio Files (*.mp3 *.wav *.m4a)')
        if audio_file:
            self.audio_text.setText(audio_file)
            self.slider_start.setEnabled(True)
            self.slider_end.setEnabled(True)
            self.start_time_input.setEnabled(True)
            self.end_time_input.setEnabled(True)

            # 오디오 파일 길이를 가져와 슬라이더 최대값 설정
            audio_duration = self.get_audio_duration(audio_file)
            self.slider_start.setMaximum(audio_duration)
            self.slider_end.setMaximum(audio_duration)
            self.slider_end.setValue(audio_duration)

            # 미디어 플레이어에 오디오 파일 설정
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(audio_file)))

    def select_output(self):
        output_file, _ = QFileDialog.getSaveFileName(self, 'Select Output File', '', 'Video Files (*.mp4)')
        if output_file:
            self.output_text.setText(output_file)

    def update_start_time(self):
        time_in_seconds = self.slider_start.value()
        if time_in_seconds >= self.slider_end.value():  # End time보다 클 수 없음
            self.slider_start.setValue(self.slider_end.value() - 1)
            return
        self.start_time_input.setTime(QTime(0, 0, 0).addSecs(time_in_seconds))

    def update_end_time(self):
        time_in_seconds = self.slider_end.value()
        if time_in_seconds <= self.slider_start.value():  # Start time보다 작을 수 없음
            self.slider_end.setValue(self.slider_start.value() + 1)
            return
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
        image_file = self.image_text.text()
        audio_file = self.audio_text.text()
        output_file = self.output_text.text()

        if not image_file or not audio_file or not output_file:
            print("All fields must be filled!")
            return

        start_time = self.start_time_input.time().toString("hh:mm:ss")
        end_time = self.end_time_input.time().toString("hh:mm:ss")

        # FFmpeg 명령어 생성
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
            '-shortest'
        ]

        # 이미지 효과 추가
        if self.wobble_checkbox.isChecked():
            command.extend(['-vf', 'scale=iw*1.05:ih*1.05,zoompan=z=\'min(zoom+0.0015,1.5)\':d=25'])
        if self.dim_checkbox.isChecked():
            command.extend(['-vf', 'eq=brightness=-0.1'])

        command.append(output_file)

        subprocess.run(command, check=True)
        print(f"Video created at {output_file}")

    def update_slider_on_playback(self, position):
        # 미디어 플레이어의 재생 위치에 맞춰 슬라이더 및 시간 업데이트
        current_time = position // 1000
        if current_time >= self.slider_end.value():
            self.media_player.pause()
            return
        self.slider_start.setValue(current_time)
        self.start_time_input.setTime(QTime(0, 0, 0).addSecs(current_time))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
            else:
                start_time = self.slider_start.value() * 1000
                self.media_player.setPosition(start_time)
                self.media_player.play()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoCreator()
    sys.exit(app.exec_())
