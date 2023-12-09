import datetime
import json
import requests
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
import sqlite3
import random
import os
import smtplib
import ssl
from email.message import EmailMessage
from ftplib import FTP
from io import BytesIO
from dotenv import load_dotenv, dotenv_values
import redis
import secrets
import string
import dotenv

app = Flask(__name__)
CACHE_TIMEOUT = 600
PER_PAGE = 15
load_dotenv()
found_dotenv = dotenv.find_dotenv('.env')
print(found_dotenv)
app = Flask(__name__)
print(os.getenv("sender_password"))
app.secret_key = secrets.token_hex(16)

redis_client = redis.from_url(os.getenv("redis"))

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

login_manager = LoginManager(app)
login_manager.login_view = 'login'

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL
    )
''')
conn.commit()
conn.close()

class User(UserMixin):
    def __init__(self, user_id, username, email, password):
        self.id = user_id
        self.username = username
        self.email = email
        self.password = password

    def get_id(self):
        return self.id

    def get_username(self):
        return self.username

    def get_email(self):
        return self.email

    def get_password(self):
        return self.password

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

# Registration route
@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_hash(password)

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ? OR email = ?', (username, email))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))

        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed_password))
        conn.commit()
        conn.close()

        flash('Registration successful', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')
    
verification_codes = {}
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()

        conn.close()

        if user_data and check_password(user_data[3], password):
            verification_code = ''.join(random.choices(string.digits, k=6))
            verification_codes[username] = verification_code
            send_verification_code(user_data[2], verification_code)
            return render_template('enter_verification_code.html', username=username)
    return render_template('login.html')

def send_verification_code(email, code):
    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    subject = "Code to login otrpo"
    body = code

    em = EmailMessage()
    em["From"] = sender_email
    em["To"] = email
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, email, em.as_string())

@app.route("/verify_code", methods=['POST'])
def verify_code():
    entered_code = request.form['code']
    username = request.form['username']
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user_data = cursor.fetchone()

    conn.close()
    stored_code = verification_codes.get(username)

    if stored_code and entered_code == stored_code:
        del verification_codes[username]  # Remove the used verification code
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])  # Replace with actual user details
        login_user(user)
        flash('Login successful', 'success')
        return redirect(url_for('main'))
    else:
        flash('Invalid verification code', 'error')
        return redirect(url_for('login'))


from flask_oauthlib.client import OAuth
app.config['GITHUB_CLIENT_ID'] = os.getenv("GITHUB_CLIENT_ID")
app.config['GITHUB_CLIENT_SECRET'] =  os.getenv("GITHUB_CLIENT_SECRET")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

oauth = OAuth(app)

github = oauth.remote_app(
    'github',
    consumer_key=app.config['GITHUB_CLIENT_ID'],
    consumer_secret=app.config['GITHUB_CLIENT_SECRET'],
    request_token_params=None,
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
)

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

@app.route('/github/login')
def github_login():
    return github.authorize(callback=url_for('github_authorized', _external=True))


@app.route('/github/authorized')
@github.authorized_handler
def github_authorized(resp):
    if resp is None or 'access_token' not in resp:
        flash('Access denied: reason={} error={}'.format(
            request.args['error_reason'],
            request.args['error_description']
        ), 'error')
        return redirect(url_for('main'))

    session['github_token'] = (resp['access_token'], '')
    user_info = github.get('user')
    username = user_info.data['login']

    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user_data = cursor.fetchone()

    if user_data:
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        login_user(user)
        flash('Login via GitHub successful', 'success')
        conn.close()
        return redirect(url_for('main'))
    else:
        cursor.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, username, generate_hash(username)))
        conn.commit()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        print(user_data)
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        login_user(user)
        flash('Login via GitHub successful', 'success')
        return redirect(url_for('main'))

recovery_codes = {}

@app.route("/recover_password", methods=['GET', 'POST'])
def recover_password():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND email = ?', (username, email))
        user_data = cursor.fetchone()

        conn.close()

        if user_data:
            recovery_code = ''.join(random.choices(string.digits, k=6))
            recovery_codes[username] = {"code": recovery_code, "email": email}
            send_recovery_code(email, recovery_code)
            return render_template('recover_password.html', username=username)

    return render_template('recover_password_request.html')

def send_recovery_code(email, code):
    sender_email = os.getenv("sender_email")
    sender_password = os.getenv("sender_password")
    subject = "Code to login otrpo"
    body = code

    em = EmailMessage()
    em["From"] = sender_email
    em["To"] = email
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, email, em.as_string())

@app.route("/recover_password/submit", methods=['POST'])
def recover_password_submit():
    username = request.form['username']
    entered_code = request.form['code']
    new_password = request.form['new_password']
    stored_recovery_data = recovery_codes.get(username)

    if stored_recovery_data and entered_code == stored_recovery_data['code']:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE username = ?', (generate_hash(new_password), username))
        conn.commit()
        conn.close()

        # Remove the used recovery code
        del recovery_codes[username]

        flash('Password recovery successful', 'success')
        return redirect(url_for('login'))
    else:
        flash('Invalid recovery code', 'error')

@app.route('/github/logout')
@login_required
def github_logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('main'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logout successful', 'success')
    return redirect(url_for('main'))

from werkzeug.security import generate_password_hash, check_password_hash

def generate_hash(password):
    return generate_password_hash(password, method='pbkdf2:sha256')

def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)

@app.route("/profile")
@login_required
def profile():
    return render_template('profile.html', user=current_user)

def update_user_password(user_id, new_password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    hashed_password = hash_password(new_password)
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed_password, user_id))

    conn.commit()
    conn.close()

@app.route("/", methods=['GET', 'POST'])
def main():
    page = int(request.args.get('page', 1)) 
    url_count = 'https://pokeapi.co/api/v2/pokemon'
    count = get_data(url_count)["count"]
    total_pages = count // PER_PAGE + (count % PER_PAGE > 0)
    search = request.args.get('search', '')

    cached_data = redis_client.get(f'page_{page}')
    
    if cached_data:
        return render_template("index.html", data=json.loads(cached_data.decode('utf-8')), page=page, total_pages=total_pages, per_page=PER_PAGE, search=search)

    pokemon_data = []
    pokemon_data = get_pokemon_page(page, PER_PAGE)
    
    redis_client.set(f'page_{page}', json.dumps(pokemon_data))

    return render_template("index.html", data=pokemon_data, page=page, total_pages=total_pages, per_page=PER_PAGE, search=search)

def get_pokemon_data(item):
    if type(item) is str or type(item) is int:
        pokemon_url = f'https://pokeapi.co/api/v2/pokemon/{item}/'
    else: 
        pokemon_url = item["url"]

    cached_data = redis_client.get(f'{pokemon_url}')
    if cached_data:
        return json.loads(cached_data.decode('utf-8'))

    pokemon_info = get_data(pokemon_url)
    front_default = pokemon_info["sprites"]["front_default"]
    id = pokemon_info["id"]
    name = pokemon_info["name"]
    hp = pokemon_info["stats"][0]["base_stat"]
    attack = pokemon_info["stats"][1]["base_stat"]
    defense = pokemon_info["stats"][2]["base_stat"]
    specialattack = pokemon_info["stats"][3]["base_stat"]
    specialdefense = pokemon_info["stats"][4]["base_stat"]
    speed = pokemon_info["stats"][5]["base_stat"]
    types = [t["type"]["name"] for t in pokemon_info["types"]]

    pokemon_data = {
        "name": name, 
        "id": id,
        "front_default": front_default, 
        "hp": hp,
        "attack": attack, 
        "defense": defense, 
        "special-attack": specialattack, 
        "special-defense": specialdefense,
        "speed": speed, 
        "types": types
    }

    redis_client.set(f'{pokemon_url}', json.dumps(pokemon_data))

    return pokemon_data

@app.route("/pokemon/<int:id>", methods=['GET'])
def pokemon(id):
    pokemon = get_pokemon_data(id)
    return(jsonify(pokemon))

@app.route("/fight", methods=['GET'])
def battle():
    player_id = request.args.get('player')
    enemy = get_random_pokemon()
    player = get_pokemon_data(player_id)
    global battle_data
    battle_data = {
        "player": player,
        "enemy": enemy
    }
    return render_template("battle.html", player=player, enemy=enemy)

rounds = 0
@app.route("/fight/<int:player_roll>", methods=['POST'])
def update_battle(player_roll):
    global battle_data
    global rounds
    player = battle_data["player"]
    enemy = battle_data["enemy"]

    enemy_roll = random.randint(1, 10)
    player_attack = player_roll % 2 == enemy_roll % 2
    if player_attack:
        if enemy["defense"] > 0:
            enemy["defense"] -= player["attack"]
        else:
            enemy["hp"] -= player["attack"]
    else:
        if player["defense"] > 0:
            player["defense"] -= enemy["attack"]
        else:
            player["hp"] -= enemy["attack"]
    rounds += 1
    winner = None
    if player["hp"] <= 0:
        winner = enemy
    elif enemy["hp"] <= 0:
        winner = player

    if winner:
        record_battle(winner["id"], player["id"], enemy["id"], rounds)

    battle_data["player"] = player
    battle_data["enemy"] = enemy

    return jsonify({
    "player": player,
    "enemy": enemy,
    "winner": winner
})

@app.route("/fight/fast", methods=['GET'])
def fast_battle():
    global battle_data
    player = battle_data["player"]
    enemy = battle_data["enemy"]
    rounds = 0

    while player["hp"] > 0 and enemy["hp"] > 0:
        player_roll = random.randint(1, 10)
        enemy_roll = random.randint(1, 10)

        player_attack = player_roll % 2 == enemy_roll % 2
        if player_attack:
            if enemy["defense"] > 0:
                enemy["defense"] -= player["attack"]
            else:
                enemy["hp"] -= player["attack"]
        else:
            if player["defense"] > 0:
                player["defense"] -= enemy["attack"]
            else:
                player["hp"] -= enemy["attack"]

        rounds += 1

    winner = None
    if player["hp"] <= 0:
        winner = enemy
    elif enemy["hp"] <= 0:
        winner = player

    if winner:
        record_battle(winner["id"], player["id"], enemy["id"], rounds)

    battle_data["player"] = player
    battle_data["enemy"] = enemy

    return jsonify({
    "player": player,
    "enemy": enemy,
    "winner": winner
})

@app.route("/random")
def random_pokemon():
    pokemon_data = [get_random_pokemon()]
    return render_template("index.html", data=pokemon_data, page=1, total_pages=1, per_page=PER_PAGE, search=None)

@app.route("/pokemon/list", methods=['GET'])
def get_pokemon_list():
    characteristic = request.args.get('characteristic')
    pokemon_data = [get_random_pokemon()]
    if characteristic not in pokemon_data[0]:
        return "Недопустимая характеристика", 400
    selected_characteristic = [pokemon[characteristic] for pokemon in pokemon_data]
    return jsonify(selected_characteristic)

@app.route("/search")
def search_pokemon():
    # Получите текст для поиска из параметров запроса (например, "text")
    search_text = request.args.get('text', '').lower()
    pokemon_data = []
    if not search_text:
        return "pipec"
    url = 'https://pokeapi.co/api/v2/pokedex/national'
    data = get_data(url)["pokemon_entries"]
    for item in range(len(data)):
        if data[item]["pokemon_species"]["name"].find(search_text) != -1:
            pokemon_data.append(get_pokemon_data(data[item]["pokemon_species"]["name"]))

    return render_template("index.html", data=pokemon_data, page=1, total_pages=1, per_page=9999, search=None)


def get_pokemon_page(page, PER_PAGE):
    offset = (page - 1) * PER_PAGE
    url = f'https://pokeapi.co/api/v2/pokemon?limit={PER_PAGE}&offset={offset}'
    pokemon_data = []
    data = get_data(url)["results"]
    for item in data:
        pokemon_data.append(get_pokemon_data(item))
    return pokemon_data

def get_random_pokemon():
    url = 'https://pokeapi.co/api/v2/pokedex/national'
    data = get_data(url)["pokemon_entries"]
    return(get_pokemon_data(random.choice(data)["pokemon_species"]["name"]))

def get_data(url):
    response = requests.get(url, timeout=5) 
    return json.loads(response.text)

conn = sqlite3.connect('battles.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS battles (
        id INTEGER PRIMARY KEY,
        timestamp DATETIME,
        player_id INTEGER,
        enemy_id INTEGER,
        winner_id INTEGER,
        rounds INTEGER
    )
''')
conn.commit()
conn.close()

