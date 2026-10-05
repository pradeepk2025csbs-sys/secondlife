"""
SECONDLIFE – Payment Processing Service
Handles Razorpay Order Creation, Verification, and Local Demo Mode Fallback.
"""

import os
import uuid
import time
import logging
from flask import current_app

logger = logging.getLogger(__name__)

try:
    import razorpay
    RAZORPAY_AVAILABLE = True
except ImportError:
    RAZORPAY_AVAILABLE = False
    logger.warning("Razorpay library not found. Running in simulated payment mode.")


def get_payment_config():
    """Retrieve Razorpay & payment configuration from Flask current_app or environment."""
    if current_app:
        key_id = current_app.config.get('RAZORPAY_KEY_ID') or os.environ.get('RAZORPAY_KEY_ID', '')
        key_secret = current_app.config.get('RAZORPAY_KEY_SECRET') or os.environ.get('RAZORPAY_KEY_SECRET', '')
        mode = (current_app.config.get('PAYMENT_MODE') or os.environ.get('PAYMENT_MODE', 'demo')).lower()
        commission_pct = current_app.config.get('PLATFORM_COMMISSION_PERCENTAGE', 5.0)
    else:
        key_id = os.environ.get('RAZORPAY_KEY_ID', '')
        key_secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
        mode = os.environ.get('PAYMENT_MODE', 'demo').lower()
        try:
            commission_pct = float(os.environ.get('PLATFORM_COMMISSION_PERCENTAGE', '5.0'))
        except ValueError:
            commission_pct = 5.0

    return {
        'key_id': key_id,
        'key_secret': key_secret,
        'mode': mode,
        'commission_pct': commission_pct
    }


def is_demo_mode():
    """Check if the payment service is running in simulated demo mode."""
    cfg = get_payment_config()
    if cfg['mode'] == 'demo':
        return True
    # If no valid keys are provided or keys are default placeholders
    if not cfg['key_id'] or not cfg['key_secret']:
        return True
    if 'your_key_id' in cfg['key_id'] or 'demo' in cfg['key_id'].lower():
        return True
    if not RAZORPAY_AVAILABLE:
        return True
    return False


def get_razorpay_client():
    """Return an authenticated Razorpay client instance, or None if in demo mode / unavailable."""
    if is_demo_mode() or not RAZORPAY_AVAILABLE:
        return None

    cfg = get_payment_config()
    try:
        client = razorpay.Client(auth=(cfg['key_id'], cfg['key_secret']))
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Razorpay client: {e}")
        return None


def create_payment_order(amount_inr, receipt=None, notes=None):
    """
    Creates a payment order.
    Returns a dict with order details ready for client-side Razorpay Checkout.
    If demo mode or live API unavailable, generates a valid simulated order.
    """
    amount_inr = float(amount_inr)
    # Razorpay expects amounts in paise (1 INR = 100 paise)
    amount_paise = int(round(amount_inr * 100))
    receipt = receipt or f"rcpt_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    notes = notes or {}

    client = get_razorpay_client()
    cfg = get_payment_config()

    if client and not is_demo_mode():
        try:
            data = {
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': receipt,
                'notes': notes,
                'payment_capture': 1
            }
            order = client.order.create(data=data)
            return {
                'id': order.get('id'),
                'amount': order.get('amount'),
                'amount_inr': amount_inr,
                'currency': order.get('currency', 'INR'),
                'receipt': receipt,
                'key_id': cfg['key_id'],
                'is_demo': False,
                'status': order.get('status', 'created')
            }
        except Exception as e:
            logger.warning(f"Razorpay live order creation failed: {e}. Falling back to demo mode order.")
            # Fall back to demo order gracefully if live call fails

    # Simulated Demo Mode Order
    demo_order_id = f"order_demo_{uuid.uuid4().hex[:14]}"
    return {
        'id': demo_order_id,
        'amount': amount_paise,
        'amount_inr': amount_inr,
        'currency': 'INR',
        'receipt': receipt,
        'key_id': cfg['key_id'] or 'rzp_demo_secondlife',
        'is_demo': True,
        'status': 'created'
    }


def verify_payment_signature(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verifies the payment signature returned by Razorpay Checkout.
    Returns (True, "Verified") on success, or (False, error_message) on failure.
    """
    if not razorpay_order_id or not razorpay_payment_id:
        return False, "Missing order ID or payment ID"

    # Handle demo mode or simulated orders
    if (
        is_demo_mode()
        or str(razorpay_order_id).startswith('order_demo_')
        or str(razorpay_signature).startswith('demo_sig_')
        or str(razorpay_payment_id).startswith('pay_demo_')
    ):
        # Demo verification succeeds as long as values are present
        if razorpay_order_id and razorpay_payment_id:
            return True, "Simulated payment verified successfully (Demo Mode)"
        return False, "Invalid simulated payment payload"

    client = get_razorpay_client()
    if not client:
        return False, "Razorpay client not configured for live verification"

    try:
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        client.utility.verify_payment_signature(params_dict)
        return True, "Payment signature verified successfully"
    except razorpay.errors.SignatureVerificationError as e:
        logger.error(f"Razorpay signature verification failed: {e}")
        return False, f"Signature verification failed: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error verifying payment: {e}")
        return False, f"Payment verification error: {str(e)}"


def calculate_platform_fees(total_amount):
    """
    Calculates platform commission and seller payout.
    Returns a dict with platform_fee, seller_amount, commission_pct.
    """
    cfg = get_payment_config()
    pct = cfg['commission_pct']
    platform_fee = round((total_amount * pct) / 100.0, 2)
    seller_amount = round(total_amount - platform_fee, 2)
    return {
        'total_amount': total_amount,
        'commission_pct': pct,
        'platform_fee': platform_fee,
        'seller_amount': seller_amount
    }
