import json
import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    with app.test_client() as client:
        yield client

def test_get_pokemon_by_id(client):
    response = client.get('/pokemon/1')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert 'id' in data
    assert 'name' in data

def test_fast_battle(client):
    response = client.get('/fight/fast')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert 'player' in data
    assert 'enemy' in data
    assert 'winner' in data
    assert 'rounds' in data

def test_get_pokemon_list(client):
    response = client.get('/pokemon/list?characteristic=hp')
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert isinstance(data, list)

def test_add_review(client):
    payload = {
        'pokemon_id': 1,
        'username': 'test_user',
        'review_text': 'This is a test review.',
        'rating': 5
    }
    response = client.post('/add_review', json=payload)
    data = json.loads(response.get_data(as_text=True))
    assert response.status_code == 200
    assert 'message' in data
    assert data['message'] == 'Отзыв успешно добавлен.'