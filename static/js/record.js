let audioURL; // Declare audioURL at the top level of the script so it's accessible everywhere

document.getElementById('startStopRecording').addEventListener('click', function() {
    const button = this;
    if (button.textContent === 'Start Recording') {
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                const mediaRecorder = new MediaRecorder(stream);
                let audioChunks = [];

                mediaRecorder.ondataavailable = event => {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = () => {
                    // Release the old audio URL if it exists
                    if (audioURL) {
                        URL.revokeObjectURL(audioURL);
                    }

                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    audioURL = URL.createObjectURL(audioBlob);

                    // Check if an audio element already exists
                    let audioElement = document.querySelector('audio');
                    if (audioElement) {
                        // Update the source of the existing audio element
                        audioElement.src = audioURL;
                    } else {
                        // Create a new audio element
                        audioElement = document.createElement('audio');
                        audioElement.src = audioURL;
                        audioElement.controls = true;
                        document.body.appendChild(audioElement);
                    }

                    uploadAudio(audioBlob); // Call upload function immediately after stop
                };

                mediaRecorder.start();
                button.textContent = 'Stop Recording';

                button.onclick = () => {
                    mediaRecorder.stop();
                    button.textContent = 'Start Recording';
                    button.onclick = setupStartButton; // Reset the button functionality
                };
            })
            .catch(error => console.error(error));
    }
});


function setupStartButton() {
    const startButton = document.getElementById('startStopRecording');
    startButton.textContent = 'Start Recording'; // Reset button text
    startButton.onclick = function() {
        // Reactivate start recording logic
    };
}

function uploadAudio(audioBlob) {
    const formData = new FormData();
    formData.append('audioFile', audioBlob, 'recording.wav');
    // Show uploading status
    updateUploadStatus('Uploading...', 'text-blue-500');

    fetch('/record', { method: 'POST', body: formData })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Network response was not ok.');
            }
        })
        .then(data => {
            console.log('Upload and processing successful. Data saved to:', data);
            updateUploadStatus('Processing complete. Data saved.', 'text-green-500');
            // If you want to fetch and display the saved JSON data, you can make another fetch request here using 'data' as the URL
            // document.getElementById('phpOutput').textContent = data
            sessionStorage.setItem('latestFile', data.filename);
            // predictEmotion(data.filename);
        })
        
        .catch(error => {
            console.error('Upload failed', error);
            updateUploadStatus('Upload failed. Please try again.', 'text-red-500');
            // Handle upload errors
        });
}

document.getElementById('predictButton').addEventListener('click', function() {
    const filename = sessionStorage.getItem('latestFile');
    if (!filename) {
        console.error('No file to predict.');
        return;
    }
    predictEmotion(filename);
});

let emotionChart; // Keep track of the chart instance

function predictEmotion(filename) {
    updatePredictionStatus('Predicting...', 'text-blue-500')
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
        updatePredictionStatus('Prediction complete.', 'text-green-500');

        // Update the prediction result text
        document.getElementById('predictionResult').textContent = 'Predicted Emotion: ' + data.predicted_emotion;

        // Assuming 'data.probabilities' is your array of probabilities
        const ctx = document.getElementById('emotionChart').getContext('2d');
        const labels = ['neutral', 'happy', 'sad', 'angry', 'fear', 'disgust', 'surprised']; // Use the same labels as in your model
        const color = 'rgb(75, 192, 192)'; // Example color, choose what you prefer

        // Destroy the previous chart instance if it exists
        if (emotionChart) emotionChart.destroy();

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
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
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

function updateUploadStatus(message, textColorClass) {
    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.textContent = message;
    // Reset any existing text color classes
    statusDiv.className = 'mt-4 ' + textColorClass;
}
