from sqlalchemy import create_engine, text
from app.database import DATABASE_URL
import os
from dotenv import load_dotenv

load_dotenv()

def create_notifications_table():
    engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
    
    with engine.connect() as connection:
        # Drop existing table if it exists (for development)
        drop_table_sql = """
        DROP TABLE IF EXISTS notifications CASCADE;
        """
        
        # Create notifications table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            type VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
            read_at TIMESTAMP WITH TIME ZONE
        );
        """
        
        # Create index for better performance
        create_index_sql = """
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_task_id ON notifications(task_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
        CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
        """
        
        try:
            connection.execute(text(drop_table_sql))
            connection.execute(text(create_table_sql))
            connection.execute(text(create_index_sql))
            connection.commit()
            print("✅ Notifications table created successfully!")
        except Exception as e:
            print(f"❌ Error creating notifications table: {e}")
            connection.rollback()

if __name__ == "__main__":
    create_notifications_table()
