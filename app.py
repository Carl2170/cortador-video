# from flask import Flask, render_template, redirect, url_for
# import os
# from moviepy.editor import *

# import requests
# import random
# import string



# app = Flask(__name__)

# # @app.route('/')
# # def hello():
# #     return 'Hola mundo'



# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/generar-email')
# def generate_random_email():
#     """Genera un correo electrónico temporal aleatorio."""
#     domain = "1secmail.com"
#     username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
#     email = f"{username}@{domain}"
#     return email

# @app.route('/check-email')
# def check_inbox():
#     """Consulta la bandeja de entrada para el correo electrónico temporal."""
#     #username, domain = email.split('@')
    
#     username1 ="50i3tecuv6" 
#     domain1 = "1secmail.com"
#     url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={username1}&domain={domain1}"
#     response = requests.get(url)
#     return response.json()

# @app.route('/ver-email')
# def get_message_details():
#     message_id = "219082587"
#     username1 ="50i3tecuv6" 
#     domain1 = "1secmail.com"
#     """Obtiene detalles de un mensaje específico."""
#     url = f"https://www.1secmail.com/api/v1/?action=readMessage&login={username1}&domain={domain1}&id={message_id}"
#     response = requests.get(url)
#     return response.json()


# @app.route('/process1_video')
# def process_video1():
#     # Nombre del archivo de video en la raíz del proyecto
#     video_filename = 'video.mp4'
#     filepath = os.path.join(os.getcwd(), video_filename)

#     if os.path.exists(filepath):
#         # Obtener la duración total del video
#         video = VideoFileClip(filepath)
#         duration = int(video.duration)

#         # Dividir el video en partes de 29 segundos
#         part_number = 1
#         start = 0
        
#         while start < duration:
#             end = min(start + 29, duration)
#             part_filename = f'part_{part_number}.mp4'
#             part_filepath = os.path.join(os.getcwd(), part_filename)
#             clip = video.subclip(start, end)
#             clip.write_videofile(part_filepath, codec="libx264")
#             start += 29
#             part_number += 1
        
#         return "Video procesado y dividido con éxito."
#     else:
#         return "No se encontró el archivo de video en la raíz del proyecto."
    
# @app.route('/corte_1video')
# def corte_1video():
#     start = 305
#     end = start + 29
#     video = VideoFileClip("video1.mp4")
#     videoCorte = video.subclip(start, end)
    
#     quantity = 1
#    # Generar nombre de archivo
#     nameVideo = f'part_1.mp4'
        
#     # Guardar el video redimensionado
#     videoCorte.write_videofile(nameVideo)

#     return "proceso terminado"


# @app.route('/process_video')
# def process_video():
#     start = 287
#     end = start + 29

#     video = VideoFileClip("video1.mp4")
#     duration = int(video.duration)
    
#     quantity = 1
#     while start < duration:
#         if end > duration:
#             end = duration
        
#         videoCorte = video.subclip(start, end)
#         #clip_resized = videoCorte.resize()
        
#         # Generar nombre de archivo
#         nameVideo = f'parte_{quantity}.mp4'
        
#         # Guardar el video redimensionado
#         videoCorte.write_videofile(nameVideo)
        
#         # Actualizar los valores de start y end para el próximo segmento
#         start = end
#         end += 29
#         quantity += 1

#     return "videos terminados"

# #comando para ejecutar el servidor
# # flask --app app --debug run host:0.0.0.0
# #flask --app app --debug run --host=0.0.0.0










import os
import glob
import json
import random
import string
import logging
import traceback
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip

# --- Config ---
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
PROGRESS_FILE = 'processing_progress.json'
MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1 GB (ajusta si quieres)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'cambia_esto')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Crear carpetas
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

# --- Helpers ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_files():
    files = []
    for ext in ALLOWED_EXTENSIONS:
        # uploads and root
        files.extend(glob.glob(os.path.join(UPLOAD_FOLDER, f"*.{ext}")))
        files.extend(glob.glob(f"*.{ext}"))
    # return base names, unique and sorted
    return sorted(list({os.path.basename(f) for f in files}))

