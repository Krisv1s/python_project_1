"""routes"""
#pylint: disable=R0913,R0917
from datetime import datetime
from typing import Optional

from fastapi import Depends, Request, HTTPException, Query, Form, APIRouter
from fastapi.responses import HTMLResponse
from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from starlette.templating import Jinja2Templates

from . import models, schemas
from .database import get_db
from .schemas import (
    EventBase,
    VisitorBase,
    RegistrationBase,
    DeleteResponse,
    VisitorUpdateResponse,
    EventUpdateResponse,
    RegistrationUpdateResponse,
)
from .utils import order_query, build_url_with_query, format_price, format_datetime_ru

api = APIRouter(
    tags=["API"],
)

templates = Jinja2Templates(directory="templates")
templates.env.filters["format_price"] = format_price
templates.env.filters["format_datetime_ru"] = format_datetime_ru


@api.get("/", response_class=HTMLResponse)
def get_route(request: Request):
    """get_route"""
    return templates.TemplateResponse(request, "index.html")


@api.get("/events/", response_class=HTMLResponse)
def get_events(
    request: Request,
    db: Session = Depends(get_db),
    visitor_id=Query(None),
    sort_by: str = Query(None),
    sort_order: int = Query(None),
    search: str = Query(None),
    status: str = Query(None),
):
    """get_events"""
    if not (visitor_id == "" or visitor_id is None or visitor_id.isdigit()):
        raise HTTPException(status_code=400, detail="Invalid visitor id")
    query = db.query(models.Event)
    if visitor_id:
        query = query.filter(models.Registration.visitor_id == visitor_id)
    if search:
        query = query.filter(
            models.Event.title.ilike(f"%{search}%")
            | models.Event.description.ilike(f"%{search}%")
            | models.Event.location.ilike(f"%{search}%")
        )
    if status:
        query = query.filter(models.Event.status == status)
    query = order_query(models.Event, query, sort_by, sort_order)
    events = query.all()
    return templates.TemplateResponse(
        request,
        "event/index.html",
        {
            "request": request,
            "events": events,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "search": search,
            "statuses": schemas.EVENT_STATUSES,
            "status": status,
        },
    )


@api.get("/events/{event_id}", response_model=schemas.Event)
def read_event(event_id: int, request: Request, db: Session = Depends(get_db)):
    """read_event"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    visitors = (
        db.query(models.Visitor)
        .join(models.Registration)
        .filter(models.Registration.event_id == event_id)
        .all()
    )
    total_income = (
        db.query(
            func.sum(
                func.coalesce(models.Registration.billed_amount, 0)
                - func.coalesce(models.Registration.refund_amount, 0)
            )
        )
        .filter(models.Registration.event_id == event_id)
        .scalar()
        or 0
    )
    expected_income = (
        db.query(func.sum(func.coalesce(models.Registration.price, 0)))
        .filter(models.Registration.event_id == event_id)
        .scalar()
        or 0
    )
    return templates.TemplateResponse(
        request,
        "event/view.html",
        {
            "request": request,
            "event": db_event,
            "visitors": visitors,
            "total_income": total_income,
            "expected_income": expected_income,
            "build_url_with_query": build_url_with_query,
        },
    )


@api.get(
    "/events/create/",
    response_class=HTMLResponse,
    description="Страница создания события",
)
def create_event_form(request: Request):
    """create_event_form"""
    return templates.TemplateResponse(
        request,
        "event/create.html",
        {
            "request": request,
            "statuses": schemas.EVENT_STATUSES,
        },
    )


@api.get("/events/{event_id}/update/", response_class=HTMLResponse)
def update_event_form(event_id: int, request: Request, db: Session = Depends(get_db)):
    """update_event_form"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return templates.TemplateResponse(
        request,
        "event/update.html",
        {
            "request": request,
            "event": db_event,
            "statuses": schemas.EVENT_STATUSES,
        },
    )


