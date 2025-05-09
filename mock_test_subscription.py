import unittest
from unittest.mock import patch, MagicMock
import sys

# Mockaa app ja db moduulit
mock_app = MagicMock()
mock_db = MagicMock()
sys.modules['app'] = mock_app
sys.modules['app.db'] = mock_db

# Mockaa muut moduulit
mock_subscription = MagicMock()
mock_user = MagicMock()
mock_payment = MagicMock()
mock_product = MagicMock()
sys.modules['models'] = MagicMock()
sys.modules['models'].Subscription = mock_subscription
sys.modules['models'].User = mock_user
sys.modules['models'].Payment = mock_payment
sys.modules['models'].Product = mock_product

# Mockaa subscription_service
mock_subscription_service = MagicMock()
sys.modules['subscription_service'] = MagicMock()
sys.modules['subscription_service'].subscription_service = mock_subscription_service

# Mockaa subscription_scheduler
mock_subscription_scheduler = MagicMock()
sys.modules['subscription_scheduler'] = MagicMock()
sys.modules['subscription_scheduler'].subscription_scheduler = mock_subscription_scheduler

# Importaa testattavat CLI-funktiot itse tiedostosta 
# ilman että ajamme koko moduulin
with open('subscription_cli.py', 'r') as f:
    subscription_cli_code = f.read()

# Etsi funktioiden määrittelyt koodista
import re

list_subscriptions_code = re.search(r'def list_subscriptions\(.*?\):(.*?)def', subscription_cli_code, re.DOTALL).group(1)
renew_subscription_code = re.search(r'def renew_subscription\(.*?\):(.*?)def', subscription_cli_code, re.DOTALL).group(1)
cancel_subscription_code = re.search(r'def cancel_subscription\(.*?\):(.*?)def', subscription_cli_code, re.DOTALL).group(1)

# Luo funktiot uudelleen
exec(f'''
def list_subscriptions(args):
    """List all active subscriptions"""
{list_subscriptions_code}

def renew_subscription(args):
    """Manually renew a subscription"""
{renew_subscription_code}

def cancel_subscription(args):
    """Cancel a subscription"""
{cancel_subscription_code}
''')

class TestSubscriptionCLI(unittest.TestCase):
    
    def test_list_subscriptions_empty(self):
        # Mockaa query-tulokset
        mock_subscription.query.filter_by.return_value.all.return_value = []
        
        # Mockaa argumentit
        args = MagicMock()
        args.status = None
        
        # Kaappaa print-funktio
        with patch('builtins.print') as mock_print:
            # Kutsu testattavaa funktiota
            list_subscriptions(args)
            # Tarkista, että oikea viesti näytetään
            mock_print.assert_any_call("No subscriptions found.")
            
    def test_list_subscriptions_with_data(self):
        # Luo testidata
        mock_sub1 = MagicMock()
        mock_sub1.id = 1
        mock_sub1.user_id = 123
        mock_sub1.status = 'active'
        mock_sub1.subscription_type = 'monthly'
        mock_sub1.expires_at = None
        mock_sub1.next_billing_date = None
        
        # Mockaa query-tulokset
        mock_subscription.query.filter_by.return_value.all.return_value = [mock_sub1]
        
        # Mockaa argumentit
        args = MagicMock()
        args.status = 'active'
        
        # Kaappaa print-funktio
        with patch('builtins.print') as mock_print:
            # Kutsu testattavaa funktiota
            list_subscriptions(args)
            # Tarkista, että oikea viesti näytetään
            mock_print.assert_any_call("Found 1 subscriptions:")
            
    def test_renew_subscription(self):
        # Mockaa subscription-objekti
        mock_sub = MagicMock()
        mock_sub.id = 1
        mock_subscription.query.get.return_value = mock_sub
        
        # Mockaa subscription service -funktio
        mock_subscription_service.renew_subscription.return_value = True
        
        # Mockaa argumentit
        args = MagicMock()
        args.subscription_id = 1
        args.days = 30
        
        # Kaappaa print-funktio
        with patch('builtins.print') as mock_print:
            # Kutsu testattavaa funktiota
            renew_subscription(args)
            # Tarkista, että service-funktiota kutsuttiin oikeilla parametreilla
            mock_subscription_service.renew_subscription.assert_called_with(1, days=30)
            # Tarkista, että onnistumisviesti näytetään
            mock_print.assert_any_call(f"Successfully renewed subscription 1 for 30 days.")
    
    def test_cancel_subscription(self):
        # Mockaa subscription-objekti
        mock_sub = MagicMock()
        mock_sub.id = 1
        mock_subscription.query.get.return_value = mock_sub
        
        # Mockaa subscription service -funktio
        mock_subscription_service.cancel_subscription.return_value = True
        
        # Mockaa argumentit
        args = MagicMock()
        args.subscription_id = 1
        args.immediate = True
        
        # Kaappaa print-funktio
        with patch('builtins.print') as mock_print:
            # Kutsu testattavaa funktiota
            cancel_subscription(args)
            # Tarkista, että service-funktiota kutsuttiin oikeilla parametreilla
            mock_subscription_service.cancel_subscription.assert_called_with(1, immediate=True)
            # Tarkista, että onnistumisviesti näytetään
            mock_print.assert_any_call(f"Successfully cancelled subscription 1 immediately.")

if __name__ == '__main__':
    unittest.main()