def get_processed_files():
    return sorted([f for f in os.listdir(PROCESSED_FOLDER) if os.path.isfile(os.path.join(PROCESSED_FOLDER, f))])

def generate_task_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

def read_all_progress():
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        logging.error("Error leyendo progress file")
        traceback.print_exc()
    return {}

def save_all_progress(all_tasks):
    try:
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(all_tasks, f, indent=2)
    except Exception:
        logging.error("Error escribiendo progress file")
        traceback.print_exc()

def save_progress(task_id, data):
    try:
        all_tasks = read_all_progress()
        all_tasks[task_id] = data
        save_all_progress(all_tasks)
        logging.debug(f"Progreso guardado: {task_id} -> {data.get('status')}")
    except Exception:
        logging.error("Error guardando progreso")
        traceback.print_exc()

def delete_progress(task_id):
    try:
        all_tasks = read_all_progress()
        if task_id in all_tasks:
            del all_tasks[task_id]
            save_all_progress(all_tasks)
            logging.info(f"Tarea {task_id} borrada del progreso")
    except Exception:
        logging.error("Error eliminando progreso")
        traceback.print_exc()

def find_file(filename):
    # buscar en uploads y en cwd
    candidates = [
        os.path.join(UPLOAD_FOLDER, filename),
        os.path.join(os.getcwd(), filename)
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None

# --- Background workers (MoviePy) ---
def worker_split_full(task_id, video_path, segment_duration):
    logging.info(f"[{task_id}] worker_split_full start: {video_path} dur={segment_duration}")
    progress = {
        'task_name': 'Dividir Video Completo',
        'video_file': os.path.basename(video_path),
        'total_segments': 0,
        'completed_segments': 0,
        'segment_files': [],
        'status': 'processing',
        'current_action': 'Iniciando...',
        'start_time': datetime.now().isoformat()
    }
    save_progress(task_id, progress)
    try:
        with VideoFileClip(video_path) as video:
            duration = int(video.duration)
            total_segments = (duration + segment_duration - 1) // segment_duration
            progress['total_segments'] = total_segments
            save_progress(task_id, progress)

            part_number = 1
            start = 0
            while start < duration:
                end = min(start + segment_duration, duration)
                progress['current_action'] = f'Procesando segmento {part_number}/{total_segments} ({start}s-{end}s)'
                progress['completed_segments'] = part_number - 1
                save_progress(task_id, progress)

                out_name = f'part_{task_id}_{part_number}.mp4'
                out_path = os.path.join(PROCESSED_FOLDER, out_name)
                logging.info(f"[{task_id}] render segment {part_number}: {start}-{end} -> {out_name}")

                clip = video.subclip(start, end)
                clip.write_videofile(out_path, codec='libx264', verbose=False, logger=None)
                clip.close()

                progress['segment_files'].append(out_name)
                progress['completed_segments'] = part_number
                save_progress(task_id, progress)

                start += segment_duration
                part_number += 1

        progress['status'] = 'completed'
        progress['end_time'] = datetime.now().isoformat()
        save_progress(task_id, progress)
        logging.info(f"[{task_id}] worker_split_full finished, segments={len(progress['segment_files'])}")

    except Exception as e:
        logging.error(f"[{task_id}] Error in worker_split_full: {e}")
        traceback.print_exc()
        progress['status'] = 'error'
        progress['error'] = str(e)
        save_progress(task_id, progress)

def worker_cut_single(task_id, video_path, start_time, duration_time):
    logging.info(f"[{task_id}] worker_cut_single start: {video_path} start={start_time} dur={duration_time}")
    progress = {
        'task_name': 'Corte Único',
        'video_file': os.path.basename(video_path),
        'total_segments': 1,
        'completed_segments': 0,
        'segment_files': [],
        'status': 'processing',
        'current_action': f'Iniciando corte {start_time}s -> {start_time+duration_time}s',
        'start_time': datetime.now().isoformat()
    }
    save_progress(task_id, progress)
    try:
        with VideoFileClip(video_path) as video:
            end_time = min(start_time + duration_time, video.duration)
            progress['current_action'] = f'Cortando {start_time}s - {end_time}s'
            save_progress(task_id, progress)

            out_name = f'corte_{task_id}_{start_time}_{int(end_time)}.mp4'
            out_path = os.path.join(PROCESSED_FOLDER, out_name)
            logging.info(f"[{task_id}] writing single cut -> {out_name}")

            clip = video.subclip(start_time, end_time)
            clip.write_videofile(out_path, codec='libx264', verbose=False, logger=None)
            clip.close()

            progress['segment_files'].append(out_name)
            progress['completed_segments'] = 1
            progress['status'] = 'completed'
            progress['end_time'] = datetime.now().isoformat()
            progress['current_action'] = 'Completado'
            save_progress(task_id, progress)
            logging.info(f"[{task_id}] worker_cut_single finished -> {out_name}")

    except Exception as e:
        logging.error(f"[{task_id}] Error in worker_cut_single: {e}")
        traceback.print_exc()
        progress['status'] = 'error'
        progress['error'] = str(e)
        save_progress(task_id, progress)

def worker_split_from_start(task_id, video_path, start_time, segment_duration):
    logging.info(f"[{task_id}] worker_split_from_start start: {video_path} start={start_time} dur={segment_duration}")
    progress = {
        'task_name': 'Segmentos desde Punto Específico',
        'video_file': os.path.basename(video_path),
        'total_segments': 0,
        'completed_segments': 0,
        'segment_files': [],
        'status': 'processing',
        'current_action': 'Iniciando...',
        'start_time': datetime.now().isoformat(),
        'start_param': start_time
    }
    save_progress(task_id, progress)
    try:
        with VideoFileClip(video_path) as video:
            duration = int(video.duration)
            temp_start = start_time
            total_segments = 0
            while temp_start < duration:
                total_segments += 1
                temp_start += segment_duration
            progress['total_segments'] = total_segments
            save_progress(task_id, progress)

            start = start_time
            end = start + segment_duration
            idx = 1
            while start < duration:
                if end > duration:
                    end = duration
                progress['current_action'] = f'Recortando segmento {idx}/{total_segments} ({start}s-{end}s)'
                progress['completed_segments'] = idx - 1
                save_progress(task_id, progress)

                out_name = f'parte_{task_id}_{idx}.mp4'
                out_path = os.path.join(PROCESSED_FOLDER, out_name)
                logging.info(f"[{task_id}] render part {idx}: {start}-{end} -> {out_name}")

                clip = video.subclip(start, end)
                clip.write_videofile(out_path, codec='libx264', verbose=False, logger=None)
                clip.close()

                progress['segment_files'].append(out_name)
                progress['completed_segments'] = idx
                save_progress(task_id, progress)

                start = end
                end += segment_duration
                idx += 1

        progress['status'] = 'completed'
        progress['end_time'] = datetime.now().isoformat()
        save_progress(task_id, progress)
        logging.info(f"[{task_id}] worker_split_from_start finished -> segments={len(progress['segment_files'])}")

    except Exception as e:
        logging.error(f"[{task_id}] Error in worker_split_from_start: {e}")
        traceback.print_exc()
        progress['status'] = 'error'
        progress['error'] = str(e)
        save_progress(task_id, progress)

# --- Routes ---
@app.route('/')
def index():
    active_tasks = read_all_progress()
    return render_template('index.html',
                           video_files=get_video_files(),
                           processed_files=get_processed_files(),
                           active_tasks=active_tasks)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'ok': False, 'error': 'No file part'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'ok': False, 'error': 'No selected file'}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            logging.info(f"Uploaded file saved to {save_path}")
            return jsonify({'ok': True, 'filename': filename})
        else:
            return jsonify({'ok': False, 'error': 'Invalid extension'}), 400
    except Exception as e:
        logging.error(f"Error in upload_file: {e}")
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/start_split_full', methods=['POST'])
def start_split_full():
    """
    Inicia división completa (desde inicio 0) en background.
    Params JSON form: { "video_file": "...", "segment_duration": 29 }
    """
    data = request.get_json() or request.form
    video_file = data.get('video_file')
    segment_duration = int(data.get('segment_duration', 29))
    if not video_file:
        return jsonify({'ok': False, 'error': 'video_file missing'}), 400
    filepath = find_file(video_file)
    if not filepath:
        return jsonify({'ok': False, 'error': 'file not found'}), 404

    task_id = generate_task_id()
    thread = threading.Thread(target=worker_split_full, args=(task_id, filepath, segment_duration), daemon=True)
    thread.start()
    logging.info(f"Started background task {task_id} for split full")
    return jsonify({'ok': True, 'task_id': task_id, 'video_file': video_file})

