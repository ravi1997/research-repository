		
# UTILS

import base64
from datetime import datetime, timedelta
import random
import string
import requests
from extension import bcrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    digits = '0123456789'
    otp = ''.join(random.choice(digits) for _ in range(length))
    return otp

def send_sms(mobile,message):
    # Data for the POST request
    data = {
        'username': 'Aiims',
        'password': 'Aiims@123',
        'senderid': 'AIIMSD',
        'mobileNos': mobile,
        'message': f'{message}',
        'templateid1': '1307161579789431013'
    }

    # Headers for the POST request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # URL of the service
    url = 'http://192.168.14.30/sms_service/Service.asmx/sendSingleSMS'

    # Send the POST request
    response = requests.post(url, data=data, headers=headers)

    # Return the response from the SMS service
    return response.status_code

def to_date(date_string): 
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError('{} is not valid date in the format YYYY-MM-DD'.format(date_string))

def randomword(length):
	letters = 'abcdefghijklmnopqrstuvwxyz'
	return ''.join(random.choice(letters) for i in range(length))

def generate_random_phone_number():
    # Generate a random 10-digit number (excluding any specific formatting)
    number = ''.join(random.choices('0123456789', k=10))
    
    # Format the number as a typical phone number (e.g., ###-###-####)
    formatted_number = f'{number[:3]}-{number[3:6]}-{number[6:]}'
    
    return formatted_number

def generate_random_dob(start_date='1970-01-01', end_date='2005-12-31'):
    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Calculate the range in days
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    
    # Generate a random date within the specified range
    random_dob = start_date + timedelta(days=random_days)
    
    return random_dob.date()

def generate_strong_password(length=10):
	# Define characters to use in the password
	characters = string.ascii_letters + string.digits + string.punctuation
	
	# Generate password
	password = ''.join(random.choice(characters) for _ in range(length))
	
	return password

def getNewSalt():
    return bcrypt.gensalt()

def derive_key(salt):
    secret_key = b'32_characters_long_key_here!!'    
    # Derive a key using the salt (this example uses a simple XOR for demonstration)
    derived_key = bytearray(secret_key)
    for i in range(len(derived_key)):
        derived_key[i] ^= salt[i % len(salt)]
    return bytes(derived_key)

def decrypt(encrypted_data,session):
    salt = base64.b64decode(session.salt)
    encrypted_data_bytes = base64.b64decode(encrypted_data)

    # Extract IV and ciphertext
    iv = encrypted_data_bytes[:16]  # The first 16 bytes are the IV
    ciphertext = encrypted_data_bytes[16:]  # The rest is the ciphertext

    # Derive the key using the salt
    derived_key = derive_key(salt)

    # Decrypt the data
    cipher = Cipher(algorithms.AES(derived_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding (PKCS7 padding)
    pad_len = decrypted_padded[-1]
    decrypted_data = decrypted_padded[:-pad_len].decode('utf-8')
    return decrypted_data