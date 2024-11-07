		
# UTILS
from datetime import datetime, timedelta
import random
import string
import requests
from flask import current_app as app
import rispy
import uuid
from app.models import Article
import secrets
import hashlib
from pprint import pprint
from nbib import read_file
import re
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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



def getNewSalt(length=16):
	# Generate a random salt with the specified byte length
	salt = secrets.token_bytes(length)
	# Convert to a hexadecimal string for easy storage
	return hashlib.sha256(salt).hexdigest()


def decrypt(encrypted_data,session,password = "my_secret_password"):
	salt = base64.b64decode(session.salt)  
	kdf = PBKDF2HMAC(
		algorithm=hashes.SHA256(),
		length=32,
		salt=salt,
		iterations=100000,
		backend=default_backend()
	)
	key = kdf.derive(password.encode())

	# Split the encrypted data into IV and ciphertext
	encrypted_data_bytes = base64.b64decode(encrypted_data)
	iv = encrypted_data_bytes[:16]  # First 16 bytes are the IV
	ciphertext = encrypted_data_bytes[16:]  # The rest is the ciphertext

	# Decrypt the data using AES in CBC mode
	cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
	decryptor = cipher.decryptor()
	decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()

	return decrypted_data.decode()




def risFileReader(filepath):
	articles = []

	with open(filepath, 'r') as bibliography_file:    
		entries = rispy.load(bibliography_file)


		for entry in entries:
			
			publication_type = ['JOURNAL']
			keyword_list = entry.get('keywords',None) or []
			keywords = []
			keywords += ({"keyword":keyword} for keyword in keyword_list)
			
			
			author_list = (entry.get('authors',None) or [])+(entry.get('first_authors',None) or [])
			
			authors = [{"fullName": author,"sequence_number":idx+1} for idx, author in enumerate(author_list)]
			
			
			title = entry.get('title',None) or entry.get('primary_title',None)
			abstract = entry.get('abstract',None)

			place_of_publication = entry.get('place_published',None)
			journal = entry.get('journal',None) or entry.get('journal_name',None) or entry.get('secondary_title',None)

			journal_abrevated = entry.get('alternate_title1',None)
			pub_date = entry.get('date',None)
			publication_year = entry.get('publication_year')
			
			
			publication_date = None
			if pub_date:
				dateSplit = pub_date.split('/')
				year = int(dateSplit[0])
				month = int(dateSplit[1]) if dateSplit[1] != '' else 1
				day = int(dateSplit[2]) if dateSplit[2] != '' else 1
				publication_date = datetime(year,month,day,0,0)
			elif publication_year:
				dateSplit = publication_year.split('/')
				# print(dateSplit)
				year = int(dateSplit[0])
				month = 1
				day = 1
				if len(dateSplit) > 1:
					month = int(dateSplit[1]) if dateSplit[1] != '' else 1
				if len(dateSplit)>2:
					day = int(dateSplit[2]) if dateSplit[2] != '' else 1
				publication_date = datetime(year,month,day,0,0)
				
			
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
				# print(file_attachments1)
				links.append(
					{
						"link":file_attachments1                        
					}
					
					)

			if file_attachments2 is not None:
				links.append(                    {
						"link":file_attachments2                        
					})

			if urls:
				links += ({"link": link} for link in urls)

			
			# print(entry['type_of_reference'] , journal , publication_date)
			
			if entry['type_of_reference'] == 'JOUR' and journal is not None and publication_date is not None:
				# print(json.dumps(links,indent=4))
				
				article = {
					"uuid":str(uuid.uuid4()),
					"keywords":keywords,
					"authors":authors,
					"title":title,
					"abstract":abstract,
					"publication_date":publication_date.isoformat(),
					"place_of_publication":place_of_publication,
					"journal":journal,
					"journal_abrevated":journal_abrevated,
					"pages":pages,
					"journal_volume":journal_volume,
					"journal_issue":journal_issue,
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


def parse_date(date_string):
	# Define regex patterns for each format
	patterns = [
		(r"^(\d{4}) (\w{3}) (\d{1,2})$", "%Y %b %d"),     # Format: "2024 Aug 19"
		(r"^(\d{4}) (\w{3})$", "%Y %b"),                   # Format: "2022 Mar"
		(r"^(\d{4}) (\w{3})-(\w{3})$", "%Y %b"),           # Format: "2019 Nov-Dec" (we'll handle end month separately)
		(r"^(\d{4})$", "%Y"),                              # Format: "2020"
	]
	
	for pattern, date_format in patterns:
		match = re.match(pattern, date_string)
		if match:
			if pattern == r"^(\d{4}) (\w{3})-(\w{3})$":
				year, start_month, end_month = match.groups()
				# Handle ranges by returning both start and end dates
				start_date = datetime.strptime(f"{year} {start_month}", "%Y %b")
				end_date = datetime.strptime(f"{year} {end_month}", "%Y %b")
				return start_date
			
			# For other patterns, parse normally
			return datetime.strptime(date_string, date_format)
	
	raise ValueError(f"Date format for '{date_string}' is not supported.")

def nbibFileReader(filepath):
	articles = []
	entries = read_file(filepath)

	for entry in entries:
		publication_type_list = entry.get('publication_types', None) or []
		publication_type = []
		publication_type += ({'publication_type':publication} for publication in publication_type_list)

		keyword_list = entry.get('descriptors', None) or []
		keywords = []
		keywords += ({"keyword":keyword['descriptor']} for keyword in keyword_list)
		author_list = (entry.get('authors', None) or [])
				
		authors = [{"fullName": author['author'], "author_abbreviated": author['author_abbreviated'], "affiliations": author['affiliations'], "sequence_number":idx + 1} for idx, author in enumerate(author_list)]
				
		title = entry.get('title', None) or entry.get('primary_title', None)
		abstract = entry.get('abstract', None)

		place_of_publication = entry.get('place_of_publication', None)
		journal = entry.get('journal', None) or entry.get('journal_name', None) or entry.get('secondary_title', None)

		journal_abrevated = entry.get('journal_abbreviated', None)
		pub_date = entry.get('publication_date', None)
		publication_date = (parse_date(pub_date) if pub_date else None)

		pages = entry.get('pages', None)

		journal_volume = entry.get('journal_volume', None)
		journal_issue = entry.get('journal_issue', None)
				
		pubmed_id = str(entry.get('pubmed_id', None))
		pmc_id = str(entry.get('pmcid', None))
		pii = entry.get('pii', None)
		doi = entry.get('doi', None)
		print_issn = entry.get('print_issn', None) or entry.get('issn', None)
		electronic_issn = entry.get('electronic_issn', None)
		linking_issn = entry.get('linking_issn', None)
		nlm_journal_id = entry.get('nlm_journal_id', None)
			
		file_attachments1 = entry.get('file_attachments1', None)
		file_attachments2 = entry.get('file_attachments2', None)
		urls = entry.get('urls', None)
			
		links = []
				
		if file_attachments1 is not None:
			# print(file_attachments1)
			links.append(
				{
					"link":file_attachments1                        
				}
						
				)

		if file_attachments2 is not None:
			links.append({
					"link":file_attachments2                        
				})

		if urls:
			links += ({"link": link} for link in urls)

		
		if 'Journal Article' in publication_type_list:
			article = {
				"uuid":str(uuid.uuid4()),
				"publication_types":publication_type,
				"keywords":keywords,
				"authors":authors,
				"title":title,
				"abstract":abstract,
				"publication_date":publication_date.isoformat(),
				"place_of_publication":place_of_publication,
				"journal":journal,
				"journal_abrevated":journal_abrevated,
				"pages":pages,
				"journal_volume":journal_volume,
				"journal_issue":journal_issue,
				"pubmed_id":pubmed_id,
				"pmc_id":pmc_id,
				"pii":pii,
				"doi":doi,
				"print_issn":print_issn,
				"linking_issn":linking_issn,
				"electronic_issn":electronic_issn,
				"nlm_journal_id":nlm_journal_id,
				"links":links
			}
			articles.append(article)

	return articles
		
