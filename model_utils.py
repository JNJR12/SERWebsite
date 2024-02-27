from keras.models import model_from_json
import keras
import numpy as np
import logging

# Path to your model and weights files
MODEL_JSON_FILE = 'model/model_nocalmcorrupted_mfcc40.json'
MODEL_WEIGHTS_FILE = 'model/weights_training_mfcc40_nocalmcorrupted.hdf5'

# Load the model from JSON file
def load_model():
    with open(MODEL_JSON_FILE, "r") as json_file:
        loaded_model_json = json_file.read()
    model = model_from_json(loaded_model_json)
    # Load weights into the new model
    model.load_weights(MODEL_WEIGHTS_FILE)
    print("Loaded model from disk")
    
    # Compile the model if necessary
    model.compile(loss='categorical_crossentropy',
                optimizer='RMSProp',
                metrics=['categorical_accuracy'])
    
    return model

# Prediction function
def predict_emotion(X_3D, model):
    prediction = model.predict(X_3D)
    logging.info(f"Raw predicted values: {prediction}")
    
    predicted_label_index = np.argmax(prediction)
    emotion_labels = ['neutral', 'happy', 'sad', 'angry', 'fear', 'disgust', 'surprised']  # Adjust based on your model's classes
    predicted_emotion = emotion_labels[predicted_label_index]
    
    
    return predicted_emotion, prediction.flatten().tolist()
