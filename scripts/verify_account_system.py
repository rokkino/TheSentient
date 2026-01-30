import sys
import os
import json
import logging

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.user import User, Base
from models.account import Account
from models.bot import Bot
from services.bot_service import bot_service
from services.ig_service import IGMarketsService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Override DB for testing - Use a fresh file to ensure schema is correct
TEST_DB_URL = "sqlite:///./test_verify.db"
if os.path.exists("./test_verify.db"):
    os.remove("./test_verify.db")

test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def verify_account_system():
    # Bind engine to test engine
    Base.metadata.create_all(bind=test_engine)
    
    db = TestSessionLocal()
    try:
        # 1. Setup Test User
        user = db.query(User).filter(User.username == 'test_admin').first()
        if not user:
            logger.info("Creating test user...")
            user = User(username='test_admin', email='admin@test.com')
            user.set_password('password123')
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # 2. Create Test Account (IG)
        logger.info("Creating test IG account...")
        creds = json.dumps({
            "username": "ig_test_user",
            "password": "ig_test_password",
            "api_key": "ig_test_key",
            "account_type": "DEMO"
        })
        account = Account(
            user_id=user.id,
            platform='IG',
            name='Test IG Account',
            credentials=creds,
            is_active=True
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info(f"Created Account ID: {account.id}")
        
        # 3. Create Bot linked to Account
        logger.info("Creating bot linked to account...")
        bot_config = {
            "broker": "IG",
            "account_id": account.id
        }
        bot = Bot(
            user_id=user.id,
            name='Test Account Bot',
            bot_type='earnings_report_genius',
            config=json.dumps(bot_config),
            is_active=True,
            status='active'
        )
        db.add(bot)
        db.commit()
        db.refresh(bot)
        logger.info(f"Created Bot ID: {bot.id}")
        
        # 4. Verify Service Resolution
        logger.info("Verifying service resolution...")
        service = bot_service._get_configured_service(db, bot)
        
        if isinstance(service, IGMarketsService):
            logger.info("SUCCESS: Service resolved as IGMarketsService")
            # Verify credentials in service
            if service.username == "ig_test_user" and service.api_key == "ig_test_key":
                 logger.info("SUCCESS: Credentials correctly injected into service")
            else:
                 logger.error(f"FAILURE: Credentials mismatch. Got: {service.username}, expected ig_test_user")
        else:
            logger.error(f"FAILURE: Service is not IGMarketsService. Got: {type(service)}")
            
        # Cleanup
        logger.info("Cleaning up...")
        db.delete(bot)
        db.delete(account)
        # db.delete(user) # Keep user for other tests
        db.commit()
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_account_system()
