		
# UTILS
from datetime import date, datetime, timedelta
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

from urllib.parse import urlparse


def is_valid_url(url):
	parsed = urlparse(url)
	return all([parsed.scheme, parsed.netloc])


def getIP(request):
	x_forwarded_for = request.headers.get('X-Forwarded-For')
	if x_forwarded_for:
		# Take the first IP if there are multiple IPs listed
		client_ip = x_forwarded_for.split(',')[0]
	else:
		client_ip = request.remote_addr
	client = request.args.get('ip', client_ip, type=str)


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

def get_base_url():
	# Get the host and port from the app's configuration
	host = "127.0.0.1" # Default to localhost if not set
	port = app.config.get("PORT", 5000)  # Default port is 5000

	# Determine the scheme based on whether the app is running in debug mode or not
	scheme = "http"
	
	# Construct the base URL
	base_url = f"{scheme}://{host}:{port}/"
	return base_url

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


def find_full_row_match(cls,instance):
	# Create a filter expression dynamically based on the instance's attributes
	filters = {column.name: getattr(instance, column.name) for column in cls.__table__.columns}

	filters.pop('id')

	# Query to find the user with matching attributes
	matched_object = cls.query.filter_by(**filters).first()

	return matched_object

# Example function to decode text
def decode_text(salt: str, encoded: str) -> str:
	decode_function = decipher(salt)
	return decode_function(encoded)

def parse_date(date_string):
	# Clean up the date string by removing extra slashes or invalid characters
	if '//' in date_string:
		# Find the position of the first occurrence of "//"
		cut_index = date_string.find('//')
		# Trim the string from the right to that index
		date_string = date_string[:cut_index]

	if '-' in date_string:
		# Find the position of the first occurrence of "//"
		cut_index = date_string.find('-')
		# Trim the string from the right to that index
		date_string = date_string[:cut_index]

	if date_string.endswith('/'):
		date_string = date_string.rstrip('/')

	# Handle incomplete month format 'YYYY/MM' by assuming the 1st day of the month
	if len(date_string) == 7 and date_string.count('/') == 1:  # E.g. '2021/12'
		# print(f"Date format '{date_string}' detected. Assuming first day of the month.")
		date_string = f"{date_string}/01"  # Convert to 'YYYY/MM/01'

	# Define regex patterns for each valid format
	patterns = [
		(r"^(\d{4}) (\w{3}) (\d{1,2})$", "%Y %b %d"),     # Format: "2024 Aug 19"
		(r"^(\d{4}) (\w{3})$", "%Y %b"),                   # Format: "2022 Mar"
		(r"^(\d{4}) (\w{3})-(\w{3})$", "%Y %b"),           # Format: "2019 Nov-Dec"
		(r"^(\d{4})$", "%Y"),                              # Format: "2020"
		(r"^(\d{4})/(\d{2})/(\d{2})$", "%Y/%m/%d")         # Format: "2021/12/01"
	]

	# Match against known date formats
	for pattern, date_format in patterns:
		match = re.match(pattern, date_string)
		if match:
			try:
				# For other patterns, parse the date
				mydate = datetime.strptime(date_string, date_format)
				return date(mydate.year, mydate.month, mydate.day)
			except ValueError:
				# Handle invalid date format
				print(f"Invalid date format: {date_string}")
				return None

	# If no pattern matches, log and return None
	print(f"Date format for '{date_string}' is not supported.")
	return None

