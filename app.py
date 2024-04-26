from flask import Flask, render_template, jsonify, request
import pyaudio
import numpy as np
import crepe

app = Flask(__name__)

# Audio settings
SAMPLE_RATE = 16000
BUFFER_SIZE = 1024

class GuitarString:
    def __init__(self, name, frequency):
        self.name = name
        self.frequency = frequency

guitar_strings = [
    GuitarString('E', 82.41),
    GuitarString('A', 110.00),
    GuitarString('D', 146.83),
    GuitarString('G', 196.00),
    GuitarString('B', 246.94),
    GuitarString('E', 329.63)
]

p = pyaudio.PyAudio()
stream = None

@app.route('/')
def index():
    return render_template('index.html', guitar_strings=guitar_strings)

@app.route('/start_estimation')
def start_estimation():
    global stream
    if stream is None:
        stream = p.open(format=pyaudio.paFloat32,
                        channels=1,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=BUFFER_SIZE)
    return jsonify({'message': 'Pitch estimation started'})

@app.route('/estimate_pitch')
def estimate_pitch():
    global stream
    if stream is not None:
        data = stream.read(BUFFER_SIZE)
        audio = np.frombuffer(data, dtype=np.float32)

        rms = np.sqrt(np.mean(np.square(audio)))
        decibels = 20 * np.log10(rms)

        if decibels > -60:
            time, frequency, confidence, activation = crepe.predict(audio, SAMPLE_RATE, viterbi=True)
            estimated_pitch = frequency[-1]
        else:
            estimated_pitch = 0

        return jsonify({'estimated_pitch': estimated_pitch, 'decibels': decibels})
    else:
        return jsonify({'error': 'Pitch estimation not started'})

@app.route('/stop_estimation')
def stop_estimation():
    global stream
    if stream is not None:
        stream.stop_stream()
        stream.close()
        stream = None
    return jsonify({'message': 'Pitch estimation stopped'})

if __name__ == '__main__':
    app.run(debug=True)