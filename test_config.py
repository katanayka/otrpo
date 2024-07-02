import os

class TestConfig:
    REDIS_URL = "redis://default:4daae7b3c7964f57b75b7667edade996@us1-game-falcon-37220.upstash.io:37220"

# test_app.py
import os
from app import app

app.config.from_object('test_config.TestConfig')