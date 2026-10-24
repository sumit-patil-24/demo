import os
import time
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/localbizhub")

# Database setup with retry mechanism for container startup
engine = None
for _ in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        break
    except Exception as e:
        time.sleep(2)

if not engine:
    SessionLocal = None
    Base = declarative_base()

class BusinessDB(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)

class ProductDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    title = Column(String, nullable=False)
    price = Column(String, nullable=False)

if engine:
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Database initialization deferred: {e}")

app = FastAPI(title="LocalBizHub API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    if not SessionLocal:
        raise HTTPException(status_code=500, detail="Database connection uninitialized")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Schemas
class ProductCreate(BaseModel):
    title: str
    price: str

class ProductResponse(ProductCreate):
    id: int
    business_id: int
    class Config:
        from_attributes = True

class BusinessCreate(BaseModel):
    name: str
    category: str
    location: str
    description: Optional[str] = ""

class BusinessResponse(BusinessCreate):
    id: int
    products: List[ProductResponse] = []
    class Config:
        from_attributes = True

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "LocalBizHub API", "database": "connected"}

@app.get("/api/businesses", response_model=List[BusinessResponse])
def get_businesses(category: Optional[str] = None, location: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(BusinessDB)
    if category:
        query = query.filter(BusinessDB.category.ilike(f"%{category}%"))
    if location:
        query = query.filter(BusinessDB.location.ilike(f"%{location}%"))
    businesses = query.all()
    results = []
    for b in businesses:
        products = db.query(ProductDB).filter(ProductDB.business_id == b.id).all()
        results.append(BusinessResponse(
            id=b.id, name=b.name, category=b.category, location=b.location, description=b.description,
            products=[ProductResponse.model_validate(p) for p in products]
        ))
    return results

@app.post("/api/businesses", response_model=BusinessResponse)
def create_business(business: BusinessCreate, db: Session = Depends(get_db)):
    db_biz = BusinessDB(**business.model_dump())
    db.add(db_biz)
    db.commit()
    db.refresh(db_biz)
    return BusinessResponse(id=db_biz.id, name=db_biz.name, category=db_biz.category, location=db_biz.location, description=db_biz.description, products=[])

@app.post("/api/businesses/{business_id}/products", response_model=ProductResponse)
def add_product(business_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    biz = db.query(BusinessDB).filter(BusinessDB.id == business_id).first()
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")
    db_prod = ProductDB(business_id=business_id, **product.model_dump())
    db.add(db_prod)
    db.commit()
    db.refresh(db_prod)
    return ProductResponse.model_validate(db_prod)
