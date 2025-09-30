from flask import Flask, render_template, redirect, url_for, request, send_file, flash, jsonify
import os, glob, json, random, string, logging, traceback
from datetime import datetime
from moviepy.editor import VideoFileClip
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de carpetas
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
PROGRESS_FILE = 'processing_progress.json'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Configurar logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_files():
    files = []
    for ext in ALLOWED_EXTENSIONS:
        files.extend(glob.glob(f"{UPLOAD_FOLDER}/*.{ext}"))
        files.extend(glob.glob(f"*.{ext}"))
    return [os.path.basename(f) for f in files]

def get_processed_files():
    return [f for f in os.listdir(PROCESSED_FOLDER) if os.path.isfile(os.path.join(PROCESSED_FOLDER, f))]

def save_progress(task_id, data):
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_tasks = json.load(f)
        else:
            all_tasks = {}
        all_tasks[task_id] = data
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(all_tasks, f, indent=2)
        logging.info(f"Progreso guardado para tarea {task_id}")
    except Exception as e:
        logging.error(f"Error guardando progreso: {e}")
        traceback.print_exc()

def get_progress(task_id):
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_tasks = json.load(f)
            return all_tasks.get(task_id, {})
    except Exception as e:
        logging.error(f"Error leyendo progreso: {e}")
        traceback.print_exc()
    return {}

def delete_progress(task_id):
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_tasks = json.load(f)
            if task_id in all_tasks:
                del all_tasks[task_id]
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(all_tasks, f, indent=2)
                logging.info(f"Tarea {task_id} eliminada del progreso")
    except Exception as e:
        logging.error(f"Error eliminando progreso: {e}")
        traceback.print_exc()

def generate_task_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

