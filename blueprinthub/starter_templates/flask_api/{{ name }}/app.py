#!/usr/bin/env python3
"""
{{ name }} - Flask API Application

A Flask API with REST endpoints, error handling, and configuration.
"""
import json
import logging
import os
import uuid
from datetime import datetime
from functools import wraps

from flask import Flask, Response, jsonify, request, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import HTTPException

# Configuration
class Config:
    """Base configuration"""
    DEBUG = False
    TESTING = False
    {% if database == "sqlite" %}
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:////{os.path.abspath(os.getcwd())}/{{ name }}.db"
    )
    {% elif database == "postgresql" %}
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "postgresql://user:password@localhost:5432/{{ name }}"
    )
    {% elif database == "mysql" %}
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://user:password@localhost:3306/{{ name }}"
    )
    {% endif %}
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = logging.DEBUG

class ProductionConfig(Config):
    """Production configuration"""
    pass

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    {% if database == "sqlite" %}
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    {% endif %}

# Select configuration based on environment
config_dict = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}
config = config_dict.get(os.environ.get("FLASK_ENV", "development"))

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Set up logging
logging.basicConfig(
    level=app.config["LOG_LEVEL"],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("{{ name }}")

# Initialize database
db = SQLAlchemy(app)

# Request timing middleware
@app.before_request
def start_timer():
    """Start timing the request"""
    g.start_time = datetime.utcnow()

@app.after_request
def log_request(response):
    """Log request details including time taken"""
    if hasattr(g, 'start_time'):
        elapsed = (datetime.utcnow() - g.start_time).total_seconds() * 1000
        logger.info(
            f"Request: {request.method} {request.path} - "
            f"Status: {response.status_code} - "
            f"Duration: {elapsed:.2f}ms"
        )
    return response

# Define database models
class Item(db.Model):
    """Item model for database storage"""
    __tablename__ = "items"
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

# Helper functions
def validate_json(f):
    """Decorator to validate JSON payload"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if not request.is_json:
                return jsonify({"error": "Missing JSON in request"}), 400
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"JSON validation error: {str(e)}")
            return jsonify({"error": "Invalid JSON"}), 400
    return wrapper

# Error handlers
@app.errorhandler(HTTPException)
def handle_http_exception(error):
    """Handle HTTP exceptions"""
    response = jsonify({"error": error.description})
    response.status_code = error.code
    logger.error(f"HTTP error: {error.code} - {error.description}")
    return response

@app.errorhandler(Exception)
def handle_generic_exception(error):
    """Handle generic exceptions"""
    logger.error(f"Unexpected error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

# API Routes
@app.route("/", methods=["GET"])
def index():
    """Root endpoint"""
    return jsonify({"message": "Welcome to {{ name.title() }} API"})

@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"})

@app.route("/items", methods=["GET"])
def get_items():
    """Get all items with optional pagination"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    
    # Apply pagination
    paginated_items = Item.query.paginate(page=page, per_page=per_page)
    
    # Format response
    return jsonify({
        "items": [item.to_dict() for item in paginated_items.items],
        "pagination": {
            "page": paginated_items.page,
            "per_page": paginated_items.per_page,
            "total_items": paginated_items.total,
            "total_pages": paginated_items.pages
        }
    })

@app.route("/items/<string:item_id>", methods=["GET"])
def get_item(item_id):
    """Get a specific item by ID"""
    item = Item.query.get(item_id)
    
    if not item:
        logger.warning(f"Item not found: {item_id}")
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify(item.to_dict())

@app.route("/items", methods=["POST"])
@validate_json
def create_item():
    """Create a new item"""
    data = request.get_json()
    
    # Validate required fields
    if not data.get("name"):
        return jsonify({"error": "Name is required"}), 400
    
    # Create new item
    item = Item(
        id=str(uuid.uuid4()),
        name=data["name"],
        description=data.get("description")
    )
    
    db.session.add(item)
    db.session.commit()
    
    logger.info(f"Created new item with ID: {item.id}")
    return jsonify(item.to_dict()), 201

@app.route("/items/<string:item_id>", methods=["PUT"])
@validate_json
def update_item(item_id):
    """Update an existing item"""
    item = Item.query.get(item_id)
    
    if not item:
        logger.warning(f"Item not found for update: {item_id}")
        return jsonify({"error": "Item not found"}), 404
    
    data = request.get_json()
    
    # Update fields if provided
    if "name" in data:
        item.name = data["name"]
    if "description" in data:
        item.description = data.get("description")
    
    db.session.commit()
    logger.info(f"Updated item with ID: {item.id}")
    
    return jsonify(item.to_dict())

@app.route("/items/<string:item_id>", methods=["DELETE"])
def delete_item(item_id):
    """Delete an item"""
    item = Item.query.get(item_id)
    
    if not item:
        logger.warning(f"Item not found for deletion: {item_id}")
        return jsonify({"error": "Item not found"}), 404
    
    db.session.delete(item)
    db.session.commit()
    logger.info(f"Deleted item with ID: {item_id}")
        
        return "", 204

    # Create database tables
    with app.app_context():
        db.create_all()

if __name__ == "__main__":
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000)