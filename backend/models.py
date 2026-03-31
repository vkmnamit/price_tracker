from pydantic import BaseModel, EmailStr
from typing import List, Optional

class User(BaseModel):
    id: Optional[str] = None  # Mongo ObjectId as string
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    wishlist: List[str] = []  # list of product IDs
    cart: List[dict] = []  # list of {product_id: str, quantity: int}

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
