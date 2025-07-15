import os
import random
import time
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

load_dotenv()
EMAIL_HOST = os.getenv("EMAIL_HOST") 
EMAIL_PORT = os.getenv("EMAIL_PORT") 
EMAIL_USER = os.getenv("EMAIL_USER")  
EMAIL_PASS = os.getenv("EMAIL_PASS")  
SENDER_EMAIL = os.getenv("SENDER_EMAIL") 

otp_storage = {}

def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def store_otp(user_identifier, otp, validity=300):
    expiry_time = time.time() + validity
    otp_storage[user_identifier] = (otp, expiry_time)
    print(f"✅ Stored OTP {otp} for {user_identifier}, expires at {expiry_time}")

def send_otp_email(receiver_email, otp):
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    msg['Subject'] = "Your OTP Code"
    body = otp
    msg.attach(MIMEText(body, 'plain'))

    try:
        port = int(EMAIL_PORT) if EMAIL_PORT else 587
        print(f" Connecting to SMTP server {EMAIL_HOST}:{port} as {EMAIL_USER}")

        if port == 465:
            server = smtplib.SMTP_SSL(EMAIL_HOST, port)
        else:
            server = smtplib.SMTP(EMAIL_HOST, port)
            server.ehlo()
            server.starttls()
            server.ehlo()

        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        server.quit()
        print(f" OTP sent successfully to {receiver_email}")
        return True, "OTP sent successfully."

    except smtplib.SMTPAuthenticationError as e:
        error_message = f" Authentication Error: {e.smtp_error.decode() if hasattr(e, 'smtp_error') else e}"
        print(error_message)
        return False, error_message
    except smtplib.SMTPConnectError as e:
        error_message = f" Connection Error: {e}"
        print(error_message)
        return False, error_message
    except smtplib.SMTPRecipientsRefused as e:
        error_message = f" Recipient refused: {e.recipients}"
        print(error_message)
        return False, error_message
    except smtplib.SMTPException as e:
        error_message = f" SMTP Error: {e}"
        print(error_message)
        return False, error_message
    except Exception as e:
        error_message = f" Unexpected error: {e}"
        print(error_message)
        return False, error_message


def verify_otp(user_identifier, input_otp):
    stored = otp_storage.get(user_identifier)
    if not stored:
        return False, 

    otp, expiry = stored
    if time.time() > expiry:
        del otp_storage[user_identifier]
        return False, 
    if otp != input_otp:
        return False, 

    # OTP verified; remove it
    del otp_storage[user_identifier]
    return True, 

if __name__ == "__main__":
    test_email = input("Enter test receiver email: ").strip()
    test_otp = generate_otp()
    store_otp(test_email, test_otp)
    if send_otp_email(test_email, test_otp):
        print("Test OTP email sent.")
    else:
        print("Failed to send test OTP email.")
