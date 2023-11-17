import pytest
from app import app

BASE_URL = 'http://localhost:5000'  # Update the URL based on your app's actual URL

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_main_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_pokemon_page(client):
    response = client.get('/pokemon/1')
    assert response.status_code == 200

def test_battle_page(client):
    response = client.get('/fight')
    assert response.status_code == 200

def test_random_pokemon_page(client):
    response = client.get('/random')
    assert response.status_code == 200

def test_pokemon_list_page(client):
    response = client.get('/pokemon/list?characteristic=hp')
    assert response.status_code == 200

def test_search_page(client):
    response = client.get('/search?text=charizard')
    assert response.status_code == 200

def test_get_ftp_files(client):
    response = client.get('/api/getFtpFiles')
    assert response.status_code == 200

def test_send_ftp_file(client):
    response = client.get('/api/sendFtpFile?pokemon=charizard')
    assert response.status_code == 200

