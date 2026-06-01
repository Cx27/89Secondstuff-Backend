from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

import auth
import models
import schemas


def get_user_by_identifier(db: Session, identifier: str):
    return db.query(models.User).filter(
        or_(
            models.User.email == identifier,
            models.User.username == identifier
        )
    ).first()


def create_user(db: Session, user_data: schemas.UserCreate, role: str = "buyer"):
    hashed_password = auth.get_password_hash(user_data.password)

    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        role=role
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_products(db: Session):
    return db.query(models.Product).filter(models.Product.status == "available").all()


def create_product(db: Session, product: schemas.ProductCreate):
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def create_booking(db: Session, user_id: int, product_id: int):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.status == "available"
    ).first()

    if not product:
        return None

    product.status = "reserved"

    expires = datetime.now(timezone.utc) + timedelta(hours=2)

    db_booking = models.Booking(user_id=user_id, product_id=product_id, expires_at=expires)
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


def update_product_status_by_admin(db: Session, product_id: int, new_status: str):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        return None

    product.status = new_status

    if new_status == "available":
        db.query(models.Booking).filter(models.Booking.product_id == product_id).delete()

    db.commit()
    db.refresh(product)
    return product


def update_product_details(db: Session, product_id: int, product_data: schemas.ProductCreate):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not db_product:
        return None

    db_product.name = product_data.name
    db_product.description = product_data.description
    db_product.price = product_data.price
    db_product.image_url = product_data.image_url

    db.commit()
    db.refresh(db_product)
    return db_product


def get_all_products_for_admin(db: Session):
    return db.query(models.Product).order_by(models.Product.id.desc()).all()


def get_all_bookings_for_admin(db: Session):
    return db.query(models.Booking).order_by(models.Booking.id.desc()).all()


def get_user_bookings(db: Session, user_id: int):
    return db.query(models.Booking).filter(models.Booking.user_id == user_id).order_by(models.Booking.id.desc()).all()
