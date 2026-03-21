def test_register(client):
    res = client.post("/api/register", json={
        "username": "testuser",
        "password": "123456"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["code"] == 200

def test_login_success(client):
    client.post("/api/register", json={
        "username": "testuser",
        "password": "123456"
    })
    res = client.post("/api/login", json={
        "username": "testuser",
        "password": "123456"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data["data"]

def test_login_fail(client):
    res = client.post("/api/login", json={
        "username": "nouser",
        "password": "wrong"
    })
    assert res.status_code == 400