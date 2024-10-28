import string
from random import choices

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models import Event, Visitor, Registration

# Настройки для тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Определение функции get_db для тестов
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Переопределение зависимости get_db в приложении
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    with TestClient(app) as client:
        yield client

def create_test_event(db):
    event = Event(
        title="Test Event",
        description="Test Description",
        status="active",
        location="Test Location",
        start_at=datetime(2023, 1, 1, 0, 0, 0),
        end_at=datetime(2023, 1, 1, 1, 0, 0),
        price=100.0,
        visitor_limit=100
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

def create_test_visitor(db):
    def generate_unique_phone():
        return ''.join(choices(string.digits, k=10))

    def generate_unique_email():
        return f"test_{''.join(choices(string.ascii_lowercase, k=5))}@example.com"

    visitor = Visitor(
        first_name="John",
        last_name="Doe",
        phone=generate_unique_phone(),
        email=generate_unique_email()
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return visitor

def create_test_registration(db, event_id, visitor_id):
    registration = Registration(
        event_id=event_id,
        visitor_id=visitor_id,
        price=100.0,
        status="unpaid"
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration

def test_get_route(client):
    response = client.get("/api/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_get_events(client):
    response = client.get("/api/events/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_event(client, db):
    event = create_test_event(db)
    response = client.get(f"/api/events/{event.id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_event_not_found(client):
    response = client.get("/api/events/999999")
    assert response.status_code == 404

def test_create_event(client, db):
    response = client.post("/api/events/create/", data={
        "title": "Test Event",
        "description": "Test Description",
        "status": "planning",
        "location": "Test Location",
        "start_at": "2023-01-01T00:00:00",
        "end_at": "2023-01-01T01:00:00",
        "price": 100.0,
        "visitor_limit": ""
    })
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_create_event_invalid_visitor_limit(client):
    response = client.post("/api/events/create/", data={
        "title": "Test Event",
        "description": "Test Description",
        "status": "planning",
        "location": "Test Location",
        "start_at": "2023-01-01T00:00:00",
        "end_at": "2023-01-01T01:00:00",
        "price": 100.0,
        "visitor_limit": "invalid"
    })
    assert response.status_code == 400

def test_update_event(client, db):
    event = create_test_event(db)
    response = client.put(f"/api/events/{event.id}/update/", json={
        "title": "Updated Event",
        "description": "Updated Description",
        "status": "planning",
        "location": "Updated Location",
        "start_at": "2023-01-01T00:00:00",
        "end_at": "2023-01-01T01:00:00",
        "price": 200.0,
        "visitor_limit": "200"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["event"]["title"] == "Updated Event"

def test_update_event_not_found(client):
    response = client.put("/api/events/999999/update/", json={
        "title": "Updated Event",
        "description": "Updated Description",
        "status": "planning",
        "location": "Updated Location",
        "start_at": "2023-01-01T00:00:00",
        "end_at": "2023-01-01T01:00:00",
        "price": 200.0,
        "visitor_limit": "200"
    })
    assert response.status_code == 404

def test_delete_event(client, db):
    event = create_test_event(db)
    response = client.delete(f"/api/events/{event.id}/delete/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redirect_url"] == "/api/events/"

def test_delete_event_not_found(client):
    response = client.delete("/api/events/999999/delete/")
    assert response.status_code == 404

def test_get_visitors(client):
    response = client.get("/api/visitors/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_visitor(client, db):
    visitor = create_test_visitor(db)
    response = client.get(f"/api/visitors/{visitor.id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_read_visitor_not_found(client):
    response = client.get("/api/visitors/999999")
    assert response.status_code == 404

def test_create_visitor(client, db):
    response = client.post("/api/visitors/create/", data={
        "first_name": "John",
        "last_name": "Doe",
        "phone": "1234567892",
        "email": "john.doe2@example.com"
    })
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_update_visitor(client, db):
    visitor = create_test_visitor(db)
    response = client.put(f"/api/visitors/{visitor.id}/update/", json={
        "first_name": "Jane",
        "last_name": "Doe",
        "phone": "0987654321",
        "email": "jane.doe@example.com"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["visitor"]["first_name"] == "Jane"

def test_get_registrations(client):
    response = client.get("/api/registrations/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_create_registration(client, db):
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    response = client.post("/api/registrations/create/", data={
        "event_id": event.id,
        "visitor_id": visitor.id
    })
    assert response.status_code == 303
    assert response.headers["location"].startswith("/api/registrations/")

def test_create_registration_invalid_event_id(client, db):
    visitor = create_test_visitor(db)
    response = client.post("/api/registrations/create/", data={
        "event_id": 999999,
        "visitor_id": visitor.id
    })
    assert response.status_code == 404

def test_create_registration_invalid_visitor_id(client, db):
    event = create_test_event(db)
    response = client.post("/api/registrations/create/", data={
        "event_id": event.id,
        "visitor_id": 999999
    })
    assert response.status_code == 404

def test_create_registration_duplicate(client, db):
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    response = client.post("/api/registrations/create/", data={
        "event_id": event.id,
        "visitor_id": visitor.id
    })
    assert response.status_code == 303
    response = client.post("/api/registrations/create/", data={
        "event_id": event.id,
        "visitor_id": visitor.id
    })
    assert response.status_code == 400

def test_update_registration(client, db):
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    registration = create_test_registration(db, event.id, visitor.id)
    response = client.put(f"/api/registrations/{registration.id}/update/", json={
        "billed_amount": "100",
        "refund_amount": "0"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["registration"]["status"] == "paid"

def test_update_registration_not_found(client):
    response = client.put("/api/registrations/999999/update/", json={
        "billed_amount": "100",
        "refund_amount": "0"
    })
    assert response.status_code == 404

def test_delete_registration(client, db):
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    registration = create_test_registration(db, event.id, visitor.id)
    response = client.delete(f"/api/registrations/{registration.id}/delete/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redirect_url"] == "/api/registrations/"

def test_delete_registration_not_found(client):
    response = client.delete("/api/registrations/999999/delete/")
    assert response.status_code == 404