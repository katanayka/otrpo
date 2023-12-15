import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.exceptions import RequestException
import sqlite3
from datetime import datetime, timedelta
import random

base_url = "http://localhost:5000"

def random_timestamp():
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2023, 1, 1)
    random_days = random.randint(0, (end_date - start_date).days)
    random_time = timedelta(seconds=random.randint(0, 86400))
    return start_date + timedelta(days=random_days, seconds=random_time.total_seconds())

def perform_battle(battle_number):
    conn = sqlite3.connect('battles.db')
    cursor = conn.cursor()

    try:
        response = requests.get(f"{base_url}/fight/fast")
        response.raise_for_status()
        battle_result = response.json()

        timestamp = random_timestamp().strftime('%Y-%m-%d %H:%M:%S')
        player_id = battle_result['player']['id']
        enemy_id = battle_result['enemy']['id']
        winner_id = battle_result['winner']['id']
        rounds = battle_result['rounds']
        user = "your_username"

        cursor.execute('''
            INSERT INTO battles (timestamp, player_id, enemy_id, winner_id, rounds, user)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, player_id, enemy_id, winner_id, rounds, user))
        conn.commit()
        print(f"Battle {battle_number}: Winner - {winner_id}")

    except RequestException as e:
        print(f"Error during battle {battle_number}: {e}")

    finally:
        conn.close()

num_battles = 10000
with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(perform_battle, i+1) for i in range(num_battles)]
    for future in as_completed(futures):
        try:
            future.result()
        except Exception as e:
            print(f"An exception occurred: {e}")
