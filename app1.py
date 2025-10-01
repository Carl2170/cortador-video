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



