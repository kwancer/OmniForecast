import os

from dotenv import load_dotenv
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, ForecastSession, engine

load_dotenv()


def verify_connection():
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL')[:20]}...")
    try:
        # Tables should be created upon import of database.py due to Base.metadata.create_all
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")

        if "sessions" in tables:
            print("SUCCESS: 'sessions' table exists.")
        else:
            print("FAILURE: 'sessions' table not found. Attempting to create...")
            Base.metadata.create_all(bind=engine)
            tables = inspector.get_table_names()
            print(f"Tables after creation attempt: {tables}")
            if "sessions" in tables:
                print("SUCCESS: 'sessions' table created.")
            else:
                print("FAILURE: Could not create tables.")
                return False

        # Test basic CRUD
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        try:
            print("Testing DB insert...")
            test_session = ForecastSession(
                session_id="test-connection-id",
                user_intent="Testing connection",
                ontology={"test": True},
            )
            db.add(test_session)
            db.commit()
            print("SUCCESS: Test record inserted.")

            print("Testing DB query...")
            queried = (
                db.query(ForecastSession)
                .filter(ForecastSession.session_id == "test-connection-id")
                .first()
            )
            if queried:
                print(f"SUCCESS: Test record retrieved: {queried.session_id}")

            print("Cleaning up test record...")
            db.delete(queried)
            db.commit()
            print("SUCCESS: Test record deleted.")
            return True
        except Exception as e:
            print(f"CRUD ERROR: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    except Exception as e:
        print(f"CONNECTION ERROR: {e}")
        return False


if __name__ == "__main__":
    if verify_connection():
        print("\nDATABASE CONNECTION VERIFIED SUCCESSFULLY!")
    else:
        print("\nDATABASE CONNECTION FAILED!")
