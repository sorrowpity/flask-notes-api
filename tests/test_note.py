def test_add_note(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    res = client.post("/api/notes", json={
        "title": "test title",
        "content": "test content"
    }, headers=headers)
    assert res.status_code == 201

def test_get_notes(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    client.post("/api/notes", json={"title":"t","content":"c"}, headers=headers)
    res = client.get("/api/notes", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    assert len(data["data"]) > 0