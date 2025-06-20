# back/demo_aurora.py
"""
Demo script for AWS Aurora Serverless v2 database operations.
This script demonstrates how to connect to an AWS Aurora Serverless v2 database
and perform basic CRUD operations using SQLAlchemy ORM.
"""
import os
import sys
from sqlalchemy.orm import Session

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our database modules
from back.database import engine, SessionLocal, get_db
from back.models_orm import Challenge, Task

def create_sample_data(db: Session):
    """Create sample data in the database"""
    print("Creating sample data...")
    
    # Create challenges
    challenge1 = Challenge(title="AWS Cloud Challenge 2023")
    challenge2 = Challenge(title="Database Performance Challenge")
    challenge3 = Challenge(title="Serverless Architecture Challenge")
    
    # Add challenges to the session
    db.add(challenge1)
    db.add(challenge2)
    db.add(challenge3)
    
    # Commit the changes to get IDs
    db.commit()
    
    # Create tasks
    task1 = Task(title="Set up Aurora Serverless v2", status="COMPLETED")
    task2 = Task(title="Configure connection pooling", status="PENDING")
    task3 = Task(title="Implement database models", status="IN_PROGRESS")
    task4 = Task(title="Write unit tests", status="COMPLETED")
    
    # Add tasks to the session
    db.add(task1)
    db.add(task2)
    db.add(task3)
    db.add(task4)
    
    # Commit the changes
    db.commit()
    
    print("Sample data created successfully!")

def query_data(db: Session):
    """Query data from the database"""
    print("\nQuerying challenges...")
    challenges = db.query(Challenge).all()
    for challenge in challenges:
        print(f"Challenge ID: {challenge.id}, Title: {challenge.title}")
    
    print("\nQuerying tasks...")
    tasks = db.query(Task).all()
    for task in tasks:
        print(f"Task ID: {task.id}, Title: {task.title}, Status: {task.status}")
    
    print("\nQuerying completed tasks...")
    completed_tasks = db.query(Task).filter(Task.status == "COMPLETED").all()
    for task in completed_tasks:
        print(f"Completed Task: {task.title}")

def update_data(db: Session):
    """Update data in the database"""
    print("\nUpdating data...")
    
    # Update a challenge
    challenge = db.query(Challenge).filter(Challenge.title.like("%Cloud%")).first()
    if challenge:
        old_title = challenge.title
        challenge.title = "AWS Cloud & Serverless Challenge 2023"
        db.commit()
        print(f"Updated challenge title from '{old_title}' to '{challenge.title}'")
    
    # Update a task status
    task = db.query(Task).filter(Task.status == "PENDING").first()
    if task:
        old_status = task.status
        task.status = "IN_PROGRESS"
        db.commit()
        print(f"Updated task '{task.title}' status from '{old_status}' to '{task.status}'")

def delete_data(db: Session):
    """Delete data from the database"""
    print("\nDeleting data...")
    
    # Delete a challenge
    challenge = db.query(Challenge).filter(Challenge.title.like("%Performance%")).first()
    if challenge:
        title = challenge.title
        db.delete(challenge)
        db.commit()
        print(f"Deleted challenge: '{title}'")
    
    # Count remaining challenges
    count = db.query(Challenge).count()
    print(f"Remaining challenges: {count}")

def main():
    """Main function to demonstrate Aurora Serverless v2 database operations"""
    print("AWS Aurora Serverless v2 Database Demo")
    print("=====================================")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Using default connection string')}")
    
    # Create database tables if they don't exist
    print("\nCreating database tables...")
    from back.models_orm import Base
    Base.metadata.create_all(bind=engine)
    
    # Get a database session
    db = SessionLocal()
    
    try:
        # Perform database operations
        create_sample_data(db)
        query_data(db)
        update_data(db)
        delete_data(db)
        
        print("\nDemo completed successfully!")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Close the database session
        db.close()

if __name__ == "__main__":
    main()