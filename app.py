from flask import Flask, render_template, jsonify, request
import pyaudio
import numpy as np
import crepe
import threading

app = Flask(__name__)

# Audio settings
SAMPLE_RATE = 16000
BUFFER_SIZE = 1024

# Global variables for storing estimated pitch and decibels
estimated_pitch_value = 0
decibels_value = 0

class GuitarString:
    def __init__(self, name, frequency):
        self.name = name
        self.frequency = frequency

# List of guitar strings with their names and frequencies
guitar_strings = [
    GuitarString('E', 82.41),
    GuitarString('A', 110.00),
    GuitarString('D', 146.83),
    GuitarString('G', 196.00),
    GuitarString('B', 246.94),
    GuitarString('E', 329.63)
]

# Add the Banjo strings
banjo_strings = [
    GuitarString('D', 294),
    GuitarString('B', 248),
    GuitarString('G', 196),
    GuitarString('D#', 147),
    GuitarString('G#', 393)
]

# Create a PyAudio object
p = pyaudio.PyAudio()
stream = None

@app.route('/')
def index():
    instrument = request.args.get('instrument', 'guitar')
    strings = guitar_strings if instrument == 'guitar' else banjo_strings
    return render_template('index.html', instrument=instrument, strings=strings)

def pitch_estimation_thread():
    global stream, estimated_pitch_value, decibels_value
    while True:
        if stream is not None:
            # Read audio data from the stream
            data = stream.read(BUFFER_SIZE)
            audio = np.frombuffer(data, dtype=np.float32)

            # Calculate the RMS (Root Mean Square) of the audio data
            rms = np.sqrt(np.mean(np.square(audio)))
            # Convert RMS to decibels
            decibels = 20 * np.log10(rms)

            if decibels > -60:
                # Estimate the pitch using CREPE
                time, frequency, confidence, activation = crepe.predict(audio, SAMPLE_RATE, viterbi=True)
                estimated_pitch = frequency[-1]
            else:
                estimated_pitch = 0

            # Store the estimated pitch and decibels in global variables
            estimated_pitch_value = estimated_pitch
            decibels_value = decibels

@app.route('/start_estimation')
def start_estimation():
    global stream
    if stream is None:
        # Open the audio stream if it's not already running
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=BUFFER_SIZE)
        # Start the pitch estimation thread
        thread = threading.Thread(target=pitch_estimation_thread)
        thread.daemon = True
        thread.start()
    return jsonify({'message': 'Pitch estimation started'})

@app.route('/estimate_pitch')
def estimate_pitch():
    global estimated_pitch_value, decibels_value
    # Return the current estimated pitch and decibels as JSON
    return jsonify({'estimated_pitch': estimated_pitch_value, 'decibels': decibels_value})

@app.route('/stop_estimation')
def stop_estimation():
    global stream
    if stream is not None:
        # Stop and close the audio stream
        stream.stop_stream()
        stream.close()
        stream = None
    return jsonify({'message': 'Pitch estimation stopped'})

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

if __name__ == '__main__':
    # Run the Flask application
    app.run(debug=True)