def record_battle(winner_id, player_id, enemy_id, rounds):
    if current_user.is_authenticated: 
        a = current_user.get_username()
    else:
        a = None
    timestamp = datetime.datetime.now()
    conn = sqlite3.connect('battles.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO battles (timestamp, player_id, enemy_id, winner_id, rounds, user) VALUES (?, ?, ?, ?, ?, ?)',
                   (timestamp, player_id, enemy_id, winner_id, rounds, a))
    
    conn.commit()
    conn.close()
    
    return 'Результат боя сохранен в базе данных.'

@app.route('/reviews')
def reviews():
    pokemon_id = request.args.get('pokemon_id')
    pokemon = get_pokemon_data(pokemon_id)
    return render_template("review.html", pokemon=pokemon)

@app.route('/add_review', methods=['POST'])
def add_review():
    data = request.json
    conn = sqlite3.connect('pokemon_reviews.db')
    c = conn.cursor()
    c.execute("INSERT INTO reviews (pokemon_id, username, review_text, rating) VALUES (?, ?, ?, ?)",
              (data['pokemon_id'], data['username'], data['review_text'], data['rating']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Отзыв успешно добавлен."})

# Получение отзывов по ID покемона
@app.route('/get_reviews/<int:pokemon_id>', methods=['GET'])
def get_reviews(pokemon_id):
    conn = sqlite3.connect('pokemon_reviews.db')
    c = conn.cursor()
    c.execute("SELECT username, review_text, rating FROM reviews WHERE pokemon_id=?", (pokemon_id,))
    reviews = [{"username": row[0], "review_text": row[1], "rating": row[2]} for row in c.fetchall()]
    conn.close()
    return jsonify({"reviews": reviews})

# Добавление оценки
@app.route('/add_rating', methods=['POST'])
def add_rating():
    data = request.json
    conn = sqlite3.connect('pokemon_reviews.db')
    c = conn.cursor()
    c.execute("INSERT INTO ratings (pokemon_id, rating) VALUES (?, ?)",
              (data['pokemon_id'], data['rating']))
    conn.commit()
    conn.close()
    return jsonify({"message": "Оценка успешно добавлена."})

# Получение средней оценки по ID покемона
@app.route('/get_average_rating/<int:pokemon_id>', methods=['GET'])
def get_average_rating(pokemon_id):
    conn = sqlite3.connect('pokemon_reviews.db')
    c = conn.cursor()
    c.execute("SELECT AVG(rating) FROM ratings WHERE pokemon_id=?", (pokemon_id,))
    average_rating = c.fetchone()[0]
    conn.close()
    return jsonify({"average_rating": average_rating})

conn = sqlite3.connect('pokemon_reviews.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER,
    username TEXT,
    review_text TEXT,
    rating INTEGER
)''')

c.execute('''CREATE TABLE IF NOT EXISTS ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER,
    rating INTEGER
)''')

conn.commit()
conn.close()

conn = sqlite3.connect('users.db')
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password TEXT
    )
''')

