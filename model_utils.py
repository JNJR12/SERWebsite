from keras.models import model_from_json
import keras
import numpy as np
import logging

# Path to your model and weights files
MODEL_JSON_FILE = 'model/model_nocalmcorrupted_mfcc40.json'
MODEL_WEIGHTS_FILE = 'model/weights_training_mfcc40_nocalmcorrupted.hdf5'

# MODEL_JSON_FILE = 'model/model_nocalmcorrupted_mfcc40_dropout.json'
# MODEL_WEIGHTS_FILE = 'model/model_weights_nocalmcorrupted_mfcc40_dropout.h5'

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
    emotion_labels = ['neutral', 'happy', 'sad', 'angry', 'fear', 'disgust', 'surprised']  # Adjust based on your model's classes
    accumulated_pred = np.zeros(len(emotion_labels))
    for snippet in X_3D:
        predictions = model.predict(snippet,use_multiprocessing=True)
        logging.info(f"Raw predicted values: {predictions}")
        accumulated_pred += predictions[0]
        
    # Average pred
    avg_pred = accumulated_pred/len(X_3D)
    
    predicted_label_index = np.argmax(avg_pred)
    
    predicted_emotion = emotion_labels[predicted_label_index]
    
    
    return predicted_emotion, avg_pred.flatten().tolist()
