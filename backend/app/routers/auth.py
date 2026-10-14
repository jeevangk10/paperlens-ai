from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..schemas import RegisterIn, LoginIn
from ..security import hash_password, verify_password, create_token, current_user
router=APIRouter(prefix="/auth", tags=["auth"])
@router.post('/register')
def register(data:RegisterIn, db:Session=Depends(get_db)):
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409,'Email already registered')
    u=User(name=data.name,email=data.email,password_hash=hash_password(data.password)); db.add(u); db.commit(); db.refresh(u)
    return {"token":create_token(u.id),"user":{"id":u.id,"name":u.name,"email":u.email}}
@router.post('/login')
def login(data:LoginIn, db:Session=Depends(get_db)):
    u=db.query(User).filter(User.email==data.email).first()
    if not u or not verify_password(data.password,u.password_hash): raise HTTPException(401,'Invalid email or password')
    return {"token":create_token(u.id),"user":{"id":u.id,"name":u.name,"email":u.email}}
@router.get('/me')
def me(user=Depends(current_user)): return {"id":user.id,"name":user.name,"email":user.email}
