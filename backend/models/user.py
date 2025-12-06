"""
User Model - Database models for user authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Profile information
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    bio = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    location = Column(String, nullable=True)
    website = Column(String, nullable=True)
    profile_picture_url = Column(String, nullable=True)

# Database setup
# Default to SQLite for development, use PostgreSQL if DATABASE_URL is set
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./thesentient.db')

# Use PostgreSQL if DATABASE_URL is set and starts with postgresql, otherwise SQLite
if DATABASE_URL.startswith('postgresql'):
    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    except Exception as e:
        print(f"Warning: Failed to connect to PostgreSQL: {e}")
        print("Falling back to SQLite...")
        DATABASE_URL = 'sqlite:///./thesentient.db'
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # SQLite configuration (default/fallback)
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    try:
        # Check if we need to migrate (add missing columns for SQLite)
        if DATABASE_URL.startswith('sqlite'):
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(engine)
                table_names = inspector.get_table_names()
                
                if 'users' in table_names:
                    # Table exists, check for missing columns
                    existing_columns = [col['name'] for col in inspector.get_columns('users')]
                    
                    # List of new columns to add
                    new_columns = {
                        'first_name': 'VARCHAR',
                        'last_name': 'VARCHAR',
                        'bio': 'VARCHAR',
                        'phone': 'VARCHAR',
                        'location': 'VARCHAR',
                        'website': 'VARCHAR',
                        'profile_picture_url': 'VARCHAR'
                    }
                    
                    # Add missing columns
                    with engine.begin() as conn:  # Use begin() for transaction
                        for col_name, col_type in new_columns.items():
                            if col_name not in existing_columns:
                                try:
                                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                                    print(f"Added column {col_name} to users table")
                                except Exception as e:
                                    print(f"Could not add column {col_name}: {e}")
                else:
                    # Table doesn't exist, create it
                    Base.metadata.create_all(bind=engine)
            except Exception as e:
                print(f"Migration check failed: {e}, recreating tables...")
                # Fallback: recreate tables
                try:
                    Base.metadata.drop_all(bind=engine)
                except:
                    pass
                Base.metadata.create_all(bind=engine)
        else:
            # For PostgreSQL, just create/update tables
            Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Error initializing database: {e}")
        # Try to create tables anyway
        try:
            Base.metadata.create_all(bind=engine)
        except Exception as e2:
            print(f"Failed to create tables: {e2}")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

