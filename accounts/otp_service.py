import random
from twilio.rest import Client
from django.conf import settings
import random
import time
from django.core.cache import cache

OTP_EXPIRATION_TIME = 300  # 5 minutes
MAX_OTP_ATTEMPTS = 3

otp_storage = {}

def send_otp(phone_number):
    otp = random.randint(100000, 999999)
    cache.set(f"otp_{phone_number}", otp, timeout=OTP_EXPIRATION_TIME)
    cache.set(f"otp_attempts_{phone_number}", 0, timeout=OTP_EXPIRATION_TIME)
    # Integrate with SMS gateway like Twilio
    print(f"Sending OTP {otp} to {phone_number}")
    return otp

def verify_otp(phone_number, otp):
    cached_otp = cache.get(f"otp_{phone_number}")
    if not cached_otp:
        return False, "OTP has expired."

    # Check OTP retry attempts
    attempts = cache.get(f"otp_attempts_{phone_number}")
    if attempts is None:
        attempts = 0

    if attempts >= MAX_OTP_ATTEMPTS:
        return False, "Maximum retry attempts exceeded."

    if str(cached_otp) == str(otp):
        cache.delete(f"otp_{phone_number}")  # OTP is valid, so delete it
        return True, "OTP verified successfully."
    else:
        # Increment OTP attempts count
        cache.incr(f"otp_attempts_{phone_number}")
        return False, "Invalid OTP. Please try again."



def send_sms(phone_number, message):
    # Twilio credentials from settings.py
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    client = Client(account_sid, auth_token)

    # Twilio sending SMS
    try:
        message = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,  # Twilio registered phone number
            to=phone_number
        )
        print(f"SMS sent successfully to {phone_number}")
    except Exception as e:
        print(f"Error sending SMS: {e}")
