from flask import Flask, render_template, redirect, url_for, request, send_file, flash, jsonify
import os
from moviepy.editor import *
import requests
import random
import string
from werkzeug.utils import secure_filename
import glob

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

@app.route('/')
def index():
    return render_template('index1.html', 
                         video_files=get_video_files(),
                         processed_files=get_processed_files())

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo')
        return redirect(url_for('index'))  # CORREGIDO: era request.url
    
    file = request.files['file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo')
        return redirect(url_for('index'))  # CORREGIDO: era request.url
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('Video subido correctamente')
        return redirect(url_for('index'))  # CORREGIDO: era index1
    
    flash('Tipo de archivo no permitido')
    return redirect(url_for('index'))  # CORREGIDO: era index1

@app.route('/process1_video', methods=['GET', 'POST'])
def process_video1():
    if request.method == 'POST':
        video_filename = request.form.get('video_file')
        segment_duration = int(request.form.get('duration', 29))
        
        if not video_filename:
            flash('Por favor selecciona un video')
            return redirect(url_for('process_video1'))  # CORREGIDO: era process_video
        
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
            return redirect(url_for('process_video1'))  # CORREGIDO: era process_video
        
        try:
            video = VideoFileClip(filepath)
            duration = int(video.duration)
            part_number = 1
            start = 0
            
            while start < duration:
                end = min(start + segment_duration, duration)
                part_filename = f'part_{part_number}.mp4'
                part_filepath = os.path.join(PROCESSED_FOLDER, part_filename)
                
                clip = video.subclip(start, end)
                clip.write_videofile(part_filepath, codec="libx264", verbose=False, logger=None)
                
                start += segment_duration
                part_number += 1
            
            video.close()
            flash(f'Video procesado y dividido en {part_number-1} partes')
            
        except Exception as e:
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
        
        try:
            video = VideoFileClip(filepath)
            end_time = start_time + segment_duration
            
            if end_time > video.duration:
                end_time = video.duration
            
            video_corte = video.subclip(start_time, end_time)
            output_filename = f'corte_unico_{start_time}_{end_time}.mp4'
            output_path = os.path.join(PROCESSED_FOLDER, output_filename)
            
            video_corte.write_videofile(output_path, codec="libx264", verbose=False, logger=None)
            video.close()
            video_corte.close()
            
            flash('Corte único creado correctamente')
            
        except Exception as e:
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
        
        try:
            video = VideoFileClip(filepath)
            duration = int(video.duration)
            
            start = start_time
            end = start + segment_duration
            quantity = 1
            
            while start < duration:
                if end > duration:
                    end = duration
                
                video_corte = video.subclip(start, end)
                output_filename = f'parte_{quantity}.mp4'
                output_path = os.path.join(PROCESSED_FOLDER, output_filename)
                
                video_corte.write_videofile(output_path, codec="libx264", verbose=False, logger=None)
                video_corte.close()
                
                start = end
                end += segment_duration
                quantity += 1
            
            video.close()
            flash(f'Proceso terminado. Se crearon {quantity-1} videos.')
            
        except Exception as e:
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
        return redirect(url_for('index'))  # CORREGIDO: era index1

@app.route('/delete/<filename>')
def delete_file(filename):
    filepath = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        flash('Archivo eliminado correctamente')
    return redirect(url_for('index'))  # CORREGIDO: era index1

@app.route('/api/files')
def api_files():
    return jsonify({
        'video_files': get_video_files(),
        'processed_files': get_processed_files()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)