conn.commit()
conn.close()


@app.route("/POCHTA", methods=["POST"])
def send_fast_fight_result():
    # Get the email address from the request body
    data = request.get_json()
    email_receiver = data.get("email")
    winner = data.get("winner")

    if not email_receiver:
        return jsonify({"error": "Email is required"}), 400

    sender_email = os.getenv("sender_email")# Set there email
    sender_password =  os.getenv("sender_password") # Set there password

    subject = "Fast Fight Results"
    body = f"Winner: {winner}"

    em = EmailMessage()
    em["From"] = sender_email
    em["To"] = email_receiver
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, email_receiver, em.as_string())

    return jsonify({"message": body})

def get_ftp_file_list():
    # Укажите данные для подключения к вашему FTP-серверу
    ftp = FTP("ftp.byethost5.com")
    ftp.login(
        user = os.getenv("FTP_USER"),
        passwd= os.getenv("FTP_PASSWORD"),
    )

    ftp.cwd("htdocs")

    # Получите список файлов
    files = ftp.nlst()

    # Закройте соединение с FTP
    ftp.quit()

    return files


def send_ftp(file_list, data):
    current_datetime = datetime.datetime.now()
    folder_name = current_datetime.strftime("%Y%m%d")
    ftp = FTP("ftp.byethost5.com")
    ftp.login(
        user = os.getenv("FTP_USER"),
        passwd= os.getenv("FTP_PASSWORD"),
    )
    if folder_name in file_list:
        ftp.cwd("htdocs")
        ftp.cwd(folder_name)
    else:
        ftp.cwd("htdocs")
        ftp.mkd(folder_name)
        ftp.cwd(folder_name)
    markdown = create_Markdown(data)
    buffer = BytesIO(markdown.encode("utf-8"))
    ftp.storbinary(f"STOR {data['name']}.md", buffer)
    ftp.quit()
    return jsonify({"message": "OK"})


@app.route("/api/getFtpFiles", methods=["GET"])
def get_ftp_files():
    file_list = get_ftp_file_list()
    return jsonify({"files": file_list})


@app.route("/api/sendFtpFile", methods=["GET"])
def send_ftp_files():
    print(request.args.get('pokemon'))
    dataPokemon = get_pokemon_data(request.args.get('pokemon'))
    file_list = get_ftp_file_list()
    return send_ftp(file_list, dataPokemon)

def create_Markdown(data):
    print(data)
    markdown_text = f"**Name:** {data['name']}\n"
    markdown_text += f"![Image]({data['front_default']})\n"
    markdown_text += f"**Types:** {', '.join(data['types'])}\n"
    return markdown_text

if __name__ == '__main__':
    app.run()
