import unittest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

# Importaa testattava moduuli
from subscription_service import SubscriptionService

class TestSubscriptionService(unittest.TestCase):
    
    @patch('subscription_service.db')
    @patch('subscription_service.Subscription')
    @patch('subscription_service.Payment')
    @patch('subscription_service.Product')
    def test_create_subscription(self, mock_product, mock_payment, mock_subscription, mock_db):
        # Mockaa kyselyn tulokset
        mock_subscription.query.filter_by.return_value.first.return_value = None
        
        # Mockaa uusi tilaus
        mock_new_subscription = Mock()
        mock_new_subscription.id = 1
        
        # Aseta mock luomaan uusi tilausobjekti kun sitä kutsutaan
        mock_subscription.return_value = mock_new_subscription
        
        # Mockaa maksu
        mock_payment_obj = Mock()
        mock_payment_obj.transaction_id = "test_transaction_123"
        
        # Testaa
        result = SubscriptionService.create_subscription(
            user_id=123,
            product_id=456,
            payment=mock_payment_obj,
            is_trial=False,
            days=30
        )
        
        # Varmista tulokset
        self.assertEqual(result, mock_new_subscription)
        mock_db.session.add.assert_called_once_with(mock_new_subscription)
        mock_db.session.commit.assert_called_once()
        
        # Varmista tilaus-objektin luomiskutsun parametrit
        args, kwargs = mock_subscription.call_args
        self.assertEqual(kwargs['user_id'], 123)
        self.assertEqual(kwargs['product_id'], 456)
        self.assertEqual(kwargs['subscription_type'], 'monthly')
        self.assertEqual(kwargs['status'], 'active')
        self.assertEqual(kwargs['payment_id'], "test_transaction_123")

    @patch('subscription_service.db')
    @patch('subscription_service.Subscription')
    def test_cancel_subscription(self, mock_subscription, mock_db):
        # Mockaa subscription
        mock_sub = Mock()
        mock_sub.id = 1
        
        # Aseta mock palauttamaan tämä objekti kun .get() kutsutaan
        mock_subscription.query.get.return_value = mock_sub
        
        # Testaa välitön peruutus
        result = SubscriptionService.cancel_subscription(1, immediate=True)
        
        # Varmista tulokset
        self.assertTrue(result)
        self.assertEqual(mock_sub.status, 'cancelled')
        self.assertIsNotNone(mock_sub.expires_at)
        mock_db.session.commit.assert_called_once()
        
        # Resetoi mockit
        mock_db.reset_mock()
        
        # Testaa kauden lopussa peruutus
        result = SubscriptionService.cancel_subscription(1, immediate=False)
        
        # Varmista tulokset
        self.assertTrue(result)
        self.assertTrue(mock_sub.cancel_at_period_end)
        mock_db.session.commit.assert_called_once()

    @patch('subscription_service.db')
    @patch('subscription_service.Subscription')
    def test_renew_subscription(self, mock_subscription, mock_db):
        # Mockaa subscription
        mock_sub = Mock()
        mock_sub.id = 1
        mock_sub.expires_at = datetime.utcnow() - timedelta(days=1)  # Mennyt vanhenemispäivä
        
        # Aseta mock palauttamaan tämä objekti kun .get() kutsutaan
        mock_subscription.query.get.return_value = mock_sub
        
        # Mockaa maksu
        mock_payment = Mock()
        mock_payment.transaction_id = "test_transaction_456"
        
        # Testaa
        result = SubscriptionService.renew_subscription(1, payment=mock_payment, days=30)
        
        # Varmista tulokset
        self.assertTrue(result)
        self.assertEqual(mock_sub.status, 'active')
        self.assertFalse(mock_sub.cancel_at_period_end)
        self.assertEqual(mock_sub.payment_id, "test_transaction_456")
        mock_db.session.commit.assert_called_once()

    @patch('subscription_service.paytrail_service')
    @patch('subscription_service.db')
    @patch('subscription_service.Subscription')
    @patch('subscription_service.Payment')
    @patch('subscription_service.Product')
    def test_process_recurring_payment(self, mock_product, mock_payment, mock_subscription, mock_db, mock_paytrail):
        # Mockaa subscription
        mock_sub = Mock()
        mock_sub.id = 1
        mock_sub.user_id = 123
        mock_sub.product_id = 456
        
        # Mockaa product
        mock_product_obj = Mock()
        mock_product_obj.id = 456
        mock_product_obj.price = 9.90
        
        # Aseta mockit palauttamaan nämä objektit kun niitä kutsutaan
        mock_subscription.query.get.return_value = mock_sub
        mock_product.query.get.return_value = mock_product_obj
        
        # Mockaa uusi maksu
        mock_payment_obj = Mock()
        mock_payment_obj.id = 789
        mock_payment.return_value = mock_payment_obj
        
        # Mockaa Paytrail-vastaus
        mock_paytrail.create_payment.return_value = {
            "success": True,
            "transaction_id": "test_tx_789",
            "payment_url": "https://test.paytrail.com/pay/123",
            "stamp": "stamp123",
            "reference": "ref123"
        }
        
        # Testaa
        result = SubscriptionService.process_recurring_payment(1, redirect_url_base="https://example.com")
        
        # Varmista tulokset
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_id"], "test_tx_789")
        self.assertEqual(result["payment_url"], "https://test.paytrail.com/pay/123")
        
        # Varmista että maksu luodaan oikein
        mock_payment.assert_called_once()
        args, kwargs = mock_payment.call_args
        self.assertEqual(kwargs['user_id'], 123)
        self.assertEqual(kwargs['product_id'], 456)
        self.assertEqual(kwargs['subscription_id'], 1)
        self.assertEqual(kwargs['amount'], 9.90)
        self.assertEqual(kwargs['payment_method'], 'paytrail')
        self.assertEqual(kwargs['status'], 'pending')
        
        # Varmista että maksua päivitetään Paytrailin transaction_id:llä
        self.assertEqual(mock_payment_obj.transaction_id, "test_tx_789")
        mock_db.session.commit.assert_called()

if __name__ == '__main__':
    unittest.main()