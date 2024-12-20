"""test_api"""
# pylint: disable=redefined-outer-name
import string
from datetime import datetime
from random import choices

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models import Event, Visitor, Registration

# Настройки для тестовой базы данных
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Определение функции get_db для тестов"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Переопределение зависимости get_db в приложении
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def db():
    """db"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(db): # pylint: disable=W0613
    """client"""
    with TestClient(app) as client:
        yield client


def create_test_event(db):
    """create_test_event"""
    event = Event(
        title="Test Event",
        description="Test Description",
        status="active",
        location="Test Location",
        start_at=datetime(2023, 1, 1, 0, 0, 0),
        end_at=datetime(2023, 1, 1, 1, 0, 0),
        price=100.0,
        visitor_limit=100,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def create_test_visitor(db):
    """create_test_visitor"""
    def generate_unique_phone():
        return "".join(choices(string.digits, k=10))

    def generate_unique_email():
        return f"test_{''.join(choices(string.ascii_lowercase, k=5))}@example.com"

    visitor = Visitor(
        first_name="John",
        last_name="Doe",
        phone=generate_unique_phone(),
        email=generate_unique_email(),
    )
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return visitor


def create_test_registration(db, event_id, visitor_id):
    """create_test_registration"""
    registration = Registration(
        event_id=event_id, visitor_id=visitor_id, price=100.0, status="unpaid"
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


def test_get_route(client):
    """get_route"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_events(client):
    """get_events"""
    response = client.get("/events/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_event(client, db):
    """read_event"""
    event = create_test_event(db)
    response = client.get(f"/events/{event.id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_event_not_found(client):
    """read_event_not_found"""
    response = client.get("/events/999999")
    assert response.status_code == 404


def test_create_event(client):
    """create_event"""
    response = client.post(
        "/events/create/",
        data={
            "title": "Test Event",
            "description": "Test Description",
            "status": "planning",
            "location": "Test Location",
            "start_at": "2023-01-01T00:00:00",
            "end_at": "2023-01-01T01:00:00",
            "price": 100.0,
            "visitor_limit": "",
        },
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_create_event_invalid_visitor_limit(client):
    """create_event"""
    response = client.post(
        "/events/create/",
        data={
            "title": "Test Event",
            "description": "Test Description",
            "status": "planning",
            "location": "Test Location",
            "start_at": "2023-01-01T00:00:00",
            "end_at": "2023-01-01T01:00:00",
            "price": 100.0,
            "visitor_limit": "invalid",
        },
    )
    assert response.status_code == 400


def test_update_event(client, db):
    """update_event"""
    event = create_test_event(db)
    response = client.put(
        f"/events/{event.id}/update/",
        json={
            "title": "Updated Event",
            "description": "Updated Description",
            "status": "planning",
            "location": "Updated Location",
            "start_at": "2023-01-01T00:00:00",
            "end_at": "2023-01-01T01:00:00",
            "price": 200.0,
            "visitor_limit": "200",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["event"]["title"] == "Updated Event"


def test_update_event_not_found(client):
    """update_event"""
    response = client.put(
        "/events/999999/update/",
        json={
            "title": "Updated Event",
            "description": "Updated Description",
            "status": "planning",
            "location": "Updated Location",
            "start_at": "2023-01-01T00:00:00",
            "end_at": "2023-01-01T01:00:00",
            "price": 200.0,
            "visitor_limit": "200",
        },
    )
    assert response.status_code == 404


def test_delete_event(client, db):
    """delete_event"""
    event = create_test_event(db)
    response = client.delete(f"/events/{event.id}/delete/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redirect_url"] == "/events/"


def test_delete_event_not_found(client):
    """delete_event"""
    response = client.delete("/events/999999/delete/")
    assert response.status_code == 404


def test_get_visitors(client):
    """get_visitors"""
    response = client.get("/visitors/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_visitor(client, db):
    """read_visitor"""
    visitor = create_test_visitor(db)
    response = client.get(f"/visitors/{visitor.id}")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_visitor_not_found(client):
    """read_visitor"""
    response = client.get("/visitors/999999")
    assert response.status_code == 404


def test_create_visitor(client):
    """create_visitor"""
    response = client.post(
        "/visitors/create/",
        data={
            "first_name": "John",
            "last_name": "Doe",
            "phone": "1234567892",
            "email": "john.doe2@example.com",
        },
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_update_visitor(client, db):
    """update_visitor"""
    visitor = create_test_visitor(db)
    response = client.put(
        f"/visitors/{visitor.id}/update/",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "0987654321",
            "email": "jane.doe@example.com",
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["visitor"]["first_name"] == "Jane"


def test_get_registrations(client):
    """get_registrations"""
    response = client.get("/registrations/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_create_registration(client, db):
    """create_registration"""
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    response = client.post(
        "/registrations/create/",
        data={"event_id": event.id, "visitor_id": visitor.id},
    )
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_create_registration_invalid_event_id(client, db):
    """create_registration"""
    visitor = create_test_visitor(db)
    response = client.post(
        "/registrations/create/",
        data={"event_id": 999999, "visitor_id": visitor.id},
    )
    assert response.status_code == 404


def test_create_registration_invalid_visitor_id(client, db):
    """create_registration"""
    event = create_test_event(db)
    response = client.post(
        "/registrations/create/", data={"event_id": event.id, "visitor_id": 999999}
    )
    assert response.status_code == 404


def test_create_registration_duplicate(client, db):
    """create_registration"""
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    response = client.post(
        "/registrations/create/",
        data={"event_id": event.id, "visitor_id": visitor.id},
    )
    assert response.status_code == 200
    response = client.post(
        "/registrations/create/",
        data={"event_id": event.id, "visitor_id": visitor.id},
    )
    assert response.status_code == 400


def test_update_registration(client, db):
    """update_registration"""
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    registration = create_test_registration(db, event.id, visitor.id)
    response = client.put(
        f"/registrations/{registration.id}/update/",
        json={"billed_amount": "100", "refund_amount": "0"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["registration"]["status"] == "paid"


def test_update_registration_not_found(client):
    """update_registration"""
    response = client.put(
        "/registrations/999999/update/",
        json={"billed_amount": "100", "refund_amount": "0"},
    )
    assert response.status_code == 404


def test_delete_registration(client, db):
    """delete_registration"""
    event = create_test_event(db)
    visitor = create_test_visitor(db)
    registration = create_test_registration(db, event.id, visitor.id)
    response = client.delete(f"/registrations/{registration.id}/delete/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["redirect_url"] == "/registrations/"


def test_delete_registration_not_found(client):
    """delete_registration"""
    response = client.delete("/registrations/999999/delete/")
    assert response.status_code == 404
