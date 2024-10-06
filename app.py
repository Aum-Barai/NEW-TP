import os
from flask import Flask, request, render_template, jsonify
import ssdeep
import sdhash
import tlsh
import pymrsh

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'docx', 'mp3', 'wav', 'mp4', 'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_type(filename):
    ext = filename.rsplit('.', 1)[1].lower()
    if ext in {'txt', 'docx'}:
        return 'text'
    elif ext in {'mp3', 'wav'}:
        return 'audio'
    elif ext in {'mp4', 'avi'}:
        return 'video'
    else:
        return 'unknown'

def calculate_similarity(file1_path, file2_path, file_type):
    if file_type == 'text':
        # Use SSDeep for text files
        hash1 = ssdeep.hash_from_file(file1_path)
        hash2 = ssdeep.hash_from_file(file2_path)
        similarity = ssdeep.compare(hash1, hash2)
        algorithm = 'SSDeep'
    elif file_type in ['audio', 'video']:
        # Use MRSH-V2 for audio and video files
        hash1 = pymrsh.hash_file(file1_path)
        hash2 = pymrsh.hash_file(file2_path)
        similarity = pymrsh.compare(hash1, hash2)
        algorithm = 'MRSH-V2'
    else:
        return None, None

    return similarity, algorithm

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'file1' not in request.files or 'file2' not in request.files:
            return jsonify({'error': 'No file part'})
        
        file1 = request.files['file1']
        file2 = request.files['file2']
        
        if file1.filename == '' or file2.filename == '':
            return jsonify({'error': 'No selected file'})
        
        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            file1_path = os.path.join(app.config['UPLOAD_FOLDER'], file1.filename)
            file2_path = os.path.join(app.config['UPLOAD_FOLDER'], file2.filename)
            
            file1.save(file1_path)
            file2.save(file2_path)
            
            file_type = get_file_type(file1.filename)
            
            similarity, algorithm = calculate_similarity(file1_path, file2_path, file_type)
            
            if similarity is not None:
                return jsonify({
                    'similarity': similarity,
                    'algorithm': algorithm,
                    'file_type': file_type,
                    'file1': file1.filename,
                    'file2': file2.filename
                })
            else:
                return jsonify({'error': 'Unsupported file type'})
    
    return render_template('index.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)