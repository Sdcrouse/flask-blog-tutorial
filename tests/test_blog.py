import pytest
from flaskr.db import get_db

def test_index_logged_in(client, auth):
    auth.login()
    response_data = client.get('/').data
    assert b"Log In" not in response_data
    assert b"Register" not in response_data
    assert b'Log Out' in response_data
    assert b'href="/create"' in response_data
    assert b'test title' in response_data
    assert b'by test on 2018-01-01' in response_data
    assert b'test\nbody' in response_data
    assert b'href="/1/update"' in response_data

def test_index_logged_out(client):
    response_data = client.get('/').data
    assert b"Log In" in response_data
    assert b"Register" in response_data
    assert b'href="/create"' not in response_data
    assert b'href="/1/update"' not in response_data
    assert b'Log Out' not in response_data

@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
    '/1/delete',
))
def test_login_required(client, path):
    response = client.post(path)
    assert response.headers["Location"] == "/auth/login"

def test_author_required(app, client, auth):
    # Change the post author to another user
    with app.app_context():
        db = get_db()
        db.execute('UPDATE post SET author_id = 2 WHERE id = 1')
        db.commit()

    auth.login()
    
    # Current user can't modify or delete another user's post
    assert client.post('/1/update').status_code == 403
    assert client.post('/1/delete').status_code == 403
    
    # Current user doesn't see the edit link
    assert b'href="/1/update"' not in client.get('/').data

@pytest.mark.parametrize('path', (
    '/2/update',
    '/2/delete',
))
def test_blog_exists_required(client, auth, path):
    auth.login()
    assert client.post(path).status_code == 404

def test_create(client, auth, app):
    auth.login()
    assert client.get('/create').status_code == 200
    
    response = client.post('/create', data={'title': 'created', 'body': ''})
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        count = db.execute('SELECT COUNT(id) FROM post').fetchone()[0]
        assert count == 2

def test_update(client, auth, app):
    auth.login()
    response = client.get('/1/update')
    assert response.status_code == 200
    assert b'test title' in response.data
    assert b'test\nbody' in response.data
    
    response = client.post('/1/update', data ={'title': 'updated', 'body': ''})
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post WHERE id = 1').fetchone()
        assert post['title'] == 'updated'

@pytest.mark.parametrize('path', (
    '/create',
    '/1/update',
))
def test_create_update_validate(client, auth, path):
    auth.login()
    response = client.post(path, data={'title': '', 'body': ''})
    assert b'Title is required.' in response.data

def test_delete(client, auth, app):
    auth.login()
    response = client.post('/1/delete')
    assert response.headers["Location"] == "/"

    with app.app_context():
        db = get_db()
        post = db.execute('SELECT * FROM post where id = 1').fetchone()
        assert post is None