from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, session,json
from flask_bcrypt import Bcrypt
import mysql.connector
import jwt
import base64
import psycopg2
import os
from functools import wraps 
import datetime
from psycopg2.extras import DictCursor
from werkzeug.utils import secure_filename
from moviepy.editor import ImageSequenceClip,concatenate_videoclips
from moviepy.editor import VideoFileClip, AudioFileClip
import shutil
from PIL import Image, ImageOps
import ffmpeg
import subprocess

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management
bcrypt = Bcrypt(app)

#MySQL database configuration
# db_config = {
#     'host': 'localhost',
#     'user': 'bhavya',
#     'password': 'root',
#     'database': 'snapslide'
# }

connection = psycopg2.connect("postgresql://bhavya:Y5tkkZWCIJrFxaOlbFjlKw@wild-impala-8903.8nk.gcp-asia-southeast1.cockroachlabs.cloud:26257/defaultdb?sslmode=verify-full&sslrootcert=root.crt") 

with connection.cursor() as cursor:
    cursor.execute("SELECT now()")
    res = cursor.fetchall()
    connection.commit()
    print(res)
#connection = mysql.connector.connect(**db_config)
# Function to create users table if it doesn't exist
def create_users_table():
    try:
        cursor = connection.cursor()
        cursor.execute("""
             CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(100) NOT NULL
            )
        """)
        connection.commit()
    except Exception as e:
        print("Error creating users table:", e)
    finally:
        cursor.close()

# Function to create uploaded_images table if it doesn't exist
def create_uploaded_images_table():
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_images (
            id SERIAL PRIMARY KEY,
            user_id INT,
            Image_Id VARCHAR(255),
            data BYTEA NOT NULL
        )
    """)
    connection.commit()
    cursor.close()

# Function to create audio_files table if it doesn't exist
def create_audio_files_table():
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audio_files (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255),
            artist VARCHAR(255),
            duration INT,
            file_path VARCHAR(255),
            data BYTEA NOT NULL
        )
    """)
    connection.commit()

    audio_files = [
        ("Rick Roll", "Rick Astley", 181, "templates/Rick roll.mp3"),
        ("Pokemon Go Song", "Misha", 180, "templates/Pokemon go song.mp3"),
        ("Doraemon Opening Song", "Doraemon", 240, "templates/Doraemon Opening Song.mp3"),
    ]
    cursor.executemany("INSERT INTO audio_files (title, artist, duration, file_path) VALUES (%s, %s, %s, %s)", audio_files)
    connection.commit()

    cursor.close()
def login_req(func):
    @wraps(func)
    def decorated_function(*args,**kwargs):
        if'username'not in session:
            return redirect(url_for('login'))
        return func(*args,**kwargs)
    return decorated_function
def generate_token(username):
    expiration_time=datetime.datetime.utcnow()+datetime.timedelta(minutes=8)
    payload={
        'username':username,
        'exp':expiration_time
    }
    token = jwt.encode(payload,app.config['SECRET_KEY'],algorithm='HS256')
    return token
# Create necessary tables on startup
create_users_table()
create_uploaded_images_table()
create_audio_files_table()

@app.route('/')
def index():
    return render_template('landingpage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Hash the password using bcrypt
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        cursor = connection.cursor()
        try:
            # Use placeholders in the SQL query to prevent SQL injection
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
            connection.commit()
        except psycopg2.Error as err:
            # Handle the error (e.g., duplicate username)
            print(f"Error: {err}")
            connection.rollback()
            return render_template('signup.html', error="Username already exists. Please choose another.")
        finally:
            cursor.close()

        return render_template('login.html')

    # If the request method is GET, render the signup page
    return render_template('signup.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            return redirect(url_for("admin"))
        cursor = connection.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username, ))
        user = cursor.fetchone()
        cursor.close()
        print(user)

        if user and bcrypt.check_password_hash(user['password'], password):
            # User authenticated, generate JWT token
            # token = jwt.encode({'username': username}, app.config['SECRET_KEY'], algorithm='HS256')
            # You can set the token in a cookie or send it in the response JSON
            # response = jsonify({'token': token})
            # For setting the token in a cookie:
            # response.set_cookie('jwt_token', token, httponly=True, secure=True)  # Make sure to set secure=True in production
            session['username'] = username
            print("hello")
            return redirect(url_for('home'))
        else:
            # User not found or incorrect password
            error = 'Invalid username or password. Please try again.'
            return render_template('login.html', error=error)

    # Render login page for GET request
    return render_template('login.html')

