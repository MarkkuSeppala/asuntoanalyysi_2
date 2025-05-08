import os
import json
import requests
import uuid
import hmac
import hashlib
from datetime import datetime
from flask import url_for, current_app
import logging

logger = logging.getLogger(__name__)

# Paytrail test credentials
MERCHANT_ID = "375917"
SECRET_KEY = "SAIPPUAKAUPPIAS"

# API URLs
API_ENDPOINT = "https://services.paytrail.com"

def calculate_hmac(service_payload, api_key, params=None, body=None):
    """
    Calculate HMAC for Paytrail API request
    """
    logger.info("Calculating HMAC signature for Paytrail request")
    
    # Get current timestamp in ISO format
    timestamp = datetime.utcnow().isoformat()
    
    # Generate a unique nonce (UUID)
    nonce = str(uuid.uuid4())
    
    # Prepare headers for the request
    headers = {
        "checkout-account": MERCHANT_ID,
        "checkout-algorithm": "sha256",
        "checkout-method": "POST",
        "checkout-nonce": nonce,
        "checkout-timestamp": timestamp
    }
    
    # Add amount if provided (in params)
    if params and "amount" in params:
        headers["checkout-amount"] = str(params["amount"])
    
    # Create the string to sign
    # First collect all the headers in alphabetical order
    header_keys = sorted(headers.keys())
    
    parts = []
    # Add headers in sorted order
    for key in header_keys:
        parts.append(f"{key}:{headers[key]}")
    
    # Add line feeds between parts
    string_to_sign = "\n".join(parts)
    
    # Add the request body if it exists
    if body:
        string_to_sign += "\n" + body
    
    # Create hmac
    hmac_obj = hmac.new(SECRET_KEY.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256)
    calculated_hmac = hmac_obj.hexdigest()
    
    # Debug log
    logger.info("=== HMAC CALCULATION DETAILS ===")
    logger.info(f"Headers used:")
    for key in header_keys:
        logger.info(f"  {key}: {headers[key]}")
    logger.info(f"String to sign (length: {len(string_to_sign)}):")
    logger.info("--- START STRING TO SIGN ---")
    logger.info(string_to_sign)
    logger.info("--- END STRING TO SIGN ---")
    logger.info(f"Calculated HMAC: {calculated_hmac}")
    logger.info("=== END HMAC CALCULATION ===")
    
    # Return both the calculated HMAC and the headers used
    return {
        "signature": calculated_hmac,
        "headers": headers
    }

def create_payment(user_id, product, redirect_url_base):
    """
    Create a payment using Paytrail API
    """
    try:
        # Format price as integer (cents)
        price_in_cents = int(float(product.price) * 100)
        
        # Debug log
        logger.info(f"Creating payment for user {user_id}, product {product.id}, price {product.price}€ ({price_in_cents} cents)")
        logger.info(f"Redirect base URL: {redirect_url_base}")

        # Create a unique stamp for this payment
        stamp = f"asuntoanalyysi-{int(datetime.now().timestamp())}-{uuid.uuid4()}"
        logger.info(f"Generated payment stamp: {stamp}")

        # Create payment request payload
        payload = {
            "stamp": stamp,
            "reference": f"user-{user_id}-product-{product.id}",
            "amount": price_in_cents,
            "currency": "EUR",
            "language": "FI",
            "items": [
                {
                    "unitPrice": price_in_cents,
                    "units": 1,
                    "vatPercentage": 24,
                    "productCode": f"product-{product.id}",
                    "description": product.name,
                    "deliveryDate": datetime.now().strftime("%Y-%m-%d")
                }
            ],
            "customer": {
                "email": ""  # Will be filled by Paytrail's form
            },
            "redirectUrls": {
                "success": f"{redirect_url_base}{url_for('payment_success')}",
                "cancel": f"{redirect_url_base}{url_for('payment_cancel')}"
            },
            "callbackUrls": {
                "success": f"{redirect_url_base}{url_for('payment_callback_success')}",
                "cancel": f"{redirect_url_base}{url_for('payment_callback_cancel')}"
            }
        }

        # Debug log
        logger.info(f"Payment payload: {json.dumps(payload, indent=2)}")
        logger.info(f"Redirect URLs: success={payload['redirectUrls']['success']}, cancel={payload['redirectUrls']['cancel']}")
        logger.info(f"Callback URLs: success={payload['callbackUrls']['success']}, cancel={payload['callbackUrls']['cancel']}")

        # Convert to JSON
        body = json.dumps(payload)
        
        # Calculate HMAC
        hmac_data = calculate_hmac("/payments", SECRET_KEY, params={"amount": price_in_cents}, body=body)
        
        # Headers for the request - using Paytrail's required format
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "signature": hmac_data["signature"]
        }
        
        # Add all headers from hmac_data
        headers.update(hmac_data["headers"])
        
        # Debug log
        logger.info(f"Request headers: {json.dumps(headers, indent=2)}")
        
        # Make the API request
        url = f"{API_ENDPOINT}/payments"
        logger.info(f"Making API request to: {url}")
        
        try:
            logger.info("Sending request to Paytrail API...")
            response = requests.post(url, headers=headers, data=body, timeout=30)
            
            # Debug log response
            logger.info(f"API Response status: {response.status_code}")
            logger.info(f"API Response content: {response.text[:1000]}")  # Log first 1000 chars to avoid huge logs
            
            # Check response
            if response.status_code == 200 or response.status_code == 201:
                response_data = response.json()
                logger.info(f"Payment created: {response_data['transactionId']}")
                logger.info(f"Payment URL: {response_data['href']}")
                return {
                    "success": True,
                    "transaction_id": response_data['transactionId'],
                    "payment_url": response_data['href'],
                    "provider_form": response_data.get('providers', []),
                    "reference": payload["reference"],
                    "stamp": payload["stamp"]
                }
            else:
                logger.error(f"Error creating payment: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Payment API error: {response.status_code} - {response.text}"
                }
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Request failed: {req_error}")
            return {
                "success": False,
                "error": f"Connection error: {req_error}"
            }
    
    except Exception as e:
        logger.exception(f"Error creating payment: {e}")
        return {
            "success": False,
            "error": str(e)
        }
        
def verify_payment_signature(params):
    """
    Verify the signature of a payment callback
    """
    try:
        # Debug log
        logger.info(f"Verifying payment signature with params: {params}")
        
        # Get signature from params
        signature = params.get("signature")
        if not signature:
            logger.error("Missing signature in callback params")
            return False
            
        # Build string to sign from params
        # Paytrail uses specific order for params in signature calculation
        checkout_params = [
            "checkout-account",
            "checkout-algorithm",
            "checkout-amount",
            "checkout-stamp",
            "checkout-reference",
            "checkout-transaction-id",
            "checkout-status"
        ]
        
        # Create the string to sign
        string_to_sign = ""
        for param in checkout_params:
            if param in params:
                string_to_sign += params[param] + "+"
        
        # Remove last +
        string_to_sign = string_to_sign[:-1]
        
        # Debug log
        logger.info(f"String to sign: {string_to_sign}")
        
        # Calculate HMAC
        hmac_obj = hmac.new(SECRET_KEY.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha256)
        calculated_hmac = hmac_obj.hexdigest().upper()
        
        # Debug log
        logger.info(f"Calculated HMAC: {calculated_hmac}")
        logger.info(f"Provided signature: {signature}")
        
        # Compare calculated HMAC with the one from params
        result = calculated_hmac == signature.upper()
        logger.info(f"Signature verification result: {result}")
        
        return result
    
    except Exception as e:
        logger.exception(f"Error verifying payment signature: {e}")
        return False 