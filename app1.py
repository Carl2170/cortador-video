from flask import Flask, render_template, redirect, url_for, request, send_file, flash, jsonify
import os
from moviepy.editor import *
import requests
import random
import string
from werkzeug.utils import secure_filename
import glob
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

# Configuración de uploads
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max

# Crear carpetas si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Archivo para guardar el progreso
PROGRESS_FILE = 'processing_progress.json'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_video_files():
    """Obtener lista de videos disponibles"""
    video_files = []
    # Buscar en uploads
    for ext in ALLOWED_EXTENSIONS:
        video_files.extend(glob.glob(f"{UPLOAD_FOLDER}/*.{ext}"))
    # Buscar en raíz
    for ext in ALLOWED_EXTENSIONS:
        video_files.extend(glob.glob(f"*.{ext}"))
    return [os.path.basename(f) for f in video_files]

def get_processed_files():
    """Obtener lista de archivos procesados"""
    return [f for f in os.listdir(PROCESSED_FOLDER) if os.path.isfile(os.path.join(PROCESSED_FOLDER, f))]

def save_progress(task_id, progress_data):
    """Guardar progreso en archivo JSON"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_progress = json.load(f)
        else:
            all_progress = {}
        
        all_progress[task_id] = progress_data
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(all_progress, f, indent=2)
    except Exception as e:
        print(f"Error guardando progreso: {e}")

def get_progress(task_id):
    """Obtener progreso de una tarea"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_progress = json.load(f)
            return all_progress.get(task_id, {})
    except:
        pass
    return {}

