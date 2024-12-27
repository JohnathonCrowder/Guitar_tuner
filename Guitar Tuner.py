import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QPoint
from PyQt5.QtGui import *
import pyaudio
import numpy as np
import crepe
import wave
import os

# Audio settings
SAMPLE_RATE = 16000
BUFFER_SIZE = 1024

class GuitarString:
    """
    Represents a guitar string with a name and frequency.

    Attributes:
        name (str): The name of the guitar string (e.g., 'E', 'A', 'D', 'G', 'B', 'E').
        frequency (float): The frequency of the guitar string in Hz.
    """

    def __init__(self, name, frequency):
        self.name = name
        self.frequency = frequency


class PitchEstimationThread(QThread):
    """
    A thread class for continuous pitch estimation using the CREPE library.
    """

    pitch_estimated = pyqtSignal(float)  # Signal emitted when a pitch is estimated
    decibel_calculated = pyqtSignal(float)  # Signal emitted when the decibel rating is calculated

    def __init__(self):
        super().__init__()
        self.is_running = False  # Flag to control the thread execution

    def run(self):
        """
        The main method of the thread, which runs the pitch estimation loop.
        """
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=BUFFER_SIZE)

        while self.is_running:
            # Read audio data from the stream
            data = stream.read(BUFFER_SIZE)
            audio = np.frombuffer(data, dtype=np.float32)

            # Calculate the RMS (root mean square) of the audio samples
            rms = np.sqrt(np.mean(np.square(audio)))

            # Convert RMS to decibels
            decibels = 20 * np.log10(rms)

            # Check if the decibel rating is above the threshold (-60 dB)
            if decibels > -60:
                # Estimate the pitch using the CREPE library
                time, frequency, confidence, activation = crepe.predict(audio, SAMPLE_RATE, viterbi=True)
                self.pitch_estimated.emit(frequency[-1])  # Emit the estimated pitch
                self.decibel_calculated.emit(decibels)  # Emit the decibel rating
            else:
                self.pitch_estimated.emit(0)  # Emit 0 as pitch if the decibel rating is below the threshold
                self.decibel_calculated.emit(decibels)  # Emit the decibel rating

        # Clean up the audio stream
        stream.stop_stream()
        stream.close()
        p.terminate()


class PitchSlider(QWidget):
    def __init__(self, target_pitch):
        super().__init__()
        self.target_pitch = target_pitch
        self.estimated_pitch = 0
        self.is_estimating = False
        self.setFixedSize(800, 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Create a rounded rectangle path for the slider
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 25, 25)

        # Draw background
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(200, 200, 200))
        painter.drawPath(path)

        # Draw target pitch line
        painter.setPen(QColor(0, 0, 0))
        target_x = self.width() // 2
        painter.drawLine(target_x, 0, target_x, self.height())

        # Fill the section between estimated pitch and target pitch with orange color
        # only if pitch estimation is running
        if self.is_estimating:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 165, 0))  # Orange color
            estimated_x = int((self.estimated_pitch - self.target_pitch + 500) / 1000 * self.width())
            if estimated_x < target_x:
                path = QPainterPath()
                path.addRoundedRect(estimated_x, 0, target_x - estimated_x, self.height(), 25, 25)
                painter.drawPath(path)
            else:
                path = QPainterPath()
                path.addRoundedRect(target_x, 0, estimated_x - target_x, self.height(), 25, 25)
                painter.drawPath(path)

    def update_estimated_pitch(self, pitch):
        self.estimated_pitch = pitch
        self.update()

    def set_estimating_state(self, is_estimating):
        self.is_estimating = is_estimating
        self.update()


class PitchEstimationGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set up the main layout
        layout = QVBoxLayout()

        # Create a horizontal layout for the target pitch and estimated pitch labels
        pitch_labels_layout = QHBoxLayout()

        # Create and configure the target pitch label
        self.target_pitch_label = QLabel('Target Pitch: -')
        self.target_pitch_label.setStyleSheet("font-size: 24px;")
        self.target_pitch_label.setFixedWidth(300)  # Set a fixed width for the label
        self.target_pitch_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Align text to the right and center vertically
        pitch_labels_layout.addWidget(self.target_pitch_label)

        # Add a horizontal spacer to create a gap between the labels
        spacer = QSpacerItem(40, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
        pitch_labels_layout.addItem(spacer)

        # Create and configure the estimated pitch label
        self.estimated_pitch_label = QLabel('Estimated Pitch: -')
        self.estimated_pitch_label.setStyleSheet("font-size: 24px;")
        self.estimated_pitch_label.setFixedWidth(300)  # Set a fixed width for the label
        self.estimated_pitch_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Align text to the left and center vertically
        pitch_labels_layout.addWidget(self.estimated_pitch_label)

        # Create a widget to hold the pitch labels layout
        pitch_labels_widget = QWidget()
        pitch_labels_widget.setLayout(pitch_labels_layout)

        # Add the pitch labels widget to the main layout with center alignment
        layout.addWidget(pitch_labels_widget, alignment=Qt.AlignCenter)

        # Create and add the pitch slider widget
        self.pitch_slider = PitchSlider(0)
        layout.addWidget(self.pitch_slider, alignment=Qt.AlignCenter)

        # Create and configure the pitch indicator widget
        self.pitch_indicator = QWidget(self.pitch_slider)
        self.pitch_indicator.setFixedSize(100, 100)
        self.pitch_indicator.setAutoFillBackground(True)
        self.set_pitch_indicator_color(QColor(255, 0, 0))  # Set initial color to red

        # Create and configure the string label as an overlay
        self.string_label = QLabel(self.pitch_indicator)
        self.string_label.setAlignment(Qt.AlignCenter)
        self.string_label.setStyleSheet("font-size: 36px; color: white;")
        self.string_label.setGeometry(0, 0, 100, 100)

        # Center the pitch indicator on the slider initially
        self.center_pitch_indicator()

        # Create a horizontal layout for the decibel rating label
        decibel_layout = QHBoxLayout()

        # Create and configure the decibel rating label
        self.decibel_label = QLabel('Decibel Rating: -')
        self.decibel_label.setStyleSheet("font-size: 24px;")
        decibel_layout.addWidget(self.decibel_label, alignment=Qt.AlignCenter)

        # Add the decibel layout to the main layout
        layout.addLayout(decibel_layout)

        # Create a horizontal layout for the instrument dropdown and record button
        instrument_record_layout = QHBoxLayout()

        # Create and configure the instrument dropdown menu
        self.instrument_dropdown = QComboBox()
        self.instrument_dropdown.addItems(['Guitar', 'Banjo', 'Ukulele', 'Violin'])
        self.instrument_dropdown.currentIndexChanged.connect(self.update_instrument)
        instrument_record_layout.addWidget(self.instrument_dropdown)

        # Create and configure the record button
        self.record_button = QPushButton('Record')
        self.record_button.setStyleSheet("font-size: 18px; padding: 5px;")
        self.record_button.setCheckable(True)
        self.record_button.toggled.connect(self.toggle_recording)
        instrument_record_layout.addWidget(self.record_button)

        # Add the instrument and record layout to the main layout
        layout.addLayout(instrument_record_layout)

        # Create and configure the string dropdown menu
        self.string_dropdown = QComboBox()
        self.string_dropdown.addItems([f"{guitar_string.name} - {guitar_string.frequency:.2f} Hz" for guitar_string in reversed(guitar_strings)])
        self.string_dropdown.currentIndexChanged.connect(self.update_target_pitch)
        layout.addWidget(self.string_dropdown)

        # Create and configure the start button
        self.start_button = QPushButton('Start')
        self.start_button.setStyleSheet("font-size: 24px; padding: 10px;")
        self.start_button.clicked.connect(self.start_estimation)
        layout.addWidget(self.start_button)

        # Create and configure the stop button
        self.stop_button = QPushButton('Stop')
        self.stop_button.setStyleSheet("font-size: 24px; padding: 10px;")
        self.stop_button.clicked.connect(self.stop_estimation)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        # Create a horizontal layout for the automatic mode and custom pitch widgets
        auto_custom_layout = QHBoxLayout()

        # Create and configure the automatic mode checkbox
        self.auto_mode_checkbox = QCheckBox('Automatic Mode')
        self.auto_mode_checkbox.setStyleSheet("font-size: 18px;")
        self.auto_mode_checkbox.stateChanged.connect(self.toggle_auto_mode)
        auto_custom_layout.addWidget(self.auto_mode_checkbox)

        # Create and configure the custom pitch checkbox
        self.custom_pitch_checkbox = QCheckBox('Custom Pitch')
        self.custom_pitch_checkbox.setStyleSheet("font-size: 18px;")
        self.custom_pitch_checkbox.stateChanged.connect(self.toggle_custom_pitch)
        auto_custom_layout.addWidget(self.custom_pitch_checkbox)

        # Create and configure the custom pitch entry box
        self.custom_pitch_entry = QLineEdit()
        self.custom_pitch_entry.setStyleSheet("font-size: 18px;")
        self.custom_pitch_entry.setValidator(QDoubleValidator())  # Allow only float values
        self.custom_pitch_entry.setVisible(False)  # Initially hide the entry box
        auto_custom_layout.addWidget(self.custom_pitch_entry)

        # Create and configure the custom pitch button
        self.custom_pitch_button = QPushButton('Set Custom Pitch')
        self.custom_pitch_button.setStyleSheet("font-size: 18px;")
        self.custom_pitch_button.clicked.connect(self.set_custom_pitch)
        self.custom_pitch_button.setVisible(False)  # Initially hide the button
        auto_custom_layout.addWidget(self.custom_pitch_button)

        # Add a horizontal spacer after the custom pitch button
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        auto_custom_layout.addItem(spacer)

        # Add the automatic mode and custom pitch layout to the main layout
        layout.addLayout(auto_custom_layout)

        # Set the main layout for the GUI
        self.setLayout(layout)

        # Set the window title and geometry
        self.setWindowTitle('Guitar Tuner')
        self.setGeometry(100, 100, 1200, 200)

        # Create and configure the pitch estimation thread
        self.estimation_thread = PitchEstimationThread()
        self.estimation_thread.pitch_estimated.connect(self.update_pitch)
        self.estimation_thread.decibel_calculated.connect(self.update_decibel_rating)

        # Initialize recording variables
        self.recording = False
        self.audio_frames = []

    def set_pitch_indicator_color(self, color):
        """Set the color of the pitch indicator widget"""
        palette = self.pitch_indicator.palette()
        palette.setColor(QPalette.Window, color)
        self.pitch_indicator.setPalette(palette)

    def center_pitch_indicator(self):
        """Center the pitch indicator on the slider"""
        slider_width = self.pitch_slider.width()
        indicator_width = self.pitch_indicator.width()
        x = (slider_width - indicator_width) // 2
        y = (self.pitch_slider.height() - self.pitch_indicator.height()) // 2
        self.pitch_indicator.move(x, y)

    def update_instrument(self, index):
        """Update the instrument based on the selected instrument from the dropdown menu"""
        instrument = self.instrument_dropdown.currentText()
        self.load_instrument_strings(instrument)

    def load_instrument_strings(self, instrument):
        """Load the strings for the selected instrument"""
        if instrument == 'Guitar':
            self.instrument_strings = guitar_strings
        elif instrument == 'Banjo':
            self.instrument_strings = banjo_strings
        elif instrument == 'Ukulele':
            self.instrument_strings = ukulele_strings
        elif instrument == 'Violin':
            self.instrument_strings = violin_strings

        self.string_dropdown.clear()
        self.string_dropdown.addItems([f"{string.name} - {string.frequency:.2f} Hz" for string in reversed(self.instrument_strings)])
        self.update_target_pitch(0)

    def update_target_pitch(self, index):
        """Update the target pitch based on the selected string from the dropdown menu"""
        self.target_pitch = self.instrument_strings[len(self.instrument_strings) - index - 1].frequency
        self.target_pitch_label.setText(f'Target Pitch: {self.target_pitch:.2f} Hz')
        self.pitch_slider.target_pitch = self.target_pitch
        self.pitch_slider.update()

        # Update the string label with the selected string name
        selected_string = self.instrument_strings[len(self.instrument_strings) - index - 1].name
        self.string_label.setText(selected_string)

    def toggle_custom_pitch(self, state):
        """Toggle the visibility of the custom pitch widgets"""
        if state == Qt.Checked:
            self.custom_pitch_entry.setVisible(True)
            self.custom_pitch_button.setVisible(True)
        else:
            self.custom_pitch_entry.setVisible(False)
            self.custom_pitch_button.setVisible(False)

    def set_custom_pitch(self):
        """Set the target pitch to the custom value entered in the entry box"""
        custom_pitch = self.custom_pitch_entry.text()
        if custom_pitch:
            try:
                self.target_pitch = float(custom_pitch)
                self.target_pitch_label.setText(f'Target Pitch: {self.target_pitch:.2f} Hz')
                self.pitch_slider.target_pitch = self.target_pitch
                self.pitch_slider.update()

                # Clear the string label text when a custom pitch is set
                self.string_label.setText('')

            except ValueError:
                QMessageBox.warning(self, 'Invalid Input', 'Please enter a valid number for the custom pitch.')

    def start_estimation(self):
        """Start the pitch estimation thread"""
        if not hasattr(self, 'target_pitch') or self.target_pitch is None:
            index = self.string_dropdown.currentIndex()
            self.update_target_pitch(index)

        self.estimation_thread.is_running = True
        self.estimation_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_estimation(self):
        """Stop the pitch estimation thread"""
        self.estimation_thread.is_running = False
        self.estimation_thread.wait()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def toggle_auto_mode(self, state):
        """Toggle automatic mode based on the checkbox state"""
        if state == Qt.Checked:
            self.string_dropdown.setVisible(False)  # Hide the string dropdown when auto mode is enabled
            self.custom_pitch_checkbox.setEnabled(False)  # Disable the custom pitch checkbox
            self.custom_pitch_entry.setVisible(False)  # Hide the custom pitch entry box
            self.custom_pitch_button.setVisible(False)  # Hide the custom pitch button
        else:
            self.string_dropdown.setVisible(True)  # Show the string dropdown when auto mode is disabled
            self.custom_pitch_checkbox.setEnabled(True)  # Enable the custom pitch checkbox
            if self.custom_pitch_checkbox.isChecked():
                self.custom_pitch_entry.setVisible(True)  # Show the custom pitch entry box if custom pitch is checked
                self.custom_pitch_button.setVisible(True)  # Show the custom pitch button if custom pitch is checked

    def find_closest_string(self, estimated_pitch):
        """Find the string with the closest frequency to the estimated pitch"""
        closest_string = None
        min_difference = float('inf')

        for string in self.instrument_strings:
            difference = abs(estimated_pitch - string.frequency)
            if difference < min_difference:
                min_difference = difference
                closest_string = string

        return closest_string

    def update_pitch(self, estimated_pitch):
        """Update the pitch labels and indicators based on the estimated pitch"""
        if estimated_pitch == 0:
            self.estimated_pitch_label.setText('Estimated Pitch: -')
            self.set_pitch_indicator_color(QColor(200, 200, 200))  # Set color to gray when no sound is detected
            self.pitch_slider.update_estimated_pitch(0)
            self.pitch_slider.set_estimating_state(False)  # Set the estimating state to False
        else:
            self.estimated_pitch_label.setText(f'Estimated Pitch: {estimated_pitch:.2f} Hz')
            pitch_difference = estimated_pitch - self.target_pitch

            if abs(pitch_difference) <= 10:
                self.set_pitch_indicator_color(QColor(0, 255, 0))  # Green color
            else:
                self.set_pitch_indicator_color(QColor(255, 0, 0))  # Red color

            self.pitch_slider.update_estimated_pitch(estimated_pitch)
            self.pitch_slider.set_estimating_state(True)  # Set the estimating state to True

            # Automatically choose the closest string if auto mode is enabled
            if self.auto_mode_checkbox.isChecked():
                closest_string = self.find_closest_string(estimated_pitch)
                if closest_string:
                    index = self.instrument_strings.index(closest_string)
                    self.string_dropdown.setCurrentIndex(len(self.instrument_strings) - index - 1)
                    self.update_target_pitch(len(self.instrument_strings) - index - 1)

    def update_decibel_rating(self, decibels):
        """Update the decibel rating label"""
        self.decibel_label.setText(f'Decibel Rating: {decibels:.2f} dB')

        # Set the estimating state based on the decibel rating
        if decibels > -60:
            self.pitch_slider.set_estimating_state(True)
        else:
            self.pitch_slider.set_estimating_state(False)

    def toggle_recording(self, checked):
        """Toggle audio recording"""
        self.recording = checked
        if self.recording:
            self.audio_frames = []  # Clear previous recording
            self.record_button.setText('Stop Recording')
        else:
            self.record_button.setText('Record')
            self.save_recording()

    def save_recording(self):
        """Save the recorded audio to a WAV file"""
        if len(self.audio_frames) > 0:
            wav_file = QFileDialog.getSaveFileName(self, 'Save Recording', '', 'WAV Files (*.wav)')[0]
            if wav_file:
                wf = wave.open(wav_file, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b''.join(self.audio_frames))
                wf.close()

    def closeEvent(self, event):
        """Handle the window close event"""
        self.stop_estimation()
        event.accept()


if __name__ == '__main__':
    guitar_strings = [
        GuitarString('E', 82.41),
        GuitarString('A', 110.00),
        GuitarString('D', 146.83),
        GuitarString('G', 196.00),
        GuitarString('B', 246.94),
        GuitarString('E', 329.63)
    ]

    banjo_strings = [
        GuitarString('D', 294),
        GuitarString('B', 248),
        GuitarString('G', 196),
        GuitarString('D', 147),
        GuitarString('G', 98)
    ]

    ukulele_strings = [
        GuitarString('A', 440),
        GuitarString('E', 329.63),
        GuitarString('C', 261.63),
        GuitarString('G', 392)
    ]

    violin_strings = [
        GuitarString('G', 196),
        GuitarString('D', 293.66),
        GuitarString('A', 440),
        GuitarString('E', 659.25)
    ]

    app = QApplication(sys.argv)
    gui = PitchEstimationGUI()
    gui.load_instrument_strings('Guitar')  # Set the default instrument to Guitar
    gui.show()
    sys.exit(app.exec_())