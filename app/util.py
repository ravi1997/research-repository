		
# UTILS
from datetime import datetime, timedelta
from functools import reduce
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
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.backends import default_backend
import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import xml.etree.ElementTree as ET

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

def getNewSalt(length: int = 16) -> str:
	characters = string.ascii_letters + string.digits
	salt = ''.join(secrets.choice(characters) for _ in range(length))
	return salt


def setCookie(response,name,value,httponly=True):
	response.set_cookie(name,value, httponly=httponly, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  

def hash_salt(salt: str) -> str:
	# Encode the salt and generate SHA-256 hash
	hash_object = hashlib.sha256(salt.encode('UTF-8'))
	# Convert to hexadecimal format
	return hash_object.hexdigest()

def decipher(salt: str):
	# Get the hashed salt
	hashed_salt = hash_salt(salt)
	
	# Function to convert text to char codes
	def text_to_chars(text):
		return [ord(c) for c in text]
	
	# Apply the hashed salt to the character code
	def apply_salt_to_char(code):
		# Reduce the XOR operation across all characters in the hashed salt
		return reduce(lambda a, b: a ^ b, text_to_chars(hashed_salt), code)
	
	# The main decode function
	def decode(encoded: str) -> str:
		# Split the encoded string into hex pairs and convert to integers
		chars = [int(encoded[i:i+2], 16) for i in range(0, len(encoded), 2)]
		# Apply salt to each char code and convert back to characters
		decoded_chars = [chr(apply_salt_to_char(char_code)) for char_code in chars]
		return ''.join(decoded_chars)
	
	return decode

# Example function to decode text
def decode_text(salt: str, encoded: str) -> str:
	decode_function = decipher(salt)
	return decode_function(encoded)


def risFileReader(filepath):
	articles = []

	with open(filepath, 'r',encoding='UTF-8') as bibliography_file:    
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
		
def download_xml(pmid, filename):
	# Construct the URL for the E-utilities API
	url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}"
	
	# Send a GET request to fetch the content
	response = requests.get(url)
	
	# Check if the request was successful
	if response.status_code == 200:
		# Write the content to a .nbib file
		with open(filename, 'w', encoding='utf-8') as file:
			file.write(response.content.decode('UTF-8'))
		app.logger.info(f"Downloaded {filename} successfully.")
	else:
		app.logger.error(f"Failed to download. HTTP Status Code: {response.status_code}")

	return response.status_code == 200
	
def parse_pubmed_xml(file_path):
	tree = ET.parse(file_path)
	root = tree.getroot()
		
	article = root.find("PubmedArticle")
	article_data = {
		"uuid":str(uuid.uuid4())
	}
	article_data["publication_types"] = [{"publication_type":pubType.text} for pubType in article.findall(".//PublicationTypeList/PublicationType")]

	# Extract Keywords
	article_data["keywords"] = [{"keyword":pubType.text} for pubType in article.findall(".//Keyword")]


	# Extract Authors
	authors = []
	for idx,author in enumerate(article.findall(".//Author")):
		last_name = author.find("LastName").text
		fore_name = author.find("ForeName").text
		initials = author.find("Initials").text
		affiliations = [affiliation.text for affiliation in author.findall(".//AffiliationInfo/Affiliation")]
		authors.append(
			{
				'fullName':f"{last_name}, {fore_name}",
				'author_abbreviated':f"{last_name} {initials}",
				'affiliations':affiliations,
				"sequence_number":idx + 1
			}    
		)
	article_data["authors"] = authors

	article_data["title"] = article.find(".//ArticleTitle").text
	article_data["abstract"] = article.find(".//Abstract/AbstractText").text
	pub_year = article.find(".//PubDate/Year").text
	pub_month = article.find(".//PubDate/Month").text
	pub_date = f"{pub_year} {pub_month}"
	article_data["publication_date"] = datetime.strptime(pub_date, "%Y %b").isoformat()
	article_data["place_of_publication"] = article.find(".//MedlineJournalInfo/Country").text
	article_data["journal"] = article.find(".//Journal/Title").text
	article_data["journal_abrevated"] = article.find(".//ISOAbbreviation").text
	article_data["pages"] = article.find(".//Pagination/MedlinePgn").text
	article_data["journal_volume"] = article.find(".//JournalIssue/Volume").text
	article_data["journal_issue"] = article.find(".//JournalIssue/Issue").text
	article_data["pubmed_id"] = article.find(".//PMID").text

	# Extract Article IDs (PubMed, DOI, PMC, etc.)
	for article_id in article.findall(".//ArticleId"):
		id_type = article_id.get("IdType")
		if id_type == "doi":
			article_data["doi"] = article_id.text
		elif id_type == "pmc":
			article_data["pmc_id"] = article_id.text
		elif id_type == "pii":
			article_data["pii"] = article_id.text

	issn = article.find(".//Journal/ISSN")
	IssnType = issn.get("IssnType")
	if IssnType == "Electronic":
		article_data["electronic_issn"]=issn.text
	
	article_data["linking_issn"] = article.find(".//ISSNLinking").text
	article_data["nlm_journal_id"] = article.find(".//NlmUniqueID").text
	article_data["links"] = []

	return article_data