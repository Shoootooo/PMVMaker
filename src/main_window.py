import sys
import os
import json
import glob
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QProgressBar, QLineEdit,
    QMessageBox, QTextEdit, QComboBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

# Import the backend modules
import scene_detector
import music_analyzer
from clip_classifier import ClipClassifier
import director
import renderer

# --- Worker Thread for AI Pipeline ---
class GenerationWorker(QThread):
    progress_text = pyqtSignal(str)
    progress_value = pyqtSignal(int)
    finished = pyqtSignal(str)

    def __init__(self, video_folder, music_file, output_file, prompts, progression, beat_tightness):
        super().__init__()
        self.video_folder = video_folder
        self.music_file = music_file
        self.output_file = output_file
        self.prompts = prompts
        self.progression = progression
        self.beat_tightness = beat_tightness
        self.is_running = True

    def run(self):
        try:
            # --- 1. Scene Detection ---
            self.progress_text.emit("Scanning for source videos...")
            self.progress_value.emit(5)

            extensions = ['*.mp4', '*.mov', '*.avi', '*.mkv', '*.webm']
            source_videos = []
            for ext in extensions:
                # Use recursive glob to find videos in subdirectories
                search_path = os.path.join(self.video_folder, '**', ext)
                source_videos.extend(glob.glob(search_path, recursive=True))

            if not source_videos:
                self.finished.emit("Error: No compatible video files (.mp4, .mov, .avi, .mkv, .webm) found in the source folder or its subdirectories.")
                return

            all_scene_clips = []
            scenes_dir = os.path.join('temp', 'detected_scenes')
            for video_path in source_videos:
                self.progress_text.emit(f"Detecting scenes in {os.path.basename(video_path)}...")
                clips = scene_detector.detect_and_split_scenes(video_path, scenes_dir)
                all_scene_clips.extend(clips)

            if not all_scene_clips:
                self.finished.emit("Error: Scene detection failed to produce any clips.")
                return

            # --- 2. Music Analysis ---
            self.progress_text.emit("Analyzing music track...")
            self.progress_value.emit(20)
            beat_times = music_analyzer.get_beat_timestamps(self.music_file, tightness=self.beat_tightness)
            music_duration = music_analyzer.get_audio_duration(self.music_file)
            if not beat_times.any() or music_duration <= 0:
                self.finished.emit("Error: Could not analyze music file.")
                return

            # --- 3. AI Classification ---
            self.progress_text.emit("Initializing AI Classifier (may download model)...")
            self.progress_value.emit(30)
            classifier = ClipClassifier()
            if not classifier.model:
                self.finished.emit("Error: Failed to load CLIP model.")
                return

            self.progress_text.emit("Classifying scenes with AI...")
            self.progress_value.emit(40)
            categorized_clips = classifier.classify_clips(all_scene_clips, self.prompts)

            # --- 4. Timeline Creation ---
            self.progress_text.emit("Creating video timeline...")
            self.progress_value.emit(60)
            edit_list = director.create_edit_list(categorized_clips, beat_times, music_duration, self.progression)
            if not edit_list:
                self.finished.emit("Error: Director failed to create an edit list. Not enough clips for all categories?")
                return

            # --- 5. Rendering ---
            self.progress_text.emit("Rendering final PMV...")
            self.progress_value.emit(70)
            def renderer_progress(p):
                # Scale renderer progress (0-1) to our progress bar range (70-100)
                if p >= 0:
                    self.progress_value.emit(int(70 + p * 30))

            renderer.render_pmv(edit_list, self.music_file, self.output_file, music_duration, on_progress=renderer_progress)

            self.progress_value.emit(100)
            self.finished.emit(f"Success! PMV saved to: {self.output_file}")

        except Exception as e:
            self.finished.emit(f"An unexpected error occurred in the pipeline: {e}")

    def stop(self):
        self.is_running = False
        self.quit()
        self.wait()

