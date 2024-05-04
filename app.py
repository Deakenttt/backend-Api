# app.py
import subprocess
import uuid
from flask import Flask, request, jsonify, send_file
import requests
from werkzeug.utils import secure_filename
import os
import ffmpeg
from scipy.spatial import distance

from moviepy.editor import VideoFileClip

def create_app():
    app = Flask(__name__, static_folder='uploads', static_url_path='/uploads')
    app.config['UPLOAD_FOLDER'] = '/app/uploads/'
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    # Other setup code...
    return app


app = create_app()


@app.route('/', methods=['GET'])
def homepage():
    return "Homepage"


@app.route('/hello', methods=['GET'])
def hello():
    return "Hello"

@app.route('/get_similar', methods=['POST'])
def cosine_similarity():
    data = request.json
    query_vector = data['query_vector']
    vector_text_pairs = data['vectors']

    # Extract embeddings and their corresponding texts
    vectors = [pair['embeddings'] for pair in vector_text_pairs]
    texts = [pair['text'] for pair in vector_text_pairs]

    # Calculate cosine similarity for each vector
    # Return the index of the most similar vector
    most_similar_index = max(range(len(vectors)), key=lambda index: 1 - distance.cosine(query_vector, vectors[index]))

    return jsonify({'most_similar_text': texts[most_similar_index]})


# add a request handler that will take a video file URL and return the length of the video

from moviepy.editor import VideoFileClip

def get_video_length(url):
    # Download the video file from the URL
    response = requests.get(url, stream=True)
    with open('temp_video.mp4', 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    
    # Get the duration of the video
    clip = VideoFileClip('temp_video.mp4')
    duration = clip.duration
    clip.close()
    
    # Delete the temporary video file
    import os
    os.remove('temp_video.mp4')
    
    return duration

@app.route('/video_length', methods=['POST'])
def video_length():
    data = request.json
    directories = data

    if not directories:
        return jsonify({'error': 'No directories provided'}), 400

    video_lengths = []
    for directory in directories:
        directory_name = directory.get('directory_name')
        video_url = directory.get('video_url')

        if not video_url:
            video_lengths.append({'directory_name': directory_name, 'error': 'Video URL not provided'})
            continue

        try:
            length = get_video_length(video_url)
            video_lengths.append({'directory_name': directory_name, 'video_url': video_url, 'length': length})
        except Exception as e:
            video_lengths.append({'directory_name': directory_name, 'video_url': video_url, 'error': str(e)})

    return jsonify({'video_lengths': video_lengths}), 200