@api.post(
    "/events/create/", response_model=EventBase, description="Создать новое событие"
)
def create_event(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    status: str = Form("planning"),
    location: str = Form(...),
    start_at: datetime = Form(...),
    end_at: datetime = Form(...),
    price: float = Form(...),
    visitor_limit: str = Form(None),
    db: Session = Depends(get_db),
):
    """create_event"""
    if not (visitor_limit == "" or visitor_limit is None or visitor_limit.isdigit()):
        raise HTTPException(status_code=400, detail="Invalid visitor limit")
    if visitor_limit == "":
        visitor_limit = None
    event_data = schemas.EventCreate(
        title=title,
        description=description,
        status=status,
        location=location,
        start_at=start_at,
        end_at=end_at,
        price=price,
        visitor_limit=visitor_limit,
    )
    db_event = models.Event(**event_data.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return RedirectResponse(url=f"/events/{db_event.id}", status_code=303)


@api.put(
    "/events/{event_id}/update/",
    response_model=EventUpdateResponse,
    description="Обновить мероприятие",
)
def update_event(
    event_id: int, event: schemas.EventUpdate, db: Session = Depends(get_db)
):
    """update_event"""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    for key, value in event.model_dump().items():
        setattr(db_event, key, value)

    db.commit()
    db.refresh(db_event)
    return {
        "status": "ok",
        "redirect_url": f"/events/{db_event.id}",
        "event": db_event,
    }


@api.delete("/events/{event_id}/delete/", response_model=DeleteResponse)
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """delete_event"""
    event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(event)
    db.commit()

    return {"status": "ok", "redirect_url": "/events/"}


@api.get("/visitors/", response_class=HTMLResponse)
def get_visitors(
    request: Request,
    db: Session = Depends(get_db),
    event_id: int = Query(None),
    sort_by: str = Query(None),
    sort_order: int = Query(None),
    search: str = Query(None),
):
    """get_visitors"""
    query = db.query(models.Visitor)
    if event_id:
        query = query.filter(models.Registration.event_id == event_id)
    if search:
        query = query.filter(
            models.Visitor.first_name.ilike(f"%{search}%")
            | models.Visitor.last_name.ilike(f"%{search}%")
            | models.Visitor.email.ilike(f"%{search}%")
        )
    query = order_query(models.Visitor, query, sort_by, sort_order)
    visitors = query.all()
    return templates.TemplateResponse(
        request,
        "visitor/index.html",
        {
            "request": request,
            "visitors": visitors,
            "sort_by": sort_by,
            "sort_order": sort_order,
        },
    )


@api.get("/visitors/{visitor_id}", response_model=schemas.Visitor)
def read_visitor(visitor_id: int, request: Request, db: Session = Depends(get_db)):
    """read_visitor"""
    db_visitor = (
        db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    )
    if db_visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    events = (
        db.query(models.Event)
        .join(models.Registration)
        .filter(models.Registration.visitor_id == visitor_id)
        .all()
    )
    return templates.TemplateResponse(
        request,
        "visitor/view.html",
        {
            "request": request,
            "visitor": db_visitor,
            "events": events,
            "build_url_with_query": build_url_with_query,
        },
    )


@api.get(
    "/visitors/create/",
    response_class=HTMLResponse,
    description="Страница создания посетителя",
)
def create_visitor_form(request: Request):
    """create_visitor_form"""
    return templates.TemplateResponse(
        request,
        "visitor/create.html",
        {
            "request": request,
        },
    )


@api.get("/visitors/{visitor_id}/update/", response_class=HTMLResponse)
def update_visitor_form(
    visitor_id: int, request: Request, db: Session = Depends(get_db)
):
    """update_visitor_form"""
    db_visitor = (
        db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    )
    if db_visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return templates.TemplateResponse(
        request,
        "visitor/update.html",
        {
            "request": request,
            "visitor": db_visitor,
        },
    )


@api.post(
    "/visitors/create/",
    response_model=VisitorBase,
    description="Создать нового посетителя",
)
def create_visitor(
    first_name: str = Form(...),
    last_name: str = Form(...),
    phone: str = Form(...),
    email: Optional[EmailStr] = Form(None),
    db: Session = Depends(get_db),
):
    """create_visitor"""
    visitor_data = schemas.VisitorCreate(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        email=email,
    )
    db_visitor = models.Visitor(**visitor_data.model_dump())
    db.add(db_visitor)
    db.commit()
    db.refresh(db_visitor)
    return RedirectResponse(url=f"/visitors/{db_visitor.id}", status_code=303)


@api.put(
    "/visitors/{visitor_id}/update/",
    response_model=VisitorUpdateResponse,
    description="Обновить посетителя",
)
def update_visitor(
    visitor_id: int, visitor: schemas.VisitorUpdate, db: Session = Depends(get_db)
):
    """update_visitor"""
    db_visitor = (
        db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    )
    if db_visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")

    for key, value in visitor.model_dump().items():
        setattr(db_visitor, key, value)

    db.commit()
    db.refresh(db_visitor)
    return {
        "status": "ok",
        "redirect_url": f"/visitors/{db_visitor.id}",
        "visitor": db_visitor,
    }


@api.delete("/visitors/{visitor_id}/delete/", response_model=DeleteResponse)
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)):
    """delete_visitor"""
    visitor = db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")

    db.delete(visitor)
    db.commit()
    return {"status": "ok", "redirect_url": "/visitors/"}