def delete_progress(task_id):
    """Eliminar progreso de una tarea completada"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_progress = json.load(f)
            
            if task_id in all_progress:
                del all_progress[task_id]
                with open(PROGRESS_FILE, 'w') as f:
                    json.dump(all_progress, f, indent=2)
    except Exception as e:
        print(f"Error eliminando progreso: {e}")

def generate_task_id():
    """Generar ID único para la tarea"""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

@app.route('/')
def index():
    # Cargar tareas en progreso
    active_tasks = {}
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                active_tasks = json.load(f)
    except:
        active_tasks = {}
    
    return render_template('index1.html', 
                         video_files=get_video_files(),
                         processed_files=get_processed_files(),
                         active_tasks=active_tasks)

@app.route('/upload', methods=['POST'])
def upload_file():
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
        file.save(filepath)
        flash('Video subido correctamente')
        return redirect(url_for('index'))
    
    flash('Tipo de archivo no permitido')
    return redirect(url_for('index'))

@app.route('/process1_video', methods=['GET', 'POST'])
def process_video1():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        segment_duration = int(request.form.get('duration', 29))
        
        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('process_video1'))
        
        # Buscar el archivo en diferentes ubicaciones
        filepath = None
        possible_paths = [
            os.path.join(UPLOAD_FOLDER, video_filename),
            video_filename,
            os.path.join(os.getcwd(), video_filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath or not os.path.exists(filepath):
            flash('No se encontró el archivo de video')
            return redirect(url_for('process_video1'))
        
        # Generar ID de tarea
        task_id = generate_task_id()
        
        try:
            video = VideoFileClip(filepath)
            duration = int(video.duration)
            total_segments = (duration + segment_duration - 1) // segment_duration
            
            # Guardar progreso inicial
            progress_data = {
                'task_name': 'Dividir Video Completo',
                'video_file': video_filename,
                'total_segments': total_segments,
                'completed_segments': 0,
                'status': 'processing',
                'start_time': datetime.now().isoformat(),
                'segment_files': []
            }
            save_progress(task_id, progress_data)
            
            part_number = 1
            start = 0
            
            while start < duration:
                end = min(start + segment_duration, duration)
                part_filename = f'part_{part_number}.mp4'
                part_filepath = os.path.join(PROCESSED_FOLDER, part_filename)
                
                # Actualizar progreso
                progress_data['current_action'] = f'Procesando segmento {part_number}/{total_segments}'
                progress_data['completed_segments'] = part_number - 1
                save_progress(task_id, progress_data)
                
                clip = video.subclip(start, end)
                clip.write_videofile(part_filepath, codec="libx264", verbose=False, logger=None)
                clip.close()
                
                progress_data['segment_files'].append(part_filename)
                progress_data['completed_segments'] = part_number
                save_progress(task_id, progress_data)
                
                start += segment_duration
                part_number += 1
            
            video.close()
            
            # Marcar como completado
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            save_progress(task_id, progress_data)
            
            flash(f'Video procesado y dividido en {part_number-1} partes')
            
        except Exception as e:
            # Marcar como error
            progress_data['status'] = 'error'
            progress_data['error'] = str(e)
            save_progress(task_id, progress_data)
            flash(f'Error al procesar el video: {str(e)}')
        
        return redirect(url_for('index'))
    
    return render_template('process1.html', video_files=get_video_files())

@app.route('/corte_1video', methods=['GET', 'POST'])
def corte_1video():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        start_time = int(request.form.get('start_time', 305))
        segment_duration = int(request.form.get('duration', 29))
        
        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('corte_1video'))
        
        # Buscar el archivo
        filepath = None
        possible_paths = [
            os.path.join(UPLOAD_FOLDER, video_filename),
            video_filename,
            os.path.join(os.getcwd(), video_filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            flash('No se encontró el archivo de video')
            return redirect(url_for('corte_1video'))
        
        # Generar ID de tarea
        task_id = generate_task_id()
        
        try:
            video = VideoFileClip(filepath)
            end_time = start_time + segment_duration
            
            if end_time > video.duration:
                end_time = video.duration
            
            # Guardar progreso inicial
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
            output_filename = f'corte_unico_{start_time}_{end_time}.mp4'
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            video_corte.write_videofile(output_path, codec="libx264", verbose=False, logger=None)
            video.close()
            video_corte.close()
            
            # Marcar como completado
            progress_data['status'] = 'completed'
            progress_data['output_file'] = output_filename
            progress_data['end_time_task'] = datetime.now().isoformat()
            save_progress(task_id, progress_data)
            
            flash('Corte único creado correctamente')
            
        except Exception as e:
            # Marcar como error
            progress_data['status'] = 'error'
            progress_data['error'] = str(e)
            save_progress(task_id, progress_data)
            flash(f'Error al crear el corte: {str(e)}')
        
        return redirect(url_for('index'))
    
    return render_template('corte1.html', video_files=get_video_files())

@app.route('/process_video', methods=['GET', 'POST'])
def process_video():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        start_time = int(request.form.get('start_time', 287))
        segment_duration = int(request.form.get('duration', 29))
        
        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('process_video'))
        
        # Buscar el archivo
        filepath = None
        possible_paths = [
            os.path.join(UPLOAD_FOLDER, video_filename),
            video_filename,
            os.path.join(os.getcwd(), video_filename)
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
        
        if not filepath:
            flash('No se encontró el archivo de video')
            return redirect(url_for('process_video'))
        
        # Generar ID de tarea
        task_id = generate_task_id()
        
        try:
            video = VideoFileClip(filepath)
            duration = int(video.duration)
            
            start = start_time
            end = start + segment_duration
            quantity = 1
            
            # Calcular total de segmentos
            total_segments = 0
            temp_start = start_time
            while temp_start < duration:
                total_segments += 1
                temp_start += segment_duration
            
            # Guardar progreso inicial
            progress_data = {
                'task_name': 'Segmentos desde Punto Específico',
                'video_file': video_filename,
                'start_time_param': start_time,
                'total_segments': total_segments,
                'completed_segments': 0,
                'status': 'processing',
                'start_time': datetime.now().isoformat(),
                'segment_files': [],
                'current_action': 'Iniciando procesamiento...'
            }
            save_progress(task_id, progress_data)
            
            while start < duration:
                if end > duration:
                    end = duration
                
                # Actualizar progreso
                progress_data['current_action'] = f'Recortando segmento {quantity}: {start}s - {end}s'
                progress_data['completed_segments'] = quantity - 1
                save_progress(task_id, progress_data)
                
                video_corte = video.subclip(start, end)
                output_filename = f'parte_{quantity}.mp4'
                output_path = os.path.join(PROCESSED_FOLDER, output_filename)
                
                video_corte.write_videofile(output_path, codec="libx264", verbose=False, logger=None)
                video_corte.close()
                
                progress_data['segment_files'].append(output_filename)
                progress_data['completed_segments'] = quantity
                save_progress(task_id, progress_data)
                
                start = end
                end += segment_duration
                quantity += 1
            
            video.close()
            
            # Marcar como completado
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now().isoformat()
            save_progress(task_id, progress_data)
            
            flash(f'Proceso terminado. Se crearon {quantity-1} videos.')
            
        except Exception as e:
            # Marcar como error
            progress_data['status'] = 'error'
            progress_data['error'] = str(e)
            save_progress(task_id, progress_data)
            flash(f'Error al procesar el video: {str(e)}')
        
        return redirect(url_for('index'))
    
    return render_template('process_video.html', video_files=get_video_files())

@app.route('/download/<filename>')
def download_file(filename):
    filepath = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        flash('Archivo no encontrado')
        return redirect(url_for('index'))

@app.route('/delete/<filename>')
def delete_file(filename):
    filepath = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash('Archivo eliminado correctamente')
    return redirect(url_for('index'))

@app.route('/progress/<task_id>')
def get_task_progress(task_id):
    """API para obtener el progreso de una tarea"""
    progress = get_progress(task_id)
    return jsonify(progress)

@app.route('/cleanup_completed')
def cleanup_completed():
    """Limpiar tareas completadas"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                all_progress = json.load(f)
            
            # Eliminar tareas completadas o con error
            tasks_to_remove = []
            for task_id, progress in all_progress.items():
                if progress.get('status') in ['completed', 'error']:
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del all_progress[task_id]
            
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(all_progress, f, indent=2)
            
            flash(f'Se limpiaron {len(tasks_to_remove)} tareas completadas')
    except Exception as e:
        flash(f'Error limpiando tareas: {str(e)}')
    
    return redirect(url_for('index'))

@app.route('/api/files')
def api_files():
    return jsonify({
        'video_files': get_video_files(),
        'processed_files': get_processed_files()
    })

@app.route('/delete_task/<task_id>')
def delete_task(task_id):
    """Eliminar una tarea específica del progreso"""
    delete_progress(task_id)
    flash('Tarea eliminada del historial de progreso')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)