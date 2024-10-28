"""schemas"""
#pylint: disable=R0903, E0213
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

EVENT_STATUSES = ["planning", "ready", "active", "completed", "cancelled"]


class BaseSchema(BaseModel):
    """base schema"""
    id: int
    created_at: datetime
    updated_at: datetime

    class ConfigDict:
        """config dict"""
        from_attributes = True


class EventBase(BaseModel):
    """event base schema"""
    title: str = Field(..., description="Название события")
    status: str = Field(..., description="Статус события")
    description: Optional[str] = Field(None, description="Описание события")
    start_at: datetime = Field(..., description="Дата и время начала события")
    location: str = Field(..., description="Место проведения события")
    end_at: datetime = Field(..., description="Дата и время окончания события")
    price: int = Field(..., description="Цена события")
    visitor_limit: Optional[int] = Field(None, description="Лимит посетителей")

    @field_validator("price")
    def price_non_negative(cls, v):
        """validate price"""
        if v < 0:
            raise ValueError("price must be non-negative")
        return v

    @field_validator("visitor_limit")
    def visitor_limit_non_negative(cls, v):
        """validate visitor limit"""
        if v is not None and v < 0:
            raise ValueError("visitor_limit must be non-negative")
        return v


class EventCreate(EventBase):
    """event create schema"""

class EventUpdate(EventBase):
    """event update schema"""

class Event(EventBase, BaseSchema):
    """event schema"""

class VisitorBase(BaseModel):
    """visitor base schema"""
    first_name: str = Field(..., description="Имя")
    last_name: str = Field(..., description="Фамилия")
    phone: str = Field(..., description="Телефон")
    email: EmailStr = Field(None, description="Почта")


class VisitorUpdate(VisitorBase):
    """visitor update schema"""

class VisitorCreate(VisitorBase):
    """visitor create schema"""

class Visitor(VisitorBase, BaseSchema):
    """visitor schema"""

REGISTRATION_STATUSES = ["unpaid", "paid", "refunded", "cancelled", "completed"]


class RegistrationBase(BaseModel):
    """registration base schema"""
    visitor_id: int = Field(..., description="ID посетителя")
    event_id: int = Field(..., description="ID мероприятия")
    status: str = Field("unpaid", description="Статус регистрации")
    price: Optional[int] = Field(None, description="Цена")
    billed_amount: Optional[int] = Field(None, description="Оплаченная сумма")
    refund_amount: Optional[int] = Field(None, description="Сумма возврата")
    billed_at: Optional[datetime] = Field(None, description="Оплата в")
    refunded_at: Optional[datetime] = Field(None, description="Возврат в")


class RegistrationUpdate(BaseModel):
    """registration update schema"""
    status: str = Field("unpaid", description="Статус регистрации")
    billed_amount: Optional[str] = Field(None, description="Оплаченная сумма")
    refund_amount: Optional[str] = Field(None, description="Сумма возврата")
    billed_at: Optional[datetime] = Field(None, description="Оплата в")
    refunded_at: Optional[datetime] = Field(None, description="Возврат в")


class RegistrationCreate(RegistrationBase):
    """registration create schema"""

class Registration(RegistrationBase, BaseSchema):
    """registration schema"""

class BaseResponse(BaseModel):
    """base response schema"""
    status: str
    redirect_url: str


class DeleteResponse(BaseResponse):
    """delete response schema"""

class UpdateResponse(BaseResponse):
    """update response schema"""

class EventUpdateResponse(UpdateResponse):
    """event update response schema"""
    event: Event


class VisitorUpdateResponse(UpdateResponse):
    """visitor update response schema"""
    visitor: Visitor


class RegistrationUpdateResponse(UpdateResponse):
    """registration update response schema"""
    registration: Registration