@api.get("/registrations/", response_class=HTMLResponse)
def get_registrations(
    request: Request,
    db: Session = Depends(get_db),
    event_id=Query(None),
    visitor_id=Query(None),
    sort_by: str = Query(None),
    sort_order: int = Query(None),
    status: str = Query(None),
):
    """get_registrations"""
    if not (event_id == "" or event_id is None or event_id.isdigit()):
        raise HTTPException(status_code=400, detail="Invalid event id")
    if not (visitor_id == "" or visitor_id is None or visitor_id.isdigit()):
        raise HTTPException(status_code=400, detail="Invalid visitor id")
    query = db.query(models.Registration)
    events = {}
    visitors = {}
    for registration in query.all():
        events.setdefault(registration.event_id, registration.event.title)
        visitors.setdefault(
            registration.visitor_id,
            f"{registration.visitor.first_name} {registration.visitor.last_name}",
        )
    if event_id:
        query = query.filter(models.Registration.event_id == event_id)
    if visitor_id:
        query = query.filter(models.Registration.visitor_id == visitor_id)
    if status:
        query = query.filter(models.Event.status == status)
    query = order_query(models.Registration, query, sort_by, sort_order)
    registrations = query.all()
    return templates.TemplateResponse(
        request,
        "registration/index.html",
        {
            "request": request,
            "registrations": registrations,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "statuses": schemas.REGISTRATION_STATUSES,
            "status": status,
            "event_id": event_id,
            "events": events,
            "visitors": visitors,
            "visitor_id": visitor_id,
        },
    )


@api.get(
    "/registrations/create/",
    response_class=HTMLResponse,
    description="Регистрация посетителя",
)
def create_registration_form(request: Request, db: Session = Depends(get_db)):
    """create_registration_form"""
    events = (
        db.query(models.Event)
        .filter(models.Event.status.notin_(["cancelled", "completed", "ready"]))
        .all()
    )
    visitors = db.query(models.Visitor).all()
    return templates.TemplateResponse(
        request,
        "registration/create.html",
        {
            "request": request,
            "events": events,
            "visitors": visitors,
        },
    )


@api.get("/registrations/{registration_id}/update/", response_class=HTMLResponse)
def update_registration_form(
    registration_id: int, request: Request, db: Session = Depends(get_db)
):
    """update_registration_form"""
    db_registration = (
        db.query(models.Registration)
        .filter(models.Registration.id == registration_id)
        .first()
    )
    if db_registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")
    return templates.TemplateResponse(
        request,
        "registration/update.html",
        {
            "request": request,
            "registration": db_registration,
            "events": [db_registration.event],
            "visitors": [db_registration.visitor],
        },
    )


@api.post(
    "/registrations/create/",
    response_model=RegistrationBase,
    description="Регистрация посетителя",
)
def create_registration(
    event_id: int = Form(...),
    visitor_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """create_registration"""
    db_visitor = (
        db.query(models.Visitor).filter(models.Visitor.id == visitor_id).first()
    )
    if db_visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    registration = (
        db.query(models.Registration)
        .filter(
            models.Registration.event_id == event_id,
            models.Registration.visitor_id == visitor_id,
        )
        .first()
    )
    if registration is not None:
        raise HTTPException(
            status_code=400, detail="Registration with this params already exists"
        )
    price = db_event.price
    status = "unpaid"
    if not price:
        status = "paid"
    registration_data = schemas.RegistrationCreate(
        visitor_id=visitor_id,
        event_id=event_id,
        price=db_event.price,
        status=status,
    )
    db_registration = models.Registration(**registration_data.model_dump())
    db.add(db_registration)
    db.commit()
    db.refresh(db_registration)
    return RedirectResponse(url="/registrations/", status_code=303)


@api.put(
    "/registrations/{registration_id}/update/",
    response_model=RegistrationUpdateResponse,
    description="Обновить регистрацию",
)
def update_registration(
    registration_id: int,
    registration: schemas.RegistrationUpdate,
    db: Session = Depends(get_db),
):
    """update_registration"""
    db_registration = (
        db.query(models.Registration)
        .filter(models.Registration.id == registration_id)
        .first()
    )
    if db_registration is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    billed_amount = registration.billed_amount
    refund_amount = registration.refund_amount
    price = db_registration.price
    if (
        billed_amount != ""
        and billed_amount is not None
        and not billed_amount.isdigit()
    ):
        raise HTTPException(status_code=400, detail="Invalid billed amount")
    billed_amount = int(billed_amount) if billed_amount else None
    if (
        refund_amount != ""
        and refund_amount is not None
        and not refund_amount.isdigit()
    ):
        raise HTTPException(status_code=400, detail="Invalid refund amount")
    refund_amount = int(refund_amount) if refund_amount else None

    if billed_amount is not None and billed_amount > 0 and billed_amount == price:
        registration.status = "paid"
        registration.billed_amount = billed_amount
        registration.billed_at = datetime.now()
    if refund_amount is not None and refund_amount > 0:
        registration.status = "refunded"
        registration.refund_amount = refund_amount
        registration.refunded_at = datetime.now()
    for key, value in registration.model_dump().items():
        setattr(db_registration, key, value)
    db.commit()
    db.refresh(db_registration)
    return {
        "status": "ok",
        "redirect_url": "/registrations/",
        "registration": db_registration,
    }


@api.delete("/registrations/{registration_id}/delete/", response_model=DeleteResponse)
def delete_registration(registration_id: int, db: Session = Depends(get_db)):
    """delete_registration"""
    registration = (
        db.query(models.Registration)
        .filter(models.Registration.id == registration_id)
        .first()
    )
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    db.delete(registration)
    db.commit()
    return {"status": "ok", "redirect_url": "/registrations/"}