# --- Main Application Window ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI PMV Generator v2.1")
        self.setGeometry(100, 100, 700, 700)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # --- Path Selectors ---
        self.video_folder_path = self._create_path_selector("1. Select Source Video Folder", self.select_video_folder)
        self.music_file_path = self._create_path_selector("2. Select Music Track", self.select_music_file)
        self.output_file_path = self._create_path_selector("3. Select Output Video File", self.set_output_file)

        # --- AI Prompts Area ---
        self.layout.addWidget(QLabel("4. Define AI Categories and Prompts (JSON format):"))
        self.prompts_input = QTextEdit()
        default_prompts = {
            "kissing": "a photo of two people kissing",
            "oral": "a photo of oral sex",
            "penetration": "a photo of sexual penetration",
            "cumshots": "a close-up photo of a cumshot"
        }
        self.prompts_input.setText(json.dumps(default_prompts, indent=2))
        self.prompts_input.setFixedHeight(150)
        self.layout.addWidget(self.prompts_input)

        # --- Options ---
        options_layout = QHBoxLayout()
        # Progression Logic
        prog_layout = QVBoxLayout()
        prog_layout.addWidget(QLabel("5. Clip Progression:"))
        self.progression_input = QLineEdit("kissing,oral,penetration,cumshots")
        prog_layout.addWidget(self.progression_input)
        options_layout.addLayout(prog_layout)

        # Beat Detection Pace
        pace_layout = QVBoxLayout()
        pace_layout.addWidget(QLabel("6. Editing Pace:"))
        self.pace_dropdown = QComboBox()
        self.pace_dropdown.addItems(["Relaxed", "Normal", "Intense"])
        self.pace_dropdown.setCurrentText("Normal")
        pace_layout.addWidget(self.pace_dropdown)
        options_layout.addLayout(pace_layout)

        self.layout.addLayout(options_layout)

        self.layout.addStretch()

        # --- Controls ---
        self.generate_button = QPushButton("Generate PMV")
        self.generate_button.setFixedHeight(40)
        self.status_label = QLabel("Ready.")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.layout.addWidget(self.generate_button)
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)

        # --- Connections ---
        self.generate_button.clicked.connect(self.start_generation)
        self.worker = None

    def _create_path_selector(self, label_text, button_callback):
        self.layout.addWidget(QLabel(label_text))
        layout = QHBoxLayout()
        line_edit = QLineEdit("Not selected")
        line_edit.setReadOnly(True)
        button = QPushButton("Browse...")
        button.clicked.connect(button_callback)
        layout.addWidget(line_edit)
        layout.addWidget(button)
        self.layout.addLayout(layout)
        return line_edit

    def select_video_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Raw Videos")
        if folder:
            self.video_folder_path.setText(folder)

    def select_music_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Music", "", "Audio Files (*.wav *.mp3)")
        if file:
            self.music_file_path.setText(file)

    def set_output_file(self):
        file, _ = QFileDialog.getSaveFileName(self, "Set Output Video", "", "Video Files (*.mp4)")
        if file:
            self.output_file_path.setText(file)

    def start_generation(self):
        # --- Input Validation ---
        if "Not selected" in self.video_folder_path.text() or \
           "Not selected" in self.music_file_path.text() or \
           "Not selected" in self.output_file_path.text():
            QMessageBox.warning(self, "Missing Info", "Please select all required paths.")
            return

        try:
            prompts = json.loads(self.prompts_input.toPlainText())
            if not isinstance(prompts, dict) or not all(isinstance(v, str) for v in prompts.values()):
                raise ValueError("Prompts must be a dictionary of strings.")
        except (json.JSONDecodeError, ValueError) as e:
            QMessageBox.critical(self, "Invalid Prompts", f"The AI prompts are not valid JSON. Error: {e}")
            return

        progression = [p.strip() for p in self.progression_input.text().split(',') if p.strip()]
        if not progression or not all(p in prompts for p in progression):
            QMessageBox.warning(self, "Invalid Progression", "The progression must contain valid category names from the prompts JSON.")
            return

        # --- Get Beat Tightness ---
        pace_map = {
            "Relaxed": 200,
            "Normal": 100,
            "Intense": 50
        }
        beat_tightness = pace_map.get(self.pace_dropdown.currentText(), 100)

        # --- Start Worker ---
        self.generate_button.setEnabled(False)
        self.progress_bar.setVisible(True)

        self.worker = GenerationWorker(
            self.video_folder_path.text(),
            self.music_file_path.text(),
            self.output_file_path.text(),
            prompts,
            progression,
            beat_tightness
        )
        self.worker.progress_text.connect(self.status_label.setText)
        self.worker.progress_value.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_generation_finished)
        self.worker.start()

    def on_generation_finished(self, message):
        self.generate_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready.")

        if message.startswith("Success"):
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())