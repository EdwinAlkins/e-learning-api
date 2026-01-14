import pytest

from fastapi.testclient import TestClient

from src.api.fastapi_app import app


@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "name": "test",
    }

@pytest.fixture
def client():
    return TestClient(app)


def test_create_user(client, sample_user_data):
    response_create = client.post("/user/", json=sample_user_data)
    assert response_create.status_code == 200
    response_create_json = response_create.json()

    response_get = client.get("/user/")
    assert response_get.status_code == 200
    
    response_get_by_id = client.get(f"/user/{response_create_json['uid']}")
    assert response_get_by_id.status_code == 200
    assert response_get_by_id.json() == response_create_json
    
    response_update = client.put(f"/user/{response_create_json['uid']}", json=sample_user_data)
    assert response_update.status_code == 200
    
    response_delete = client.delete(f"/user/{response_create_json['uid']}")
    assert response_delete.status_code == 200
    
    response_get_after_delete = client.get(f"/user/{response_create_json['uid']}")
    assert response_get_after_delete.status_code == 404
