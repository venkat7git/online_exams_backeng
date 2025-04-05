from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database credentials
USERNAME = "root"  # Change if needed
PASSWORD = "Mysql3306m"  # Set your MySQL password
HOST = "localhost"
PORT = "3306"
DATABASE_NAME = "online_exam_system"

# MySQL connection URL
DATABASE_URL = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DATABASE_NAME}"

# Create engine
try:
    engine = create_engine(DATABASE_URL)
    connection = engine.connect()
    print("✅ Database connected successfully!")
    connection.close()
except Exception as e:
    print("❌ Error connecting to database:", e)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
