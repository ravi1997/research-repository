		
# UTILS
import base64
from datetime import datetime, timedelta
import random
import string
import requests
from app.extension import bcrypt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from flask import current_app as app
import rispy

from app.models import Article




def generate_otp(length=6):
    """Generate a random OTP of specified length."""
    digits = '0123456789'
    otp = ''.join(random.choice(digits) for _ in range(length))
    return otp

def send_sms(mobile,message):
    # Data for the POST request
    data = {
        'username': app.config.get('OTP_USERNAME'),
        'password': app.config.get('OTP_PASSWORD'),
        'senderid': app.config.get('OTP_SENDERID'),
        'mobileNos': mobile,
        'message': f'{message}',
        'templateid1': app.config.get('OTP_ID')
    }

    # Headers for the POST request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # URL of the service
    url = app.config.get('OTP_SERVER')
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




def risFileReader(filepath,my_author):
    articles = []

    with open(filepath, 'r') as bibliography_file:    
        entries = rispy.load(bibliography_file)


        for entry in entries:
            
            publication_type = ['JOURNAL']
            keywords = entry.get('keywords',None) or []
            author_list = (entry.get('authors',None) or [])+(entry.get('first_authors',None) or [])
            
            authors = [{"fullName": author,"sequence_number":idx+1} for idx, author in enumerate(author_list)]
            
            title = entry.get('title',None) or entry.get('primary_title',None)
            abstract = entry.get('abstract',None)

            place_of_publication = entry.get('place_published',None)
            journal = entry.get('journal',None) or entry.get('journal_name',None) or entry.get('secondary_title',None)

            journal_abrevated = entry.get('alternate_title1',None)
            pub_date = entry.get('date',None)
            
            
            if pub_date:
                dateSplit = pub_date.split('/')
                year = int(dateSplit[0])
                month = int(dateSplit[1]) if dateSplit[1] != '' else 1
                day = int(dateSplit[2]) if dateSplit[2] != '' else 1
                publication_date = datetime(year,month,day,0,0)
                print(dateSplit)
            
            
            start_page = entry.get('start_page',None)
            end_page = entry.get('end_page',None)
            pages = None
            if start_page is not None and end_page is not None:
                pages =  f'{start_page}-{end_page}'

            journal_volume = entry.get('volume',None)
            journal_issue = entry.get('number',None)
            
            pubmed_id = entry.get('pubmed_id',None)
            pmc_id = entry.get('pmc_id',None)
            pii = entry.get('pii',None)
            doi = entry.get('doi',None)
            print_issn = entry.get('print_issn',None) or entry.get('issn',None)
            electronic_issn = entry.get('electronic_issn',None)
            linking_issn = entry.get('linking_issn',None)
            nlm_journal_id = entry.get('nlm_journal_id',None)
        
        
            file_attachments1 = entry.get('file_attachments1',None)
            file_attachments2 = entry.get('file_attachments2',None)
            urls = entry.get('urls',None)
        
            links = []
            
            if file_attachments1 is not None:
                links.append(file_attachments1)

            if file_attachments2 is not None:
                links.append(file_attachments2)

            links += (urls or [])

            
            if entry['type_of_reference'] == 'JOUR' and next((item for item in authors if item["fullName"] == my_author), None) is not None and journal is not None:
                article = {
                    "keywords":keywords,
                    "authors":authors,
                    "title":title,
                    "abstract":abstract,
                    "place_of_publication":place_of_publication,
                    "journal":journal,
                    "journal_abrevated":journal_abrevated,
                    "publication_date":publication_date,
                    "pages":pages,
                    "journal_volume":journal_volume,
                    "number":journal_issue,
                    "pubmed_id":pubmed_id,
                    "pmc_id":pmc_id,
                    "pii":pii,
                    "doi":doi,
                    "print_issn":print_issn,
                    "electronic_issn":electronic_issn,
                    "linking_issn":linking_issn,
                    "nlm_journal_id":nlm_journal_id,
                    "links":links
                }
                articles.append(article)
                
    return articles



