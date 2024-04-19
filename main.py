from flask import Flask, render_template, request
from flask_mail import Mail, Message
from pytube import YouTube
from pydub import AudioSegment
import urllib.request
import re
import os
import zipfile

app = Flask(__name__)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'psanan_be21@thapar.edu'
app.config['MAIL_PASSWORD'] = 'jxzn dtoq uolt bqbz'

mail = Mail(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/mashup', methods=['POST'])
def mashup():
    singer_name = request.form['singer_name']
    num_songs = int(request.form['num_songs'])
    trimming_duration = int(request.form['trimming_duration'])
    recipient_email = request.form['email']

    # Check input constraints
    if num_songs < 10:
        return "Number of songs should be greater than 10."

    if trimming_duration < 20:
        return "Trimming duration should be greater than 20 seconds."

    # Your existing mashup code goes here
    x = singer_name.replace(' ', '')
    html = urllib.request.urlopen('https://www.youtube.com/results?search_query=' + str(x))
    video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())

    # Downloading songs
    downloaded_count = 0
    i = 0
    mashup_song = None  # Variable to store the mashup song
    while downloaded_count < num_songs and i < len(video_ids):
        try:
            yt = YouTube("https://www.youtube.com/watch?v=" + video_ids[i])
            print("Downloading File " + str(downloaded_count + 1) + " .......")
            stream = yt.streams.filter(only_audio=True).first()
            stream.download(filename=f'tempaudio-{downloaded_count}.mp3')

            # If this is the first song, save it as the mashup song
            if downloaded_count == 0:
                mashup_song = AudioSegment.from_file(f'tempaudio-{downloaded_count}.mp3')[:trimming_duration * 1000]

            # If not the first song, append to the mashup song
            else:
                aud_file = AudioSegment.from_file(f'tempaudio-{downloaded_count}.mp3')[:trimming_duration * 1000]
                mashup_song = mashup_song.append(aud_file, crossfade=1000)

            downloaded_count += 1
        except Exception as e:
            print(f"Error downloading video {downloaded_count + 1}: {e}")

        i += 1

    # Export the mashup song
    mashup_song.export(f'mashup_song.mp3', format='mp3')

    # Create a zip file containing mashedup songs and the mashup song
    zip_file_path = 'mashedup_songs.zip'
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for i in range(downloaded_count):
            audio_file_path = f'tempaudio-{i}.mp3'
            zipf.write(audio_file_path, os.path.basename(audio_file_path))

        # Add the mashup song to the zip
        zipf.write('mashup_song.mp3', 'mashup_song.mp3')

    # Send the zip file to the specified email
    send_email(recipient_email, zip_file_path)

    # Delete temporary files if required
    for i in range(downloaded_count):
        os.remove(f'tempaudio-{i}.mp3')
    os.remove('mashup_song.mp3')

    return "Mashup created and sent to the specified email."

def send_email(recipient_email, attachment_path):
    subject = 'Mashup Song'
    sender_email = 'psanan_be21@thapar.edu'

    message = Message(subject, sender=sender_email, recipients=[recipient_email])
    message.body = 'Enjoy the mashed-up song!'
    with app.open_resource(attachment_path) as attachment:
        message.attach(attachment_path, 'application/zip', attachment.read())

    mail.send(message)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
