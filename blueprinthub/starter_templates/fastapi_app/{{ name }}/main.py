#!/usr/bin/env python3
"""
{{ name }} - FastAPI Application

A FastAPI application with CRUD operations, error handling, and logging.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

{% if orm == "sqlalchemy" %}
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Database setup
DATABASE_URL = "{% if database == 'sqlite' %}sqlite:///./{{ name }}.db{% elif database == 'postgresql' %}postgresql://user:password@localhost/{{ name }}{% elif database == 'mysql' %}mysql+pymysql://user:password@localhost/{{ name }}{% endif %}"
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ItemDB(Base):
    """Database model for items"""
    __tablename__ = "items"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
{% elif orm == "tortoise" %}
from tortoise import fields, models
from tortoise.contrib.fastapi import register_tortoise

class ItemDB(models.Model):
    """Database model for items"""
    id = fields.CharField(pk=True, max_length=36)
    name = fields.CharField(max_length=100, index=True)
    description = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "items"
{% endif %}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("{{ name }}")

# Pydantic models
class ItemBase(BaseModel):
    """Base item model with common attributes"""
    name: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    """Model for creating items"""
    pass

class ItemResponse(ItemBase):
    """Model for item responses"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class ErrorResponse(BaseModel):
    """Model for error responses"""
    detail: str

# Create FastAPI app
app = FastAPI(
    title="{{ name.title() }} API",
    description="A FastAPI application with CRUD operations",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    start_time = datetime.utcnow()
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds() * 1000
    logger.info(f"Response: {response.status_code} (took {process_time:.2f}ms)")
    
    return response

# API Routes
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {"message": "Welcome to {{ name.title() }} API"}

@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/items/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item: ItemCreate,
    {% if orm == "sqlalchemy" %}db: Session = Depends(get_db){% endif %}
):
    """Create a new item"""
    logger.info(f"Creating new item: {item.name}")
    
    item_id = str(uuid.uuid4())
    
    {% if orm == "sqlalchemy" %}
    db_item = ItemDB(
        id=item_id,
        name=item.name,
        description=item.description,
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item
    {% elif orm == "tortoise" %}
    db_item = await ItemDB.create(
        id=item_id,
        name=item.name,
        description=item.description,
    )
    
    return db_item
    {% endif %}

@app.get("/items/", response_model=List[ItemResponse])
async def read_items(
    skip: int = 0,
    limit: int = 100,
    {% if orm == "sqlalchemy" %}db: Session = Depends(get_db){% endif %}
):
    """Get all items with pagination"""
    logger.info(f"Fetching items (skip={skip}, limit={limit})")
    
    {% if orm == "sqlalchemy" %}
    items = db.query(ItemDB).offset(skip).limit(limit).all()
    return items
    {% elif orm == "tortoise" %}
    items = await ItemDB.all().offset(skip).limit(limit)
    return items
    {% endif %}

@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(
    item_id: str,
    {% if orm == "sqlalchemy" %}db: Session = Depends(get_db){% endif %}
):
    """Get a specific item by ID"""
    logger.info(f"Fetching item with ID: {item_id}")
    
    {% if orm == "sqlalchemy" %}
    item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    {% elif orm == "tortoise" %}
    item = await ItemDB.filter(id=item_id).first()
    {% endif %}
    
    if not item:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    return item

@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: str,
    item_update: ItemBase,
    {% if orm == "sqlalchemy" %}db: Session = Depends(get_db){% endif %}
):
    """Update an existing item"""
    logger.info(f"Updating item with ID: {item_id}")
    
    {% if orm == "sqlalchemy" %}
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    {% elif orm == "tortoise" %}
    db_item = await ItemDB.filter(id=item_id).first()
    {% endif %}
    
    if not db_item:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    {% if orm == "sqlalchemy" %}
    db_item.name = item_update.name
    db_item.description = item_update.description
    db_item.updated_at = datetime.utcnow()
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    {% elif orm == "tortoise" %}
    await db_item.update_from_dict({
        "name": item_update.name,
        "description": item_update.description,
    })
    await db_item.save()
    {% endif %}
    
    return db_item

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: str,
    {% if orm == "sqlalchemy" %}db: Session = Depends(get_db){% endif %}
):
    """Delete an item"""
    logger.info(f"Deleting item with ID: {item_id}")
    
    {% if orm == "sqlalchemy" %}
    db_item = db.query(ItemDB).filter(ItemDB.id == item_id).first()
    {% elif orm == "tortoise" %}
    db_item = await ItemDB.filter(id=item_id).first()
    {% endif %}
    
    if not db_item:
        logger.warning(f"Item not found: {item_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )
    
    {% if orm == "sqlalchemy" %}
    db.delete(db_item)
    db.commit()
    {% elif orm == "tortoise" %}
    await db_item.delete()
    {% endif %}

{% if orm == "tortoise" %}
# Register Tortoise ORM
register_tortoise(
    app,
    db_url="{% if database == 'sqlite' %}sqlite://{{ name }}.db{% elif database == 'postgresql' %}postgres://user:password@localhost:5432/{{ name }}{% elif database == 'mysql' %}mysql://user:password@localhost:3306/{{ name }}{% endif %}",
    modules={"models": [__name__]},
    generate_schemas=True,
    add_exception_handlers=True,
)
{% endif %}

if __name__ == "__main__":
    uvicorn.run("{{ name }}.main:app", host="0.0.0.0", port=8000, reload=True)