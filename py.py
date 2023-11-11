import datetime
import json
import requests
from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import sqlite3
import random
import os
import smtplib
import smtplib
import ssl
from email.message import EmailMessage
from ftplib import FTP
from io import BytesIO
from dotenv import load_dotenv
import redis

app = Flask(__name__)
CACHE_TIMEOUT = 600
PER_PAGE = 20
load_dotenv()
TOKEN = os.getenv("TOKEN")
DOMAIN = os.getenv("DOMAIN")


redis_client = redis.from_url(os.getenv("redis"))

@app.route("/", methods=['GET', 'POST'])
def main():
    page = int(request.args.get('page', 1)) 
    url_count = 'https://pokeapi.co/api/v2/pokemon'
    count = get_data(url_count)["count"]
    total_pages = count // PER_PAGE + (count % PER_PAGE > 0)
    search = request.args.get('search', '')
    pokemon_data = []
    pokemon_data = get_pokemon_page(page, PER_PAGE)

    return render_template("index.html", data=pokemon_data, page=page, total_pages=total_pages, per_page=PER_PAGE, search=search)

def get_pokemon_data(item):
    if type(item) is str or type(item) is int:
        pokemon_url = f'https://pokeapi.co/api/v2/pokemon/{item}/'
    else: 
        pokemon_url = item["url"]

    cached_data = redis_client.get(f'pokemon_{item}')
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

    redis_client.set(f'pokemon_{item}', json.dumps(pokemon_data))

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
    timestamp = datetime.datetime.now()
    
    conn = sqlite3.connect('battles.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO battles (timestamp, player_id, enemy_id, winner_id, rounds) VALUES (?, ?, ?, ?, ?)',
                   (timestamp, player_id, enemy_id, winner_id, rounds))
    
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
