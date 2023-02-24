from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import requests
import os
import argparse
import subprocess
import time
import json

# Configuración del logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Definición de la función para manejar el comando /start
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hola, me encargo de generar subtítulos a los videos de youtube que me pases por acá")

def delete_files(filename):
    # lista todos los archivos en el directorio actual
    files = os.listdir('.')
    # recorre los archivos y elimina aquellos cuyo nombre contenga 'filename'
    for file in files:
        if filename in file:
            os.remove(file)

#paso a SRT
def generate_srt(input_file, output_file):
    with open(input_file, encoding='utf-8') as f:
        data = json.load(f)


    srt_lines = []
    for i, prediction in enumerate(data["prediction"]):
        time_begin = prediction["time_begin"]
        time_end = prediction["time_end"]
        transcript = prediction["transcription"]
        srt_lines.append(f"{i+1}\n{format_time(time_begin)} --> {format_time(time_end)}\n{transcript}\n\n")


    with open(output_file, "w") as f:
        f.writelines(srt_lines)


def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds // 60) % 60)
    seconds = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# Aca sucede la magia
def gladia_request(file, namefile):
    url = 'https://api.gladia.io/audio/text/audio-transcription/'
    headers = {
        'accept': 'application/json',
        'x-gladia-key': 'ba1c2a6d-4b43-4d80-9eab-3381563ddf9f'
    }

    files = {
        'audio': (file, open(file, 'rb'), 'audio/mpeg'),
        'language': (None, 'spanish'),
        'language_behaviour': (None, 'automatic multiple languages'),
    }

    response = requests.post(url, headers=headers, files=files)

    # Verificar si la solicitud se realizó correctamente
    if response.status_code == 200:
        # Guardar el contenido en un archivo
        with open(f'{namefile}.json', 'wb') as f:
            f.write(response.content)
            print("La respuesta se guardó correctamente")

        # Verificar si se ha escrito contenido en el archivo
        if len(response.content) > 0:
            cwd = os.getcwd()
            logging.warning(cwd)
            #srt_command = f"python ./srt.py {namefile}.json {namefile}.srt"
            generate_srt(f'{namefile}.json', f'{namefile}.srt')
            #subprocess.call(srt_command)
            return f'{namefile}.srt'
            
        else:
            print("La respuesta está vacía. No se generará el archivo SRT.")
    else:
        print("No se pudo realizar la solicitud. Código de estado HTTP:", response.status_code)


# función para manejar mensajes de texto
def handle_text(update, context):
    text = update.message.text
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Has enviado un mensaje de texto: {text}")

# Definición de la función para manejar los mensajes con documentos
def handle_document(update, context):
    document = update.message.document
    file_id = document.file_id
    file_name = document.file_name
    context.bot.get_file(file_id).download(file_name)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Archivo '{file_name}' recibido.")

# función para manejar enlaces
def handle_link(update, context):
    link = update.message.text
    print(link)
    yt_dlp_command = ["yt-dlp", "-x", "--audio-format","mp3", "--restrict-filenames", "--progress", "--output", "%(title)s", link]
    process = subprocess.Popen(yt_dlp_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout:
        print(line.rstrip())
        if line.startswith('[ExtractAudio] Destination:'):
            filename = line.split(':')[1].strip()
            print(filename)
    print(f"El nombre del archivo descargado es {filename}")
    # Obtener el nombre del archivo sin extensión
    basename, ext = os.path.splitext(filename)
    output_filename = f"{basename}.mp3"
    srt = gladia_request(output_filename, basename)
    print(srt)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Acá tenés el subtítulo generado a partir del video")
    context.bot.send_document(chat_id=update.effective_chat.id, document=open(srt, 'rb'))
    delete_files(basename)



# función principal del bot
def main():
    # Configuración del Updater con el token de acceso
    updater = Updater(token='6111889331:AAFs3IDp8ZyTB6Ine_DXgQQ_zuRxAO8Sux0', use_context=True)

    # Configuración de los manejadores de comandos y mensajes
    start_handler = CommandHandler('start', start)
    link_handler = MessageHandler(Filters.regex(r'https?://\S+'), handle_link)  # manejar enlaces
    document_handler = MessageHandler(Filters.document, handle_document)
    text_handler = MessageHandler(Filters.text & (~Filters.command), handle_text)


    # Agregando los manejadores al dispatcher
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(document_handler)
    updater.dispatcher.add_handler(link_handler)
    updater.dispatcher.add_handler(text_handler)

    # Inicio del polling
    updater.start_polling()

    # Mantenemos el bot en ejecución
    updater.idle()

if __name__ == '__main__':
    main()
