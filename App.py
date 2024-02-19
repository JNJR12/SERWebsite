from flask import Flask, flash, redirect, render_template, request, jsonify, url_for
import os
import subprocess
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'm4a'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        # Implement the logic previously in process_audio.php
        # Save the file and process it with your Python script
        pass
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
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('upload', filename=filename))
    return render_template('upload.html')


@app.route('/predict', methods=['POST'])
def predict():
    # Implement the logic to make predictions using your ML model
    pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)
