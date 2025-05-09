"""
Subscription Service Module for handling recurring subscriptions.
This module encapsulates the logic for managing subscription lifecycles, 
including creation, renewal, cancellation, and payment processing.
"""

import logging
import uuid
from datetime import datetime, timedelta
from flask import current_app

# Import local modules
import paytrail_service
from models import db, Subscription, Payment, Product, User

logger = logging.getLogger(__name__)

class SubscriptionService:
    """
    Service class for handling subscription operations.
    This class is responsible for the business logic of subscriptions.
    """
    
    @staticmethod
    def create_subscription(user_id, product_id, payment=None, is_trial=False, days=30):
        """
        Create a new subscription for a user.
        
        Args:
            user_id (int): The user ID
            product_id (int): The product ID
            payment (Payment, optional): The payment associated with this subscription
            is_trial (bool, optional): Whether this is a trial subscription
            days (int, optional): Number of days until subscription expires
            
        Returns:
            Subscription: The created subscription object
        """
        try:
            logger.info(f"Creating new subscription for user {user_id}, product {product_id}")
            
            # Check if user already has an active subscription for this product
            existing_sub = Subscription.query.filter_by(
                user_id=user_id,
                product_id=product_id,
                status='active'
            ).first()
            
            if existing_sub:
                logger.info(f"User already has an active subscription (ID: {existing_sub.id})")
                return existing_sub
            
            # Calculate expiration and next billing dates
            now = datetime.utcnow()
            expires_at = now + timedelta(days=days)
            next_billing_date = expires_at
            
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                product_id=product_id,
                subscription_type='monthly',
                status='active',
                expires_at=expires_at,
                is_trial=is_trial,
                next_billing_date=next_billing_date,
                last_payment_date=now if not is_trial else None,
                payment_id=payment.transaction_id if payment else None
            )
            
            db.session.add(subscription)
            
            # Link payment to subscription if provided
            if payment:
                payment.subscription_id = subscription.id
            
            db.session.commit()
            logger.info(f"Successfully created subscription (ID: {subscription.id})")
            
            return subscription
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error creating subscription: {e}")
            raise
    
    @staticmethod
    def cancel_subscription(subscription_id, immediate=False):
        """
        Cancel a subscription.
        
        Args:
            subscription_id (int): The subscription ID to cancel
            immediate (bool, optional): Whether to cancel immediately or at period end
            
        Returns:
            bool: True if canceled successfully, False otherwise
        """
        try:
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return False
                
            logger.info(f"Cancelling subscription {subscription_id}, immediate={immediate}")
            
            if immediate:
                subscription.status = 'cancelled'
                subscription.expires_at = datetime.utcnow()
            else:
                subscription.cancel_at_period_end = True
                
            db.session.commit()
            logger.info(f"Successfully cancelled subscription {subscription_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error cancelling subscription: {e}")
            return False
    
    @staticmethod
    def renew_subscription(subscription_id, payment=None, days=30):
        """
        Renew a subscription for another period.
        
        Args:
            subscription_id (int): The subscription ID to renew
            payment (Payment, optional): The payment associated with this renewal
            days (int, optional): Number of days to extend subscription
            
        Returns:
            bool: True if renewed successfully, False otherwise
        """
        try:
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return False
                
            logger.info(f"Renewing subscription {subscription_id} for {days} days")
            
            # Update subscription dates
            now = datetime.utcnow()
            # If subscription has already expired, extend from current date
            if subscription.expires_at < now:
                subscription.expires_at = now + timedelta(days=days)
            else:
                # Otherwise extend from current expiration date
                subscription.expires_at = subscription.expires_at + timedelta(days=days)
                
            subscription.next_billing_date = subscription.expires_at
            subscription.last_payment_date = now
            subscription.status = 'active'  # Ensure status is active
            subscription.cancel_at_period_end = False  # Reset cancellation flag
            
            # Update payment reference if provided
            if payment:
                subscription.payment_id = payment.transaction_id
                payment.subscription_id = subscription.id
                
            db.session.commit()
            logger.info(f"Successfully renewed subscription {subscription_id} until {subscription.expires_at}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error renewing subscription: {e}")
            return False
    
    @staticmethod
    def process_recurring_payment(subscription_id, redirect_url_base=None):
        """
        Process a recurring payment for a subscription.
        This creates a new payment record and initiates the Paytrail payment flow.
        
        Args:
            subscription_id (int): The subscription ID for the payment
            redirect_url_base (str, optional): Base URL for Paytrail redirects
            
        Returns:
            dict: Payment result dictionary with payment URL and transaction details
        """
        try:
            subscription = Subscription.query.get(subscription_id)
            if not subscription:
                logger.error(f"Subscription {subscription_id} not found")
                return {"success": False, "error": "Subscription not found"}
                
            # Get product details
            product = Product.query.get(subscription.product_id)
            if not product:
                logger.error(f"Product {subscription.product_id} not found")
                return {"success": False, "error": "Product not found"}
                
            # Create a new payment in our database
            payment = Payment(
                user_id=subscription.user_id,
                product_id=product.id,
                subscription_id=subscription.id,
                amount=product.price,
                payment_method='paytrail',
                status='pending'  # Will be updated when payment is completed
            )
            
            db.session.add(payment)
            db.session.commit()
            
            logger.info(f"Created pending payment (ID: {payment.id}) for subscription {subscription_id}")
            
            # Create Paytrail payment
            payment_result = paytrail_service.create_payment(
                user_id=subscription.user_id,
                product=product,
                redirect_url_base=redirect_url_base
            )
            
            if payment_result["success"]:
                # Update our payment record with transaction ID
                payment.transaction_id = payment_result["transaction_id"]
                db.session.commit()
                
                logger.info(f"Successfully created Paytrail payment for subscription {subscription_id}")
                return payment_result
            else:
                logger.error(f"Failed to create Paytrail payment: {payment_result.get('error')}")
                payment.status = 'failed'
                db.session.commit()
                return payment_result
                
        except Exception as e:
            db.session.rollback()
            logger.exception(f"Error processing recurring payment: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_subscriptions_due_for_renewal(days_before=3):
        """
        Get all subscriptions that are due for renewal.
        This finds subscriptions that are about to expire within the specified days.
        
        Args:
            days_before (int): Number of days before expiration to consider for renewal
            
        Returns:
            list: List of Subscription objects due for renewal
        """
        try:
            now = datetime.utcnow()
            renewal_cutoff = now + timedelta(days=days_before)
            
            # Find active subscriptions that are not marked for cancellation
            # and are due for renewal within the specified days
            subscriptions_due = Subscription.query.filter(
                Subscription.status == 'active',
                Subscription.cancel_at_period_end == False,
                Subscription.next_billing_date <= renewal_cutoff
            ).all()
            
            logger.info(f"Found {len(subscriptions_due)} subscriptions due for renewal")
            return subscriptions_due
            
        except Exception as e:
            logger.exception(f"Error getting subscriptions due for renewal: {e}")
            return []

# Create a singleton instance
subscription_service = SubscriptionService() 