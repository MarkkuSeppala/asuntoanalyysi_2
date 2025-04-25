#!/usr/bin/env python3
import json
import logging
import sys
import os

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fix_risk_data_encoding():
    """
    Fixes the encoding of risk data in the database by reencoding it with ensure_ascii=False
    """
    try:
        from models import db, RiskAnalysis
        from app import app  # Import the Flask app to get the app context
        
        logger.info("Starting to fix risk data encoding in the database")
        fixed_count = 0
        error_count = 0
        
        with app.app_context():
            # Get all risk analyses from the database
            all_risk_analyses = RiskAnalysis.query.all()
            logger.info(f"Found {len(all_risk_analyses)} risk analyses to process")
            
            for risk in all_risk_analyses:
                try:
                    if risk.risk_data:
                        # Load the JSON data
                        data = json.loads(risk.risk_data)
                        
                        # Rewrite it with ensure_ascii=False
                        risk.risk_data = json.dumps(data, ensure_ascii=False)
                        fixed_count += 1
                        
                        logger.info(f"Fixed encoding for risk analysis ID {risk.id}")
                except Exception as e:
                    logger.error(f"Error fixing risk analysis ID {risk.id}: {e}")
                    error_count += 1
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Successfully fixed {fixed_count} risk analyses, {error_count} errors")
    
    except Exception as e:
        logger.error(f"Error in fix_risk_data_encoding: {e}")
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Running fix_risk_data_encoding script")
    success = fix_risk_data_encoding()
    
    if success:
        logger.info("Successfully completed fixing risk data encoding")
    else:
        logger.error("Failed to fix risk data encoding")
        sys.exit(1) 