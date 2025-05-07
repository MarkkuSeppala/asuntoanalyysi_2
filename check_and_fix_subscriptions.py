import os
import sys
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_database_url():
    """Get database URL from environment or use default SQLite database"""
    database_url = os.environ.get('DATABASE_URL')
    
    # Fall back to SQLite if no DATABASE_URL is provided
    if not database_url:
        database_url = 'sqlite:///flask_database.db'
        logger.info(f"Using default SQLite database: {database_url}")
    else:
        # Handle postgres:// vs postgresql:// URL prefix
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        logger.info(f"Using database URL from environment")
    
    return database_url

def check_and_fix_subscriptions_table():
    """Check subscriptions table structure and fix it to match models.py"""
    # Get database URL
    db_url = get_database_url()
    
    try:
        # Create engine and connect
        engine = create_engine(db_url)
        conn = engine.connect()
        inspector = inspect(engine)
        
        logger.info("Connected to database successfully")
        
        # Check if subscriptions table exists
        if 'subscriptions' not in inspector.get_table_names():
            logger.error("Subscriptions table does not exist in the database")
            return False
        
        # Get existing columns
        columns = [col['name'] for col in inspector.get_columns('subscriptions')]
        logger.info(f"Existing columns in subscriptions table: {columns}")
        
        # Check for missing columns based on models.py
        expected_columns = [
            'id', 'user_id', 'product_id', 'subscription_type', 
            'status', 'created_at', 'expires_at', 'is_trial', 
            'next_billing_date', 'cancel_at_period_end', 'last_payment_date', 'payment_id'
        ]
        
        missing_columns = [col for col in expected_columns if col not in columns]
        logger.info(f"Missing columns: {missing_columns}")
        
        # Add missing columns
        for column in missing_columns:
            logger.info(f"Adding missing column: {column}")
            
            if column == 'subscription_type':
                # Add subscription_type column
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN subscription_type VARCHAR(50);
                """))
                
                # Update existing rows based on product type
                conn.execute(text("""
                    UPDATE subscriptions 
                    SET subscription_type = (
                        SELECT 
                            CASE 
                                WHEN p.type = 'subscription' THEN 'monthly' 
                                WHEN p.type = 'one_time' THEN 'one_time'
                                ELSE 'monthly'
                            END
                        FROM products p 
                        WHERE p.id = subscriptions.product_id
                    );
                """))
                
                # Make the column non-nullable
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ALTER COLUMN subscription_type SET NOT NULL;
                """))
            
            elif column == 'is_trial':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN is_trial BOOLEAN NOT NULL DEFAULT false;
                """))
            
            elif column == 'cancel_at_period_end':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN cancel_at_period_end BOOLEAN NOT NULL DEFAULT false;
                """))
            
            elif column == 'created_at':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;
                """))
            
            elif column == 'expires_at':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN expires_at TIMESTAMP WITHOUT TIME ZONE;
                """))
            
            elif column == 'next_billing_date':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN next_billing_date TIMESTAMP WITHOUT TIME ZONE;
                """))
            
            elif column == 'last_payment_date':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN last_payment_date TIMESTAMP WITHOUT TIME ZONE;
                """))
            
            elif column == 'payment_id':
                conn.execute(text("""
                    ALTER TABLE subscriptions 
                    ADD COLUMN payment_id VARCHAR(100);
                """))
                
        conn.commit()
        
        # Verify changes
        updated_columns = [col['name'] for col in inspector.get_columns('subscriptions')]
        logger.info(f"Updated columns in subscriptions table: {updated_columns}")
        
        missing_after_update = [col for col in expected_columns if col not in updated_columns]
        if missing_after_update:
            logger.warning(f"Still missing columns after update: {missing_after_update}")
        else:
            logger.info("All expected columns are now present in the subscriptions table")
            
        # Show sample data
        result = conn.execute(text("""
            SELECT id, user_id, product_id, subscription_type, status 
            FROM subscriptions 
            LIMIT 5;
        """))
        
        rows = result.fetchall()
        if rows:
            logger.info("Sample data from subscriptions table:")
            for row in rows:
                logger.info(f"  {row}")
        else:
            logger.info("Subscriptions table is empty")
            
        conn.close()
        return True
            
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting subscriptions table check and fix")
    success = check_and_fix_subscriptions_table()
    
    if success:
        logger.info("Subscriptions table check and fix completed successfully")
        sys.exit(0)
    else:
        logger.error("Failed to check and fix subscriptions table")
        sys.exit(1) 