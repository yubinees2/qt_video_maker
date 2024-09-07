import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QSlider, QVBoxLayout,
    QFileDialog, QTimeEdit, QCheckBox, QMessageBox, QProgressDialog
)
from PyQt5.QtCore import Qt, QTime, QProcess, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl
from pathlib import Path
import subprocess
import re

plugin_path = Path("venv/lib/python3.9/site-packages/PyQt5/Qt5/plugins")
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(plugin_path.absolute())

class VideoCreator(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.ffmpeg_process = None  # FFmpeg 작업을 관리할 QProcess 객체
        self.media_time = 0
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_media_time)
        self.update_timer.start(100)

    def init_ui(self):
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

        # 음악 재생 상태 확인 아이콘
        self.playback_status_label = QLabel('Playback:')
        self.playback_status_icon = QLabel()
        self.update_playback_icon(False)  # 초기에는 일시정지 상태
        # 현재 미디어 시간
        self.media_time_label = QLabel('Media Time: 00:00:00')
        layout.addWidget(self.playback_status_label)
        layout.addWidget(self.playback_status_icon)
        layout.addWidget(self.media_time_label)

        # 슬라이더와 시간 입력
        self.slider_label = QLabel('Audio Trim:')
        self.start_time_label = QLabel('Start Time:')
        self.end_time_label = QLabel('End Time:')
        self.start_time_text = QLabel('00:00:00')
        self.end_time_text = QLabel('00:00:00')
        self.slider_start = QSlider(Qt.Horizontal)
        self.slider_end = QSlider(Qt.Horizontal)
        self.slider_start.setEnabled(False)
        self.slider_end.setEnabled(False)
        self.slider_start.valueChanged.connect(self.update_start_time)
        self.slider_end.valueChanged.connect(self.update_end_time)
        layout.addWidget(self.slider_label)
        layout.addWidget(self.start_time_label)
        layout.addWidget(self.start_time_text)
        layout.addWidget(self.slider_start)
        layout.addWidget(self.end_time_label)
        layout.addWidget(self.end_time_text)
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
        self.media_player.positionChanged.connect(self.update_on_playback)

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
            self.start_time_text.setText("00:00:00")
            self.end_time_text.setText("00:00:00")

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
        self.start_time_text.setText(QTime(0, 0, 0).addSecs(time_in_seconds).toString("hh:mm:ss"))
        self.update_playback_on_slider()

    def update_end_time(self):
        time_in_seconds = self.slider_end.value()
        if time_in_seconds <= self.slider_start.value():  # Start time보다 작을 수 없음
            self.slider_end.setValue(self.slider_start.value() + 1)
            return
        self.end_time_text.setText(QTime(0, 0, 0).addSecs(time_in_seconds).toString("hh:mm:ss"))
        self.update_playback_on_slider()

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
            QMessageBox.warning(self, "Warning", "All fields must be filled!")
            return

        start_time = self.slider_start.value()
        end_time = self.slider_end.value()

        # FFmpeg 명령어 생성
        command = [
            'ffmpeg',
            '-loop', '1',
            '-i', image_file,
            '-ss', QTime(0, 0, 0).addSecs(start_time).toString("hh:mm:ss"),
            '-to', QTime(0, 0, 0).addSecs(end_time).toString("hh:mm:ss"),
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

        # Progress Dialog 설정
        self.progress_dialog = QProgressDialog("Processing video...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowTitle("Progress")
        self.progress_dialog.canceled.connect(self.cancel_ffmpeg_process)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.show()

        # QProcess를 이용하여 FFmpeg 비동기 실행
        self.ffmpeg_process = QProcess(self)
        self.ffmpeg_process.setProgram(command[0])
        self.ffmpeg_process.setArguments(command[1:])
        self.ffmpeg_process.readyReadStandardError.connect(self.update_progress)
        self.ffmpeg_process.finished.connect(self.process_finished)
        self.ffmpeg_process.start()

    def update_progress(self):
        # FFmpeg의 진행 상황을 읽어와서 %로 변환 후 ProgressDialog 업데이트
        # (예: "frame=  100 fps= 20 q=0.0 Lsize=  500kB time=00:00:05.00 bitrate= 800.0kbits/s speed=0.400x")
        # 사용자가 FFmpeg 진행 상황을 통해 실제 %를 계산하도록 추가 로직 필요
        # FFmpeg로부터 출력된 stderr 로그를 읽어들임
        output = self.ffmpeg_process.readAllStandardError().data().decode()

        # FFmpeg 진행 상황에서 "time=" 부분을 추출하여 현재까지 처리된 시간을 가져옴
        time_match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", output)
        if time_match:
            current_time_str = time_match.group(1)
            current_seconds = self.convert_time_to_seconds(current_time_str)

            # 전체 시간 대비 현재까지 진행된 시간을 백분율로 계산
            progress_percent = int((current_seconds / self.total_duration) * 100)
            self.progress_dialog.setValue(progress_percent)

    def convert_time_to_seconds(self, time_str):
        """
        HH:MM:SS.ss 형식의 시간을 초 단위로 변환하는 유틸리티 함수
        """
        time_parts = time_str.split(':')
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        seconds = float(time_parts[2])
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds

    def process_finished(self):
        self.progress_dialog.setValue(100)
        QMessageBox.information(self, "Completed", "Video processing completed successfully!")

    def cancel_ffmpeg_process(self):
        if self.ffmpeg_process:
            self.ffmpeg_process.kill()
        self.progress_dialog.cancel()
        QMessageBox.warning(self, "Cancelled", "Video processing was cancelled!")

    def update_media_time(self):
        # if self.media_player.state() == QMediaPlayer.PlayingState:
        self.media_time = self.media_player.position() / 1000  # 밀리초를 초로 변환
        self.media_time_label.setText(f'Media Time: {QTime(0, 0, 0).addSecs(int(self.media_time)).toString("hh:mm:ss")}')

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Left:
            if self.slider_start.hasFocus():
                new_start_time = self.slider_start.value() - 5
                self.slider_start.setValue(max(new_start_time, 0))
            elif self.slider_end.hasFocus():
                new_end_time = self.slider_end.value() - 5
                self.slider_end.setValue(max(new_end_time, self.slider_start.value() + 1))
            else:
                new_media_time = self.media_time - 5
                self.media_player.setPosition(max(new_media_time * 1000, self.slider_start.value()*1000))
        elif event.key() == Qt.Key_Right:
            if self.slider_start.hasFocus():
                new_start_time = self.slider_start.value() + 5
                self.slider_start.setValue(min(new_start_time, self.slider_end.value() - 1))
            elif self.slider_end.hasFocus():
                new_end_time = self.slider_end.value() + 5
                self.slider_end.setValue(min(new_end_time, self.get_audio_duration(self.audio_text.text())))
            else:
                new_media_time = self.media_time + 5
                self.media_player.setPosition(min([new_media_time * 1000,
                                                   self.get_audio_duration(self.audio_text.text()) * 1000,
                                                    self.slider_end.value()*1000]))
        elif event.key() == Qt.Key_Space:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.update_playback_icon(False)
            else:
                # start_time = self.slider_start.value() * 1000
                # self.media_player.setPosition(start_time)
                self.media_player.play()
                self.update_playback_icon(True)
                # self.update_timer.start(100)  # 매 초마다 시간 업데이트
        self.update_media_time()

    def update_playback_icon(self, is_playing):
        if is_playing:
            self.playback_status_icon.setText('⏸️')  # 재생 아이콘
        else:
            self.playback_status_icon.setText('▶️')  # 일시정지 아이콘

    def update_on_playback(self, position):
        self.update_media_time()
        current_time = position // 1000
        if current_time >= self.slider_end.value():
            self.media_player.pause()
            return
        # self.slider_start.setValue(current_time)
        # self.start_time_text.setText(QTime(0, 0, 0).addSecs(current_time).toString("hh:mm:ss"))
    def update_playback_on_slider(self):
        start_time = self.slider_start.value() * 1000
        end_time = self.slider_end.value() * 1000
        if start_time > self.media_player.position():
            self.media_player.setPosition(start_time)
        if end_time < self.media_player.position():
            self.media_player.setPosition(end_time)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoCreator()
    sys.exit(app.exec_())