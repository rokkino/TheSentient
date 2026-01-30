"""
User Model - Database models for user authentication
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import json

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
    tabs = Column(Text, nullable=True)  # JSON string storing user's tab configuration
    use_local_llama = Column(Boolean, default=False)  # Toggle for local Llama (Ollama)
    gemini_api_key = Column(String, nullable=True)  # Google Gemini API Key (Flash/Free)
    
    # AI Configuration
    ai_provider = Column(String, default="gemini")  # gemini, openai, anthropic, deepseek
    gemini_pro_api_key = Column(String, nullable=True)  # Google Gemini Pro (Paid)
    openai_api_key = Column(String, nullable=True)  # ChatGPT
    anthropic_api_key = Column(String, nullable=True)  # Claude
    deepseek_api_key = Column(String, nullable=True)  # Deepseek
    llama_api_key = Column(String, nullable=True)  # Llama API

    # AI model versions (per-provider)
    gemini_model = Column(String, nullable=True)  # e.g. gemini-3.0-flash
    openai_model = Column(String, nullable=True)  # e.g. gpt-4o
    anthropic_model = Column(String, nullable=True)  # e.g. claude-3-5-sonnet-20240620
    deepseek_model = Column(String, nullable=True)  # e.g. deepseek-chat
    llama_model = Column(String, nullable=True)  # e.g. llama-3.3-70b-instruct

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
        # Import bot and message models to ensure they're registered with Base
        from models.bot import Bot, Decision
        from models.chat import Message
        from models.news import News
        from models.strategy import Strategy
        
        # Check if we need to migrate (add missing columns for SQLite)
        if DATABASE_URL.startswith('sqlite'):
            try:
                from sqlalchemy import inspect, text
                inspector = inspect(engine)
                table_names = inspector.get_table_names()
                
                # Always create all tables first (including bots table)
                Base.metadata.create_all(bind=engine)
                
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
                        'profile_picture_url': 'VARCHAR',
                        'tabs': 'TEXT',
                        'use_local_llama': 'BOOLEAN',
                        'gemini_api_key': 'VARCHAR',
                        'ai_provider': 'VARCHAR DEFAULT "gemini"',
                        'gemini_pro_api_key': 'VARCHAR',
                        'openai_api_key': 'VARCHAR',
                        'anthropic_api_key': 'VARCHAR',
                        'deepseek_api_key': 'VARCHAR',
                        'llama_api_key': 'VARCHAR',
                        'gemini_model': 'VARCHAR',
                        'openai_model': 'VARCHAR',
                        'anthropic_model': 'VARCHAR',
                        'deepseek_model': 'VARCHAR',
                        'llama_model': 'VARCHAR'
                    }
                    
                    # Add missing columns
                    with engine.begin() as conn:  # Use begin() for transaction
                        for col_name, col_type in new_columns.items():
                            if col_name not in existing_columns:
                                try:
                                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                                    print(f"Added column {col_name} to users table")
                                except Exception as e:
                                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                                    print(f"Added column {col_name} to users table")
                                except Exception as e:
                                    print(f"Could not add column {col_name}: {e}")
                
                if 'messages' in table_names:
                    # Check for missing columns in messages table
                    existing_columns = [col['name'] for col in inspector.get_columns('messages')]
                    
                    if 'recipient_id' not in existing_columns:
                        try:
                            with engine.begin() as conn:
                                conn.execute(text("ALTER TABLE messages ADD COLUMN recipient_id INTEGER"))
                                print("Added column recipient_id to messages table")
                        except Exception as e:
                            print(f"Could not add column recipient_id: {e}")
            except Exception as e:
                print(f"Migration check failed: {e}, creating all tables...")
                # Fallback: create all tables
                try:
                    Base.metadata.create_all(bind=engine)
                except Exception as e2:
                    print(f"Failed to create tables: {e2}")
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