def fileReader(filepath):
	articles = []
	
	# Check file format (RIS or NBIB)
	is_ris = filepath.endswith('.ris')
	is_nbib = filepath.endswith('.nbib')

	if not (is_ris or is_nbib):
		raise ValueError("Unsupported file format. Please provide a .ris or .nbib file.")
	
	# Load file content
	entries = []
	try:
		if is_ris:
			with open(filepath, 'r', encoding='UTF-8') as bibliography_file:    
				entries = rispy.load(bibliography_file)
		elif is_nbib:
			entries = read_file(filepath)  # Assuming this function handles NBIB format
	except Exception as e:
		print(f"Error reading the file: {e}")
		return []
	
	# Process each entry
	for entry in entries:
		try:
			# Extract common fields with null handling
			publication_type_list = entry.get('publication_types', None) or []
			publication_type_t = entry.get('type_of_reference', None)

			pub_date = entry.get('date', None) or entry.get('publication_date', None)
			publication_date = parse_date(pub_date) if pub_date else None
			

			if 'Journal Article' not in publication_type_list and publication_type_t != "JOUR":
				# Handle missing essential fields
				if  not publication_date:
					continue

			publication_type = [{'publication_type': 'Journal Article'}]
			if is_ris:
				# For RIS files, authors are usually stored under the 'AU' tag
				keyword_list = entry.get('keywords',None) or []
				keywords = []
				keywords += ({"keyword":keyword} for keyword in keyword_list)
								
				author_list = (entry.get('authors',None) or [])+(entry.get('first_authors',None) or [])
				authors = [{"fullName": author} for author in author_list]
			
			elif is_nbib:
				# For NBIB files, authors might be under 'authors' or 'first_authors' (or both)
				keyword_list = entry.get('descriptors', None) or []
				keywords = []
				keywords += ({"keyword":keyword['descriptor']} for keyword in keyword_list)
				author_list = (entry.get('authors', None) or [])
				
				authors = [{"fullName": author['author'], "author_abbreviated": author['author_abbreviated'], "affiliations": author['affiliations']} for author in author_list]
		
			
			title = entry.get('title', None) or entry.get('primary_title', None)
			abstract = entry.get('abstract', None)
			journal = entry.get('journal', None) or entry.get('journal_name', None) or entry.get('secondary_title', None)
			journal_abrevated = entry.get('alternate_title1', None) if is_ris else entry.get('journal_abbreviated', None)

			
			pages = f"{entry.get('start_page', '')}-{entry.get('end_page', '')}" if entry.get('start_page') and entry.get('end_page') else None
			journal_volume = entry.get('volume', None)
			journal_issue = entry.get('number', None)
			pubmed_id = str(entry.get('pubmed_id', None))
			pmc_id = str(entry.get('pmcid', None))
			pii = entry.get('pii', None)
			doi = entry.get('doi', None)
			issn = entry.get('print_issn', None) or entry.get('issn', None)
			
			links = []
			file_attachments1 = entry.get('file_attachments1',None)
			file_attachments2 = entry.get('file_attachments2',None)
			urls = entry.get('urls',None)
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
				for link in urls:
					if is_valid_url(link):
						# print(f"link : {link}")
						links.append({"link": link})

			# print(f"links : {links}")
			# Create the article dictionary
			article = {
				"uuid": str(uuid.uuid4()),
				"publication_types": publication_type,
				"keywords": keywords,
				"authors": authors,
				"title": title,
				"abstract": abstract,
				"publication_date": publication_date.isoformat() if publication_date else None,
				"journal": journal,
				"journal_abrevated": journal_abrevated,
				"pages": pages,
				"journal_volume": journal_volume,
				"journal_issue": journal_issue,
				"pubmed_id": pubmed_id,
				"pmc_id": pmc_id,
				"pii": pii,
				"doi": doi,
				"print_issn": issn,
				"links": links
			}

			articles.append(article)

		except Exception as e:
			print(f"Error processing entry: {e}")
			continue

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
	article_data = {}
	
	try:
		tree = ET.parse(file_path)
		root = tree.getroot()

		article = root.find("PubmedArticle")
		if article is None:
			raise ValueError("PubmedArticle not found in the XML.")
		
		article_data["uuid"] = str(uuid.uuid4())
		
		# Extract Publication Types (handling None)
		publication_types = article.findall(".//PublicationTypeList/PublicationType")
		article_data["publication_types"] = [{"publication_type": pubType.text} for pubType in publication_types if pubType.text]

		# Extract Keywords (handling None)
		keywords = article.findall(".//Keyword")
		article_data["keywords"] = [{"keyword": keyword.text} for keyword in keywords if keyword.text]

		# Extract Authors (handling None and empty elements)
		authors = []
		for author in article.findall(".//Author"):
			last_name = author.find("LastName")
			fore_name = author.find("ForeName")
			initials = author.find("Initials")
			affiliations = author.findall(".//AffiliationInfo/Affiliation")
			
			# Safeguard against missing author fields
			last_name_text = last_name.text if last_name is not None else ""
			fore_name_text = fore_name.text if fore_name is not None else ""
			initials_text = initials.text if initials is not None else ""
			affiliations_text = [affiliation.text for affiliation in affiliations if affiliation.text]

			authors.append(
				{
					'fullName': f"{last_name_text}, {fore_name_text}".strip(", "),
					'author_abbreviated': f"{last_name_text} {initials_text}".strip(),
					'affiliations': affiliations_text,
				}
			)
		article_data["authors"] = authors

		# Extract Title
		title = article.find(".//ArticleTitle")
		article_data["title"] = title.text if title is not None else "No title available"

		# Extract Abstract
		abstract = article.find(".//Abstract/AbstractText")
		article_data["abstract"] = abstract.text if abstract is not None else "No abstract available"

		# Extract Publication Date (handling None)
		pub_date = article.find(".//PubDate")
		pub_year = pub_date.find("Year").text if pub_date is not None else None
		pub_month = pub_date.find("Month").text if pub_date is not None else None
		if pub_year and pub_month:
			article_data["publication_date"] = date(int(pub_year), datetime.strptime(pub_month, "%b").month, 1).isoformat()
		else:
			article_data["publication_date"] = None  # If year or month is missing, set to None

		# Extract Place of Publication
		place_of_publication = article.find(".//MedlineJournalInfo/Country")
		article_data["place_of_publication"] = place_of_publication.text if place_of_publication is not None else "Unknown"

		# Extract Journal Details
		journal_title = article.find(".//Journal/Title")
		article_data["journal"] = journal_title.text if journal_title is not None else "Unknown"
		journal_abbrev = article.find(".//ISOAbbreviation")
		article_data["journal_abrevated"] = journal_abbrev.text if journal_abbrev is not None else "Unknown"

		# Extract Pagination (Pages)
		pagination = article.find(".//Pagination/MedlinePgn")
		article_data["pages"] = pagination.text if pagination is not None else "N/A"

		# Extract Journal Volume and Issue
		journal_volume = article.find(".//JournalIssue/Volume")
		article_data["journal_volume"] = journal_volume.text if journal_volume is not None else "N/A"
		journal_issue = article.find(".//JournalIssue/Issue")
		article_data["journal_issue"] = journal_issue.text if journal_issue is not None else "N/A"

		# Extract PubMed ID
		pubmed_id = article.find(".//PMID")
		article_data["pubmed_id"] = pubmed_id.text if pubmed_id is not None else "N/A"

		# Extract Article IDs (DOI, PMC, PII)
		for article_id in article.findall(".//ArticleId"):
			id_type = article_id.get("IdType")
			if id_type == "doi":
				article_data["doi"] = article_id.text
			elif id_type == "pmc":
				article_data["pmc_id"] = article_id.text
			elif id_type == "pii":
				article_data["pii"] = article_id.text

		# Extract ISSNs (handling None)
		issn = article.find(".//Journal/ISSN")
		if issn is not None:
			IssnType = issn.get("IssnType")
			if IssnType == "Electronic":
				article_data["electronic_issn"] = issn.text
		else:
			article_data["electronic_issn"] = "N/A"

		# Extract Linking ISSN
		linking_issn = article.find(".//ISSNLinking")
		article_data["linking_issn"] = linking_issn.text if linking_issn is not None else "N/A"

		# Extract NLM Journal ID
		nlm_journal_id = article.find(".//NlmUniqueID")
		article_data["nlm_journal_id"] = nlm_journal_id.text if nlm_journal_id is not None else "N/A"

		# Links (if available)
		article_data["links"] = []

	except Exception as e:
		print(f"Error while parsing the PubMed XML: {e}")
		return None
	
	return article_data

