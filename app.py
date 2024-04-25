from flask import Flask, render_template, jsonify
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

@app.route('/')
def index():
    return render_template('index.html', guitar_strings=guitar_strings)

@app.route('/estimate_pitch')
def estimate_pitch():
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=BUFFER_SIZE)

    data = stream.read(BUFFER_SIZE)
    audio = np.frombuffer(data, dtype=np.float32)

    rms = np.sqrt(np.mean(np.square(audio)))
    decibels = 20 * np.log10(rms)

    if decibels > -60:
        time, frequency, confidence, activation = crepe.predict(audio, SAMPLE_RATE, viterbi=True)
        estimated_pitch = frequency[-1]
    else:
        estimated_pitch = 0

    stream.stop_stream()
    stream.close()
    p.terminate()

    return jsonify({'estimated_pitch': estimated_pitch, 'decibels': decibels})

if __name__ == '__main__':
    app.run(debug=True)