@app.route('/start_cut_single', methods=['POST'])
def start_cut_single():
    """Inicia un corte único en background. Params: video_file, start_time, duration"""
    data = request.get_json() or request.form
    video_file = data.get('video_file')
    start_time = int(data.get('start_time', 0))
    duration_time = int(data.get('duration', 29))
    if not video_file:
        return jsonify({'ok': False, 'error': 'video_file missing'}), 400
    filepath = find_file(video_file)
    if not filepath:
        return jsonify({'ok': False, 'error': 'file not found'}), 404

    task_id = generate_task_id()
    thread = threading.Thread(target=worker_cut_single, args=(task_id, filepath, start_time, duration_time), daemon=True)
    thread.start()
    logging.info(f"Started background task {task_id} for single cut")
    return jsonify({'ok': True, 'task_id': task_id, 'video_file': video_file})

@app.route('/start_split_from', methods=['POST'])
def start_split_from():
    """Inicia división desde un punto específico. Params: video_file, start_time, segment_duration"""
    data = request.get_json() or request.form
    video_file = data.get('video_file')
    start_time = int(data.get('start_time', 0))
    segment_duration = int(data.get('segment_duration', 29))
    if not video_file:
        return jsonify({'ok': False, 'error': 'video_file missing'}), 400
    filepath = find_file(video_file)
    if not filepath:
        return jsonify({'ok': False, 'error': 'file not found'}), 404

    task_id = generate_task_id()
    thread = threading.Thread(target=worker_split_from_start, args=(task_id, filepath, start_time, segment_duration), daemon=True)
    thread.start()
    logging.info(f"Started background task {task_id} for split from start")
    return jsonify({'ok': True, 'task_id': task_id, 'video_file': video_file})

