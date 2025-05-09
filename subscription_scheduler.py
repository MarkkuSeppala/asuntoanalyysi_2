"""
Subscription Scheduler Module
This module is responsible for scheduling and executing subscription renewals
and handling the automated billing cycle.
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from flask import current_app
import schedule

from models import db, Subscription, User, Payment
from subscription_service import subscription_service
import email_service

logger = logging.getLogger(__name__)

class SubscriptionScheduler:
    """
    Manages the scheduling of subscription-related tasks.
    This includes renewal notifications, payment processing, and expiration checks.
    """
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
        logger.info("Subscription scheduler initialized")
        
    def start(self):
        """Start the scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting subscription scheduler")
        self.running = True
        
        # Schedule daily subscription tasks
        schedule.every().day.at("03:00").do(self.process_renewals)
        schedule.every().day.at("10:00").do(self.send_renewal_reminders)
        schedule.every().day.at("14:00").do(self.handle_failed_payments)
        schedule.every().day.at("20:00").do(self.expire_subscriptions)
        
        # Start the scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        logger.info("Subscription scheduler started")
        
    def stop(self):
        """Stop the scheduler"""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
            
        logger.info("Stopping subscription scheduler")
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=2.0)
        logger.info("Subscription scheduler stopped")
        
    def _run_scheduler(self):
        """Run the scheduler loop"""
        logger.info("Scheduler thread started")
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    def process_renewals(self):
        """
        Process subscription renewals for all subscriptions due to be renewed
        """
        logger.info("Processing subscription renewals")
        try:
            with current_app.app_context():
                subscriptions = subscription_service.get_subscriptions_due_for_renewal()
                
                logger.info(f"Found {len(subscriptions)} subscriptions to renew")
                
                for subscription in subscriptions:
                    try:
                        # Get base URL from config
                        base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
                        
                        # Initiate payment for subscription renewal
                        payment_result = subscription_service.process_recurring_payment(
                            subscription.id,
                            redirect_url_base=base_url
                        )
                        
                        if payment_result["success"]:
                            # Send renewal payment email with payment link
                            user = User.query.get(subscription.user_id)
                            if user and user.email:
                                email_service.send_subscription_renewal_email(
                                    user.email,
                                    user.first_name,
                                    payment_result["payment_url"]
                                )
                                logger.info(f"Sent renewal email to {user.email} for subscription {subscription.id}")
                        else:
                            logger.error(f"Failed to create payment for subscription {subscription.id}: {payment_result.get('error')}")
                            
                    except Exception as e:
                        logger.exception(f"Error processing renewal for subscription {subscription.id}: {e}")
                        
        except Exception as e:
            logger.exception(f"Error in process_renewals: {e}")
    
    def send_renewal_reminders(self):
        """
        Send renewal reminder emails to users whose subscriptions
        will be renewed soon
        """
        logger.info("Sending subscription renewal reminders")
        try:
            with current_app.app_context():
                # Get subscriptions expiring in 5 days
                now = datetime.utcnow()
                reminder_date = now + timedelta(days=5)
                
                subscriptions = Subscription.query.filter(
                    Subscription.status == 'active',
                    Subscription.cancel_at_period_end == False,
                    Subscription.next_billing_date <= reminder_date,
                    Subscription.next_billing_date > now + timedelta(days=4)
                ).all()
                
                logger.info(f"Found {len(subscriptions)} subscriptions for renewal reminders")
                
                for subscription in subscriptions:
                    try:
                        user = User.query.get(subscription.user_id)
                        if user and user.email:
                            email_service.send_subscription_renewal_reminder_email(
                                user.email,
                                user.first_name,
                                subscription.next_billing_date
                            )
                            logger.info(f"Sent renewal reminder to {user.email} for subscription {subscription.id}")
                    except Exception as e:
                        logger.exception(f"Error sending reminder for subscription {subscription.id}: {e}")
                        
        except Exception as e:
            logger.exception(f"Error in send_renewal_reminders: {e}")
    
    def handle_failed_payments(self):
        """
        Handle subscriptions with failed renewal payments
        """
        logger.info("Handling failed renewal payments")
        try:
            with current_app.app_context():
                # Get subscriptions that should have been renewed but have failed payments
                three_days_ago = datetime.utcnow() - timedelta(days=3)
                
                failed_subscriptions = Subscription.query.join(
                    Payment, 
                    Subscription.id == Payment.subscription_id
                ).filter(
                    Subscription.next_billing_date < datetime.utcnow(),
                    Subscription.status == 'active',
                    Payment.status == 'failed',
                    Payment.created_at > three_days_ago
                ).all()
                
                logger.info(f"Found {len(failed_subscriptions)} subscriptions with failed payments")
                
                for subscription in failed_subscriptions:
                    try:
                        user = User.query.get(subscription.user_id)
                        if user and user.email:
                            # Get base URL from config
                            base_url = current_app.config.get('BASE_URL', 'http://localhost:5000')
                            
                            # Try to create a new payment
                            payment_result = subscription_service.process_recurring_payment(
                                subscription.id,
                                redirect_url_base=base_url
                            )
                            
                            if payment_result["success"]:
                                email_service.send_failed_payment_retry_email(
                                    user.email,
                                    user.first_name,
                                    payment_result["payment_url"]
                                )
                                logger.info(f"Sent payment retry email to {user.email} for subscription {subscription.id}")
                            else:
                                logger.error(f"Failed to create retry payment for subscription {subscription.id}")
                                
                    except Exception as e:
                        logger.exception(f"Error handling failed payment for subscription {subscription.id}: {e}")
                        
        except Exception as e:
            logger.exception(f"Error in handle_failed_payments: {e}")
    
    def expire_subscriptions(self):
        """
        Mark expired subscriptions as inactive
        """
        logger.info("Processing subscription expirations")
        try:
            with current_app.app_context():
                # Find subscriptions that have expired
                expired_subscriptions = Subscription.query.filter(
                    Subscription.status == 'active',
                    Subscription.expires_at < datetime.utcnow()
                ).all()
                
                logger.info(f"Found {len(expired_subscriptions)} expired subscriptions")
                
                for subscription in expired_subscriptions:
                    try:
                        # If the subscription was set to cancel at period end, mark as cancelled
                        if subscription.cancel_at_period_end:
                            subscription.status = 'cancelled'
                            logger.info(f"Subscription {subscription.id} marked as cancelled (cancel_at_period_end=True)")
                        else:
                            # Check if we've been trying to renew (having recent failed payments)
                            recent_failed_payment = Payment.query.filter(
                                Payment.subscription_id == subscription.id,
                                Payment.status == 'failed',
                                Payment.created_at > datetime.utcnow() - timedelta(days=7)
                            ).first()
                            
                            if recent_failed_payment:
                                # If we've been trying to renew, mark as payment_failed
                                subscription.status = 'payment_failed'
                                logger.info(f"Subscription {subscription.id} marked as payment_failed")
                            else:
                                # Otherwise mark as expired
                                subscription.status = 'expired'
                                logger.info(f"Subscription {subscription.id} marked as expired")
                        
                        db.session.commit()
                        
                        # Send expiration notification
                        user = User.query.get(subscription.user_id)
                        if user and user.email:
                            email_service.send_subscription_expired_email(
                                user.email,
                                user.first_name,
                                subscription.status
                            )
                            logger.info(f"Sent expiration email to {user.email} for subscription {subscription.id}")
                            
                    except Exception as e:
                        db.session.rollback()
                        logger.exception(f"Error processing expiration for subscription {subscription.id}: {e}")
                        
        except Exception as e:
            logger.exception(f"Error in expire_subscriptions: {e}")

# Create singleton instance
subscription_scheduler = SubscriptionScheduler() 