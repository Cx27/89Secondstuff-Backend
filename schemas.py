from pydantic import BaseModel


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    status: str

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    product_id: int


class BookingResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    status: str

    class Config:
        from_attributes = True
