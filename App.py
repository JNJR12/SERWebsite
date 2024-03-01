from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
import os
import subprocess
from werkzeug.utils import secure_filename
from datetime import datetime
import librosa
from pydub import AudioSegment, effects
import noisereduce as nr
import numpy as np
from model_utils import load_model, predict_emotion
import logging

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_audio(file_path, frame_length=2048, hop_length=512, total_length = 173056):
    '''
    A process to an audio .wav file before executing a prediction.
      Arguments:
      - file_path - The system path to the audio file.
      - frame_length - Length of the frame over which to compute the speech features. default: 2048
      - hop_length - Number of samples to advance for each frame. default: 512

      Return:
        'X_3D' variable, containing a shape of: (batch, timesteps, feature) for a single file (batch = 1).
    '''
    # Fetch sample rate.
    _, sr = librosa.load(path = file_path, sr = None)
    # Load audio file
    rawsound = AudioSegment.from_file(file_path, duration = None)
    # Normalize to 5 dBFS
    normalizedsound = effects.normalize(rawsound, headroom = 5.0)

    # Transform the audio file to np.array of samples
    normal_x = np.array(normalizedsound.get_array_of_samples(), dtype = 'float32')
    xt, index = librosa.effects.trim(normal_x, top_db=30)
    # padded_x = np.pad(xt, (0, 173056-len(xt)), 'constant')
    if len(xt) < total_length:
          padded_x = np.pad(xt, (0, total_length - len(xt)), 'constant')
    else:
          padded_x = xt[:total_length]  # Truncate the signal if it's longer than total_length
    # Noise reduction
    final_x = nr.reduce_noise(padded_x, sr=sr)


    f1 = librosa.feature.rms(y = final_x, frame_length=frame_length, hop_length=hop_length, center=True, pad_mode='reflect').T # Energy - Root Mean Square
    f2 = librosa.feature.zero_crossing_rate(final_x, frame_length=frame_length, hop_length=hop_length,center=True).T # ZCR
    f3 = librosa.feature.mfcc(y = final_x, sr=sr, S=None, n_mfcc=40, hop_length = hop_length).T # MFCC

    # f1 = librosa.feature.rms(y=final_x, frame_length=frame_length, hop_length=hop_length) # Energy - Root Mean Square
    # f2 = librosa.feature.zero_crossing_rate(y=final_x , frame_length=frame_length, hop_length=hop_length, center=True) # ZCR
    # f3 = librosa.feature.mfcc(y=final_x, sr=sr, n_mfcc=13, hop_length = hop_length) # MFCC

    X = np.concatenate((f1, f2, f3), axis = 1)

    X_3D = np.expand_dims(X, axis=0)

    return X_3D

model = load_model()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        if 'audioFile' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['audioFile']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            original_filename = secure_filename(file.filename)
            filename, file_extension = os.path.splitext(original_filename)
            unique_filename = f"{filename}_{timestamp}{file_extension}"
            
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            X_3D = preprocess_audio(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            
            np.save(os.path.join('preprocessed', f'{unique_filename}_recorded.npy'), X_3D)
            # return jsonify({'message': 'File successfully saved', 'filename': unique_filename})
            return jsonify({'filename': unique_filename})
    else:
        return render_template('record.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'audioFile' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['audioFile']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            X_3D = preprocess_audio(file_path=filepath)
            
            np.save(os.path.join('preprocessed', f'{filename}.npy'), X_3D)

            
            
            return jsonify({'filename': filename})
    return render_template('upload.html')


@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        filename = data['filename']
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        X_3D = preprocess_audio(file_path)
        
        predicted_emotion, probabilities = predict_emotion(X_3D, model)
        # app.logger.info("Predicted Emotion is: ", predicted_emotion)
        return jsonify({'predicted_emotion': predicted_emotion, 'probabilities': probabilities})
    except Exception as e:
        app.logger.error(f'Error during prediction: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5000)