@app.route('/task_progress/<task_id>')
def task_progress(task_id):
    tasks = read_all_progress()
    return jsonify(tasks.get(task_id, {}))

@app.route('/api/files')
def api_files():
    return jsonify({
        'video_files': get_video_files(),
        'processed_files': get_processed_files()
    })

@app.route('/download/<filename>')
def download_file(filename):
    safe = os.path.basename(filename)
    path = os.path.join(PROCESSED_FOLDER, safe)
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    # also allow downloading uploaded original
    path2 = os.path.join(UPLOAD_FOLDER, safe)
    if os.path.exists(path2):
        return send_file(path2, as_attachment=True)
    return "File not found", 404

@app.route('/delete_processed/<filename>', methods=['POST'])
def delete_processed(filename):
    try:
        safe = os.path.basename(filename)
        path = os.path.join(PROCESSED_FOLDER, safe)
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Deleted processed file {path}")
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'error': 'not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting file: {e}")
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/delete_upload/<filename>', methods=['POST'])
def delete_upload(filename):
    try:
        safe = os.path.basename(filename)
        path = os.path.join(UPLOAD_FOLDER, safe)
        if os.path.exists(path):
            os.remove(path)
            logging.info(f"Deleted upload {path}")
            return jsonify({'ok': True})
        return jsonify({'ok': False, 'error': 'not found'}), 404
    except Exception as e:
        logging.error(f"Error deleting upload: {e}")
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/cleanup_completed', methods=['POST'])
def cleanup_completed():
    try:
        tasks = read_all_progress()
        removed = []
        for k, v in list(tasks.items()):
            if v.get('status') in ('completed', 'error'):
                removed.append(k)
                del tasks[k]
        save_all_progress(tasks)
        logging.info(f"Cleaned up tasks: {removed}")
        return jsonify({'ok': True, 'removed': removed})
    except Exception as e:
        logging.error(f"Error cleaning tasks: {e}")
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

# Run
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
