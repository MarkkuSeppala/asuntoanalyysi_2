import secrets
import string
from datetime import datetime, timedelta
from models import db, User
import logging

logger = logging.getLogger(__name__)

def generate_verification_token(length=64):
    """
    Luo satunnaisen varmistustokenin rekisteröitymistä varten.
    
    Args:
        length (int): Tokenin pituus merkkeinä.
    
    Returns:
        str: Uniikki satunnainen merkistä koostuva token.
    """
    alphabet = string.ascii_letters + string.digits
    token = ''.join(secrets.choice(alphabet) for _ in range(length))
    return token

def save_verification_token(user, token):
    """
    Tallentaa varmistustokenin käyttäjän tietoihin.
    
    Args:
        user (User): Käyttäjäobjekti.
        token (str): Varmistustoken.
    
    Returns:
        bool: True jos tallennus onnistui, False jos epäonnistui.
    """
    try:
        user.verification_token = token
        user.verification_token_created_at = datetime.utcnow()
        user.is_verified = False
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error saving verification token: {str(e)}")
        db.session.rollback()
        return False

def is_token_expired(token_created_at, expiry_hours=24):
    """
    Tarkistaa onko token vanhentunut.
    
    Args:
        token_created_at (datetime): Tokenin luontiaika.
        expiry_hours (int): Tokenin voimassaoloaika tunteina.
    
    Returns:
        bool: True jos token on vanhentunut, False jos voimassa.
    """
    if not token_created_at:
        return True
        
    expiry_time = token_created_at + timedelta(hours=expiry_hours)
    return datetime.utcnow() > expiry_time

def validate_token(token):
    """
    Tarkistaa tokenin oikeellisuuden ja voimassaolon.
    
    Args:
        token (str): Tarkistettava token.
    
    Returns:
        tuple: (User-objekti jos token on kelvollinen, status)
            status voi olla: 'valid', 'expired', 'invalid'
    """
    try:
        user = User.query.filter_by(verification_token=token).first()
        
        if not user:
            return None, 'invalid'
            
        if is_token_expired(user.verification_token_created_at):
            return user, 'expired'
            
        return user, 'valid'
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return None, 'invalid'

def mark_email_verified(user):
    """
    Merkitsee käyttäjän sähköpostiosoitteen vahvistetuksi.
    
    Args:
        user (User): Käyttäjäobjekti.
    
    Returns:
        bool: True jos merkintä onnistui, False jos epäonnistui.
    """
    try:
        user.is_verified = True
        user.verification_token = None
        user.verification_token_created_at = None
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Error marking email as verified: {str(e)}")
        db.session.rollback()
        return False 