"""utils"""
from datetime import datetime
from typing import Type
from urllib.parse import urlencode

from fastapi import Query

from app.database import Base


def build_url_with_query(base_url, **kwargs):
    """build_url_with_query"""
    query_string = urlencode(kwargs)
    return f"{base_url}?{query_string}"


def order_query(
    model: Type[Base], query: Query, sort_by: str, sort_order: int
) -> Query:
    """order_query"""
    if sort_by and hasattr(model, sort_by):
        if sort_order:
            query = query.order_by(getattr(model, sort_by).desc())
        else:
            query = query.order_by(getattr(model, sort_by))
    return query


def format_price(value):
    """format_price"""
    return f"{value if value else 0:.2f} ₽"


def format_datetime_ru(value):
    """format_datetime_ru"""
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y %H:%M:%S")
    return value