@app.route('/home')
@login_req
def home():
    return render_template('home.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Clear the session
    return render_template('login.html')  # Redirect to login page


@app.route('/admin')
def admin():
    # Fetch users from the database
    cursor = connection.cursor(cursor_factory=DictCursor)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    
    # Iterate over each user and fetch their uploaded images
    for user in users:
        cursor.execute("SELECT * FROM uploaded_images WHERE user_id = %s", (user['id'],))
        images = cursor.fetchall()
        # print(f"User ID: {user['id']}, Images: {images}")
        # # Add the fetched images to the user dictionary if they exist
        # if images:
        #     user['images'] = images
    
    cursor.close()
    # # Print the fetched data (for debugging purposes)
    # print("Fetched Users:", users)
    # Pass the users to the admin.html template
    return render_template('admin.html', users=users,images=images)

@app.route('/success')
def success():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login page if not logged in
    return render_template('success.html')

@app.route('/upload', methods=['GET', 'POST'])
@login_req
def upload_image():
    # Get user ID from token or session
    # user_id = get_user_id_from_token_or_session()

    # Receive uploaded image file
    if request.method=='POST':
        # file = request.files['file']
        if 'fileInput' not in request.files:
            return redirect(request.url)
        files = request.files.getlist('fileInput')
        current_user = session.get('username')
        try:
            cursor = connection.cursor(cursor_factory=DictCursor)
            cursor.execute("SELECT * FROM users WHERE username = %s", (current_user, ))
            user = cursor.fetchone()
            cursor.close()
            if user:
                user_id = user['id']
                for file in files:
                    if file.filename == '':
                        continue  # Skip empty file inputs
                    image_data = file.read()
                    image_filename = str(file.filename)
                    print(image_filename)
                    cursor = connection.cursor(cursor_factory=DictCursor)
                    cursor.execute("INSERT INTO uploaded_images (user_id, Image_Id, data) VALUES (%s, %s, %s)",(user_id, image_filename, image_data))
                    connection.commit()
                return render_template('upload.html')
        except Exception as e:
            print(f"The error '{e}' occurred")
            return render_template('upload.html')
    return render_template('upload.html')
        # images_data = request.json
        # if images_data:
        #     for image in images_data:
        #         print(image['name'])  # Print the image file name
        #     return 'Images uploaded successfully', 200
        # else:
        #     return 'No images received', 400
        # return render_template('upload.html')
    #return jsonify(success=True, images=["image1.png", "image2.png"])
    # @app.route('/uploaded_images')
    # def insert_image(filename, data):
    #     cursor = connection.cursor()
    #     try:
    #         # Insert image into the database
    #         cursor.execute("INSERT INTO images (filename, data) VALUES (%s, %s)", (filename, data))
    #         connection.commit()
    #         print("Image inserted successfully")
    #     except Exception as e:
    #         print("Error inserting image:", e)
    #         connection.rollback()
    #     finally:
    #         cursor.close()

    # def uploaded_images():
    #      # Get the JSON data sent in the request
    #     images_json = request.json

    #     # Process each image in the JSON data
    #     for image in images_json:
    #         filename = image['name']
    #         data = image['src']  # Assuming 'src' contains the base64-encoded image data

    #         # Insert image into the database
    #         insert_image(filename, data)

    #     Return a response (you can customize this as needed)
    #     return jsonify({'message': 'Images uploaded successfully'})
        # Get user ID from token or session
        # user_id = get_user_id_from_token_or_session()

        # Fetch uploaded images for the user from the database
        # uploaded_images = fetch_uploaded_images(user_id)

        # Return the list of uploaded images
        # return jsonify(success=True, images=uploaded_images)

        # For now, returning a dummy response
    

def get_resolution(resolutionSelect):
    if resolutionSelect == '1080p':
        return (1920, 1080)
    elif resolutionSelect == '720p':
        return (1280, 720)
    elif resolutionSelect == '480p':
        return (854, 480)
    elif resolutionSelect == '360p':
        return (640, 360)
    elif resolutionSelect == '240p':
        return (426, 240)
    elif resolutionSelect == '144p':
        return (256, 144)
    
def find_dimensions(image, resolution):
    width, height = image.size
    target_width, target_height = resolution
    aspect_ratio = width / height
    target_aspect_ratio = target_width / target_height

    if aspect_ratio > target_aspect_ratio:
        new_width = target_width
        new_height = int(target_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(target_height * aspect_ratio)

    border_width = (target_width - new_width) // 2
    border_height = (target_height - new_height) // 2

    return new_width, new_height, border_width, border_height

def fetch_audio_file(username):
    cursor = connection.cursor()
    cursor.execute("SELECT file_path FROM audio_files WHERE title = %s", (username,))
    audio_file = cursor.fetchone()
    cursor.close()
    if audio_file:
        return audio_file[0]
    else:
        return None
    
def createvideo(images,selected_names,username,resolution,duration,transition):
    file_format = "mp4"
    # print(images)
    # resolution = get_resolution(resolution)
    # Fetch the audio file path from the database
    audio_file = fetch_audio_file(username)  # Replace with your function to fetch the audio file path

    if os.path.exists('output.' + file_format):
        os.remove('output.' + file_format)
    if os.path.exists('movie.' + file_format):
        os.remove('movie.' + file_format)
    input_files = []
    transitions= []
    durations= []
    # files= fetch_images(username)
    filepath= os.path.join('static', 'usernames', username)

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    #fetched_images= fetch_images(username)transition= transition.lower()
    for i in range(len(images)):
        image=images[i]
        name=selected_names[i]
        print(name)
        # if transition in ['circleopen', 'fade', 'wipeleft', 'wiperight', 'wipeup', 'wipedown', 'slideleft', 'slideright', 'slideup', 'slidedown', 'radial', 'smoothleft', 'smoothright', 'smoothup', 'smoothdown', 'circlecrop', 'rectangle', 'distance', 'fadeblack', 'fadewhite']:
        #     transitions= [transition]+transitions
        # else:
        #     transitions= ['fade']+transitions
        if not name.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            continue
        # id= int(id)
        duration = int(duration)
        filename= name
        # encoded_image = base64.b64encode(image).decode('utf-8')
        with open(os.path.join(filepath, filename), "wb") as file:
            file.write(base64.b64decode(image))

        image = Image.open(os.path.join(filepath, filename))
        image=image.resize(resolution)
        # width, height, border_width, border_height= find_dimensions(image, resolution)
        # image= image.resize((width, height))
        # image= ImageOps.expand(image, (border_width//2, border_height//2, border_width-(border_width//2), border_height-(border_height//2)), fill='black')
        image.save(os.path.join(filepath, "new_"+filename))

        # if not os.path.exists(os.path.join('static', 'mini_videos')):
        #     os.makedirs(os.path.join('static', 'mini_videos'))
        # output_path = os.path.join('static', 'mini_videos', f'{name}.mp4')
        sequence=[]
        for _ in range(30*duration):
            sequence.append(os.path.join(filepath, "new_"+filename))
        clip=ImageSequenceClip(sequence,fps=30)
        # clip.write_videofile(output_path)
        input_files.append(clip)
        # ffmpeg_cmd = [
        #     'ffmpeg',
        #     '-i', os.path.join(filepath, "new_" + filename),
        #     '-loop', '1', '-t', str(duration),
        #     '-filter_complex', f"[0:v]scale={resolution[0]}:{resolution[1]},setsar=1[v];[0:a]anull[a]",
        #     '-map', '[v]', '-map', '[a]',
        #     output_path
        # ]
        # try:
        #     subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
        # except subprocess.CalledProcessError as e:
        #     print("ffmpeg error:", e.stderr)
        # print(output_path)
        # input_files.append(output_path)
    
    # streams = [ffmpeg.input(input_file) for input_file in input_files]
    # for j in range(len(streams)-1):
    #     x = ffmpeg.filter([streams[j], streams[j+1]], 'xfade', transition=transition, duration= 1, offset= 5) 
    #     output_stream = x.output('movie'+ str(j) + '.' + file_format)
    #     ffmpeg.run(output_stream, overwrite_output=True)
    #     streams[j+1] = ffmpeg.input('movie'+ str(j) + '.' + file_format)
        
    # output_stream = streams[-1].output('movie.' + file_format)
    # ffmpeg.run(output_stream, overwrite_output=True)

        # Add audio to the video
    # video = VideoFileClip('movie.' + file_format)
    video = concatenate_videoclips(input_files)
    if audio_file:
        audio = AudioFileClip(audio_file)
        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)
        video = video.set_audio(audio)
    video.write_videofile(os.path.join("static", "final.mp4"), codec='libx264')


        # shutil.rmtree(os.path.join('static', 'usernames'))
        # for file in input_files:
        #     os.remove(file)
        # shutil.rmtree(os.path.join('static', 'mini_videos'))
        # for i in range(len(streams)-1):
        #     if os.path.exists('movie'+ str(i) + '.' + file_format):
        #         os.remove('movie'+ str(i) + '.' + file_format)
        # print("Done")
        # return render_template('createvideo.html')
    
@app.route('/createvideo', methods=['GET', 'POST'])
@login_req
def create_video():
    if request.method == 'GET':
        # Fetch the titles of audio files from the database
        cursor = connection.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT title FROM audio_files")
        audio_titles = [row['title'] for row in cursor.fetchall()]
        cursor.close()
        current_user = session.get('username')
        cursor = connection.cursor(cursor_factory=DictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (current_user, ))
        user = cursor.fetchone()
        cursor.close()
        if user:
            user_id = user['id']
            cursor = connection.cursor(cursor_factory=DictCursor)
            cursor.execute("SELECT * FROM uploaded_images WHERE user_id = %s", (user_id,))
            images = cursor.fetchall()

            modified_images = []
            for image in images:
                image_data = base64.b64encode(image['data']).decode('utf-8')
                modified_images.append({
                    'ImageId': image['id'],
                    'ImageData': image_data,
                    # 'ImageMetadata': image['data']  # Assuming ImageMetadata is the fourth column
                })
        # Pass the audio titles to the template
            cursor.close()
            return render_template('createvideo.html', images=modified_images)
        else:
            return render_template('createvideo.html')
    elif request.method == 'POST':

        images_to_select = request.form.getlist('delete')
        resolution = request.form.get('resolutionSelect')  # Get resolution from form data
        duration = request.form.get('defaultDurationInput')
        transition = request.form.get('transitionSelect')
        # Call get_resolution with resolution argument
        resolution_tup = get_resolution(resolution)
        if images_to_select:
            images=[]
            cursor = connection.cursor()
            for image_id in images_to_select:
                cursor.execute("SELECT * FROM uploaded_images WHERE id = %s", (image_id,))
                selected_image = cursor.fetchone()
                images.append(selected_image)
            encoded_images = []
            selected_names=[]
            for image in images:
                encoded_image = base64.b64encode(image[3]).decode('utf-8')
                encoded_images.append(encoded_image)
                selected_names.append(image[2])
            # print(encoded_images)
            cursor.close()
            current_user = session.get('username')
            cursor = connection.cursor(cursor_factory=DictCursor)
            cursor.execute("SELECT * FROM users WHERE username = %s", (current_user, ))
            user = cursor.fetchone()
            cursor.close()
            if user:
                user_id = user['id']
                cursor = connection.cursor(cursor_factory=DictCursor)
                cursor.execute("SELECT * FROM uploaded_images WHERE user_id = %s", (user_id,))
                previous_images = cursor.fetchall()

                modified_images = []
                for image in previous_images:
                    print(image)
                    image_data = base64.b64encode(image['data']).decode('utf-8')
                    modified_images.append({
                        'ImageId': image['id'],
                        'ImageData': image_data,
                        'name': image[2]
                        # 'ImageMetadata': image['data']  # Assuming ImageMetadata is the fourth column
                    })
            print(current_user,resolution_tup,duration,transition)
            createvideo(encoded_images,selected_names,current_user,resolution_tup,duration,transition)
            return render_template('createvideo.html', selected_images = encoded_images, images = modified_images)
        # Handle POST request (e.g., process form data)
        # Your POST request handling logic goes here # Placeholder for actual logic
    
@app.route('/audio_library')
def audio_library():
    # Fetch audio files from the database
    # audio_files = fetch_audio_files()

    # For now, returning a dummy response
    audio_files = [{"filename": "audio1.mp3", "description": "Description 1"},
                   {"filename": "audio2.mp3", "description": "Description 2"}]
    return render_template('audio_library.html', audio_files=audio_files)

@app.route('/static/audio/<path:filename>')
def audio_file(filename):
    return send_from_directory('static/audio', filename)

@app.route('/add_audio', methods=['GET', 'POST'])
@login_req
def add_audio():
    audio_file = request.form.get('audio_file')
    video_file = request.form.get('video_file')

    try:
        video = VideoFileClip(video_file)
        audio = AudioFileClip(audio_file)

        if audio.duration > video.duration:
            audio = audio.subclip(0, video.duration)

        final_video = video.set_audio(audio)
        final_video.write_videofile("final_video.mp4", codec='libx264')

        return render_template('createvideo.html', message="Audio added successfully")
    except Exception as e:
        print(f"An error occurred: {e}")
        return render_template('createvideo.html', message="An error occurred while adding audio")

@app.route('/download_video', methods=['GET', 'POST'])
@login_req
def download_video():
    return send_from_directory('static', 'movie.mp4', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)


'''
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import subprocess
import base64  # Added import for base64 module

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('createvideo.html')

@app.route('/create_video', methods=['POST'])
def create_video():
    data = request.get_json()
    image_paths = data.get('imagePaths', [])

    image_folder = 'uploaded_images'
    abs_image_folder = os.path.abspath(image_folder)
    os.makedirs(image_folder, exist_ok=True)

    for i, image_path in enumerate(image_paths):
        _, image_data = image_path.split(',')
        decoded_data = base64.b64decode(image_data)
        print("Decoded image data:", decoded_data[:50])  # Print first 50 bytes for inspection
        with open(os.path.join(image_folder, f'image_{i + 1}.png'), 'wb') as img_file:
            img_file.write(decoded_data)

    print("Uploaded images directory path:", abs_image_folder)

    # No need to run create_video.py as a subprocess, integrate its functionality here

    return jsonify(success=True)


@app.route('/uploaded_images')
def uploaded_images():
    image_folder = 'uploaded_images'
    abs_image_folder = os.path.abspath(image_folder)
    images = [f'{image_folder}/{img}' for img in os.listdir(image_folder) if img.endswith((".png", ".jpg"))]
    return jsonify(success=True, images=images)


if __name__ == '__main__':
    app.run(debug=True)
'''
