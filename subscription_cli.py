"""
Command-line utility for subscription management and scheduling.
This script provides commands for managing subscriptions and
running the recurring payment scheduler.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/subscription_cli.log')
    ]
)
logger = logging.getLogger(__name__)

# Add the current directory to sys.path to allow importing the application modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import Flask app and models after setting up path
from app import app, db
from models import Subscription, User, Payment, Product
from subscription_service import subscription_service
from subscription_scheduler import subscription_scheduler

def list_subscriptions(args):
    """List all active subscriptions"""
    with app.app_context():
        if args.status:
            subscriptions = Subscription.query.filter_by(status=args.status).all()
        else:
            subscriptions = Subscription.query.all()
            
        if not subscriptions:
            print("No subscriptions found.")
            return
            
        print(f"Found {len(subscriptions)} subscriptions:")
        print("-" * 80)
        print(f"{'ID':<5} {'User ID':<8} {'Status':<10} {'Type':<10} {'Expires':<20} {'Next Billing':<20}")
        print("-" * 80)
        
        for sub in subscriptions:
            expires_at = sub.expires_at.strftime("%Y-%m-%d %H:%M") if sub.expires_at else "N/A"
            next_billing = sub.next_billing_date.strftime("%Y-%m-%d %H:%M") if sub.next_billing_date else "N/A"
            print(f"{sub.id:<5} {sub.user_id:<8} {sub.status:<10} {sub.subscription_type:<10} {expires_at:<20} {next_billing:<20}")

def renew_subscription(args):
    """Manually renew a subscription"""
    with app.app_context():
        try:
            subscription = Subscription.query.get(args.subscription_id)
            if not subscription:
                print(f"Subscription ID {args.subscription_id} not found.")
                return
                
            days = args.days if args.days else 30
            
            result = subscription_service.renew_subscription(subscription.id, days=days)
            if result:
                print(f"Successfully renewed subscription {subscription.id} for {days} days.")
                print(f"New expiration date: {subscription.expires_at.strftime('%Y-%m-%d %H:%M')}")
            else:
                print(f"Failed to renew subscription {subscription.id}.")
                
        except Exception as e:
            print(f"Error: {e}")

def cancel_subscription(args):
    """Cancel a subscription"""
    with app.app_context():
        try:
            subscription = Subscription.query.get(args.subscription_id)
            if not subscription:
                print(f"Subscription ID {args.subscription_id} not found.")
                return
                
            immediate = args.immediate if args.immediate else False
            
            result = subscription_service.cancel_subscription(subscription.id, immediate=immediate)
            if result:
                if immediate:
                    print(f"Successfully cancelled subscription {subscription.id} immediately.")
                else:
                    print(f"Subscription {subscription.id} will be cancelled at the end of the billing period.")
            else:
                print(f"Failed to cancel subscription {subscription.id}.")
                
        except Exception as e:
            print(f"Error: {e}")

def process_renewals(args):
    """Manually process subscription renewals"""
    with app.app_context():
        try:
            print("Processing subscription renewals...")
            subscription_scheduler.process_renewals()
            print("Renewal processing completed.")
        except Exception as e:
            print(f"Error processing renewals: {e}")

def run_scheduler(args):
    """Run the subscription scheduler"""
    try:
        print("Starting subscription scheduler...")
        subscription_scheduler.start()
        
        # Keep the scheduler running until interrupted
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping scheduler...")
            subscription_scheduler.stop()
            print("Scheduler stopped.")
            
    except Exception as e:
        print(f"Error running scheduler: {e}")

def check_expiring(args):
    """List subscriptions expiring soon"""
    with app.app_context():
        try:
            days = args.days if args.days else 7
            now = datetime.utcnow()
            cutoff_date = now + timedelta(days=days)
            
            expiring_subscriptions = Subscription.query.filter(
                Subscription.status == 'active',
                Subscription.expires_at <= cutoff_date,
                Subscription.expires_at > now
            ).all()
            
            if not expiring_subscriptions:
                print(f"No subscriptions expiring within the next {days} days.")
                return
                
            print(f"Found {len(expiring_subscriptions)} subscriptions expiring within the next {days} days:")
            print("-" * 80)
            print(f"{'ID':<5} {'User ID':<8} {'Status':<10} {'Expires':<20} {'Cancel at end':<15}")
            print("-" * 80)
            
            for sub in expiring_subscriptions:
                expires_at = sub.expires_at.strftime("%Y-%m-%d %H:%M") if sub.expires_at else "N/A"
                cancel_end = "Yes" if sub.cancel_at_period_end else "No"
                print(f"{sub.id:<5} {sub.user_id:<8} {sub.status:<10} {expires_at:<20} {cancel_end:<15}")
                
        except Exception as e:
            print(f"Error checking expiring subscriptions: {e}")

def main():
    """Main function for the CLI"""
    parser = argparse.ArgumentParser(description="Subscription management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List subscriptions
    list_parser = subparsers.add_parser("list", help="List subscriptions")
    list_parser.add_argument("--status", help="Filter by status (active, cancelled, expired)")
    list_parser.set_defaults(func=list_subscriptions)
    
    # Renew subscription
    renew_parser = subparsers.add_parser("renew", help="Renew a subscription")
    renew_parser.add_argument("subscription_id", type=int, help="Subscription ID to renew")
    renew_parser.add_argument("--days", type=int, help="Number of days to renew for (default: 30)")
    renew_parser.set_defaults(func=renew_subscription)
    
    # Cancel subscription
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a subscription")
    cancel_parser.add_argument("subscription_id", type=int, help="Subscription ID to cancel")
    cancel_parser.add_argument("--immediate", action="store_true", help="Cancel immediately instead of at period end")
    cancel_parser.set_defaults(func=cancel_subscription)
    
    # Process renewals
    process_parser = subparsers.add_parser("process", help="Process subscription renewals")
    process_parser.set_defaults(func=process_renewals)
    
    # Run scheduler
    scheduler_parser = subparsers.add_parser("run-scheduler", help="Run the subscription scheduler")
    scheduler_parser.set_defaults(func=run_scheduler)
    
    # Check expiring
    expiring_parser = subparsers.add_parser("expiring", help="List subscriptions expiring soon")
    expiring_parser.add_argument("--days", type=int, help="Number of days to look ahead (default: 7)")
    expiring_parser.set_defaults(func=check_expiring)
    
    # Parse arguments and call the appropriate function
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        return
        
    args.func(args)

if __name__ == "__main__":
    main() 