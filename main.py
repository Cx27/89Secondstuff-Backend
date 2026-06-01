import os
import shutil

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import engine, get_db
import auth
import crud
import models
import schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="89Secondstuff API")

app.mount("/static", StaticFiles(directory="uploads"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ga valid atau udah expired dawg!",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_identifier(db, identifier=email)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    cek_email = crud.get_user_by_identifier(db, identifier=user.email)
    cek_username = crud.get_user_by_identifier(db, identifier=user.username)

    if cek_email or cek_username:
        raise HTTPException(status_code=400, detail="Email atau Username udah kedaftar dawg!")

    return crud.create_user(db=db, user_data=user)


@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_identifier(db, identifier=form_data.username)

    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email/Username atau password salah bang")

    access_token = auth.create_access_token(data={"sub": user.email, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/admin/upload-image")
def upload_image(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak! Lu bukan admin dawg.")

    allowed_extensions = ["image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Format file ga valid! Cuma boleh JPG/PNG.")

    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return {"url": f"http://127.0.0.1:8000/static/{file.filename}"}


@app.get("/products", response_model=list[schemas.ProductResponse])
def read_products(db: Session = Depends(get_db)):
    return crud.get_products(db)


@app.get("/admin/products", response_model=list[schemas.ProductResponse])
def admin_read_all_products(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak! Lu bukan admin dawg.")
    return crud.get_all_products_for_admin(db)


@app.post("/products", response_model=schemas.ProductResponse)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak! Lu bukan admin dawg.")
    return crud.create_product(db=db, product=product)


@app.put("/admin/products/{product_id}", response_model=schemas.ProductResponse)
def admin_edit_product(product_id: int, product_data: schemas.ProductCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak! Lu bukan admin dawg.")
    updated_product = crud.update_product_details(db=db, product_id=product_id, product_data=product_data)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Barangnya ga ketemu bang.")
    return updated_product


@app.patch("/admin/products/{product_id}/status", response_model=schemas.ProductResponse)
def admin_update_product_status(product_id: int, new_status: str, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Lu bukan admin dawg! Gak usah modif data.")
    if new_status not in ["sold", "reserved", "available"]:
        raise HTTPException(status_code=400, detail="Status cuma boleh 'sold', 'reserved', atau 'available' bang!")

    updated_product = crud.update_product_status_by_admin(db=db, product_id=product_id, new_status=new_status)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Barangnya gak ketemu dawg.")
    return updated_product


@app.get("/admin/bookings", response_model=list[schemas.BookingResponse])
def admin_read_all_bookings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak! Lu bukan admin dawg.")
    return crud.get_all_bookings_for_admin(db)


@app.get("/bookings", response_model=list[schemas.BookingResponse])
def read_my_bookings(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_user_bookings(db=db, user_id=current_user.id)


@app.post("/bookings", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_booking = crud.create_booking(db=db, user_id=current_user.id, product_id=booking.product_id)
    if not db_booking:
        raise HTTPException(status_code=400, detail="Barang ini udah ga available atau ga ketemu!")
    return db_booking