@app.route('/')
def index():
    active_tasks = {}
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                active_tasks = json.load(f)
    except Exception as e:
        logging.error(f"Error leyendo tareas activas: {e}")
        traceback.print_exc()
    return render_template('index1.html',
                           video_files=get_video_files(),
                           processed_files=get_processed_files(),
                           active_tasks=active_tasks)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo')
            return redirect(url_for('index'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logging.info(f"Subiendo archivo {filename} a {filepath}")
            file.save(filepath)
            flash('Video subido correctamente')
            return redirect(url_for('index'))

        flash('Tipo de archivo no permitido')
        return redirect(url_for('index'))

    except Exception as e:
        logging.error(f"Error en upload_file: {e}")
        traceback.print_exc()
        flash(f"Error subiendo archivo: {str(e)}")
        return redirect(url_for('index'))

# --- PROCESO DE VIDEO (dividir completo) ---
@app.route('/process1_video', methods=['GET', 'POST'])
def process_video1():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        segment_duration = int(request.form.get('duration', 29))

        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('process_video1'))

        filepath = next((p for p in [os.path.join(UPLOAD_FOLDER, video_filename), video_filename, os.path.join(os.getcwd(), video_filename)] if os.path.exists(p)), None)
        if not filepath:
            flash('No se encontró el archivo de video')
            return redirect(url_for('process_video1'))

        task_id = generate_task_id()
        try:
            logging.info(f"Iniciando división de video {video_filename} en segmentos de {segment_duration}s")
            video = VideoFileClip(filepath)
            duration = int(video.duration)
            total_segments = (duration + segment_duration - 1) // segment_duration

            progress_data = {
                'task_name': 'Dividir Video Completo',
                'video_file': video_filename,
                'total_segments': total_segments,
                'completed_segments': 0,
                'status': 'processing',
                'start_time': datetime.now().isoformat(),
                'segment_files': [],
                'current_action': 'Iniciando procesamiento...'
            }
            save_progress(task_id, progress_data)

            start = 0
            part_number = 1
            while start < duration:
                end = min(start + segment_duration, duration)
                part_filename = f'part_{part_number}.mp4'
                part_filepath = os.path.join(PROCESSED_FOLDER, part_filename)

                progress_data['current_action'] = f'Procesando segmento {part_number}/{total_segments}'
                progress_data['completed_segments'] = part_number - 1
                save_progress(task_id, progress_data)

                logging.info(f"Procesando segmento {part_number}: {start}s a {end}s -> {part_filepath}")
                clip = video.subclip(start, end)
                clip.write_videofile(part_filepath, codec="libx264", verbose=False, logger=None)
                clip.close()

                progress_data['segment_files'].append(part_filename)
                progress_data['completed_segments'] = part_number
                save_progress(task_id, progress_data)

                start += segment_duration
                part_number += 1

            video.close()
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            save_progress(task_id, progress_data)
            flash(f'Video procesado y dividido en {part_number-1} partes')

        except Exception as e:
            progress_data['status'] = 'error'
            progress_data['error'] = str(e)
            save_progress(task_id, progress_data)
            logging.error(f"Error dividiendo video: {e}")
            traceback.print_exc()
            flash(f'Error al procesar el video: {str(e)}')

        return redirect(url_for('index'))

    return render_template('process1.html', video_files=get_video_files())

# --- CORTE ÚNICO ---
@app.route('/corte_1video', methods=['GET', 'POST'])
def corte_1video():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        start_time = int(request.form.get('start_time', 305))
        segment_duration = int(request.form.get('duration', 29))

        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('corte_1video'))

        filepath = next((p for p in [os.path.join(UPLOAD_FOLDER, video_filename), video_filename, os.path.join(os.getcwd(), video_filename)] if os.path.exists(p)), None)
        if not filepath:
            flash('No se encontró el archivo de video')
            return redirect(url_for('corte_1video'))

        task_id = generate_task_id()
        try:
            logging.info(f"Iniciando corte único: {video_filename} desde {start_time}s por {segment_duration}s")
            video = VideoFileClip(filepath)
            end_time = min(start_time + segment_duration, video.duration)

            progress_data = {
                'task_name': 'Corte Único',
                'video_file': video_filename,
                'start_time': start_time,
                'end_time': end_time,
                'status': 'processing',
                'start_time_task': datetime.now().isoformat(),
                'current_action': f'Creando corte de {start_time}s a {end_time}s'
            }
            save_progress(task_id, progress_data)

            video_corte = video.subclip(start_time, end_time)
            part_filename = f'corte_{start_time}_{end_time}.mp4'
            part_filepath = os.path.join(PROCESSED_FOLDER, part_filename)
            video_corte.write_videofile(part_filepath, codec="libx264", verbose=False, logger=None)
            video_corte.close()
            video.close()

            progress_data['status'] = 'completed'
            progress_data['segment_files'] = [part_filename]
            progress_data['completed_segments'] = 1
            progress_data['end_time_task'] = datetime.now().isoformat()
            save_progress(task_id, progress_data)

            flash(f'Corte único generado: {part_filename}')
            logging.info(f'Corte único generado: {part_filename}')

        except Exception as e:
            progress_data['status'] = 'error'
            progress_data['error'] = str(e)
            save_progress(task_id, progress_data)
            logging.error(f"Error en corte único: {e}")
            traceback.print_exc()
            flash(f'Error al generar corte único: {str(e)}')

        return redirect(url_for('index'))

    return render_template('corte_1video.html', video_files=get_video_files())

# --- Obtener progreso de tarea ---
@app.route('/task_progress/<task_id>')
def get_task_progress(task_id):
    data = get_progress(task_id)
    return jsonify(data)

# --- Descargar archivo ---
@app.route('/download/<filename>')
def download_file(filename):
    try:
        path = os.path.join(PROCESSED_FOLDER, filename)
        if os.path.exists(path):
            return send_file(path, as_attachment=True)
        flash('Archivo no encontrado')
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error descargando archivo {filename}: {e}")
        traceback.print_exc()
        flash(f"Error descargando archivo: {str(e)}")
        return redirect(url_for('index'))

# --- Eliminar archivo ---
@app.route('/delete/<filename>')
def delete_file(filename):
    try:
        path = os.path.join(PROCESSED_FOLDER, filename)
        if os.path.exists(path):
            os.remove(path)
            flash('Archivo eliminado')
        else:
            flash('Archivo no encontrado')
    except Exception as e:
        logging.error(f"Error eliminando archivo {filename}: {e}")
        traceback.print_exc()
        flash(f"Error eliminando archivo: {str(e)}")
    return redirect(url_for('index'))

# --- Limpiar tareas completadas ---
@app.route('/cleanup')
def cleanup_completed():
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_tasks = json.load(f)
            all_tasks = {k:v for k,v in all_tasks.items() if v.get('status') != 'completed'}
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(all_tasks, f, indent=2)
            logging.info("Tareas completadas eliminadas")
            flash("Tareas completadas eliminadas")
    except Exception as e:
        logging.error(f"Error limpiando tareas: {e}")
        traceback.print_exc()
        flash(f"Error limpiando tareas: {str(e)}")
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
