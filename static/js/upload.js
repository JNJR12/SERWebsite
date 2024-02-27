document.getElementById('uploadBtn').addEventListener('click', function() {
    const fileInput = document.querySelector('input[type="file"]');
    const audioFile = fileInput.files[0];
    if (!audioFile) {
        alert('Please select an audio file first.');
        return;
    }

    updateUploadStatus('Uploading...', 'text-blue-500');

    const formData = new FormData();
    formData.append('audioFile', audioFile);

    fetch('/upload', { method: 'POST', body: formData })
        .then(response => {
            if (!response.ok) throw new Error('Upload failed.');
            return response.json();
        })
        .then(data => {
            updateUploadStatus('Finished uploading.', 'text-green-500');
            console.log('Upload successful:', data.filename);
            // Update audio source for playback
            const audioPlayer = document.getElementById('audioPlayback');
            audioPlayer.src = URL.createObjectURL(audioFile);
            audioPlayer.hidden = false;

            // Show the "Predict" button
            document.getElementById('predictBtn').hidden = false;

            // Store the filename in sessionStorage for prediction
            sessionStorage.setItem('latestFile', data.filename);
        })
        .catch(error => {console.error('Error:', error);
        updateUploadStatus('Upload failed. Please try again.', 'text-red-500');
    });
});

function updateUploadStatus(message, textColorClass) {
    const statusDiv = document.getElementById('uploadStatus');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = textColorClass;
    }
}


document.getElementById('predictBtn').addEventListener('click', function() {
    const filename = sessionStorage.getItem('latestFile');
    if (!filename) {
        console.error('No file to predict.');
        return;
    }
    predictEmotion(filename);
});

let emotionChart;

function predictEmotion(filename) {
    updatePredictionStatus('Predicting...', 'text-blue-500');
    fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => {
        if (!response.ok) throw new Error('Prediction failed.');
        return response.json();
    })
    .then(data => {
        updatePredictionStatus('Prediction Complete', 'text-green-500');
        // Destroy the previous chart instance if it exists
        if (emotionChart) {
            emotionChart.destroy();
        }

        // Assuming 'data.probabilities' is your array of probabilities
        const ctx = document.getElementById('emotionChart').getContext('2d');
        const labels = ['neutral', 'happy', 'sad', 'angry', 'fear', 'disgust', 'surprised']; // Use the same labels as in your model
        const color = 'rgb(75, 192, 192)'; // Example color, choose what you prefer
        
        emotionChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Probability',
                    data: data.probabilities, // This should come from your prediction response
                    backgroundColor: color,
                    borderColor: color,
                    borderWidth: 1
                }]
            },
            options: {
                maintainAspectRatio: false,
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    
        // Update the prediction result text
        document.getElementById('predictionResult').textContent = 'Predicted Emotion: ' + data.predicted_emotion;
    })
    .catch(error => {
        console.error('Error:', error);
        updatePredictionStatus('Prediction failed. Please try again.', 'text-red-500');
    });
}

function updatePredictionStatus(message, textColorClass) {
    const statusDiv = document.getElementById('predictionStatus');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = textColorClass;
    }
}