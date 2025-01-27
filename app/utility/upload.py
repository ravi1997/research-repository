from datetime import date, datetime
import re
import uuid
import requests
import xml.etree.ElementTree as ET

import rispy
from nbib import read_file

from app.mylogger import error_logger
from app.utility.misc import is_valid_url

from flask import current_app as app

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
				error_logger.info(f"Invalid date format: {date_string}")
				return None

	# If no pattern matches, log and return None
	error_logger.info(f"Date format for '{date_string}' is not supported.")
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
		error_logger.info(f"Error reading the file: {e}")
		return []
	
 
	skipped = 0
	# Process each entry
	for entry in entries:
		try:
			# Extract common fields with null handling
			publication_type_list = entry.get('publication_types', None) or []
			publication_type_t = entry.get('type_of_reference', None)

			pub_date = entry.get('date', None) or entry.get('publication_date', None)
   
			pub_year = entry.get('year', None)
   
			year_match = re.search(r'\b(19|20)\d{2}\b', pub_date)

			if not year_match:
				pub_date = pub_year + " " + pub_date
   
			publication_date = parse_date(pub_date) if pub_date else None
			app.logger.info(f"pub_date : {pub_date}, publication_date : {publication_date}, year : {entry.get('year', None)}")

			if 'Journal Article' not in publication_type_list and publication_type_t != "JOUR":
				# Handle missing essential fields
				if  not publication_date:
					skipped = skipped + 1
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
			pubmed_id = str(entry.get('pubmed_id', None)) if entry.get('pubmed_id', None) else None
			pmc_id = str(entry.get('pmcid', None)) if entry.get('pmcid', None) else None
			pii = entry.get('pii', None)
			doi = entry.get('doi', None)
			issn = entry.get('print_issn', None) or entry.get('issn', None)
			
			links = []
			file_attachments1 = entry.get('file_attachments1',None)
			file_attachments2 = entry.get('file_attachments2',None)
			urls = entry.get('urls',None)
			if file_attachments1 is not None:
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
					app.logger.info(f"link : {link}")
					if is_valid_url(link):
						app.logger.info(f"pubmed_id : {pubmed_id}, condition : {("ncbi.nlm.nih.gov/pubmed" in link or "pubmed.ncbi.nlm.nih.gov/" in link)}")
						if pubmed_id == None and ("ncbi.nlm.nih.gov/pubmed" in link or "pubmed.ncbi.nlm.nih.gov/" in link):
							result = link.rsplit('/', 2)  # Split only once from the right
							app.logger.info(f"result : {result}")
							last_split = result[-1] if len(str(result[-1])) > 3 else result[-2]
							app.logger.info(f"last_split : {last_split}")
							pubmed_id = str(last_split)
							app.logger.info(f"pubmed_id : {pubmed_id}")

						app.logger.info(f"pmc_id : {pmc_id},condition : {"ncbi.nlm.nih.gov/pmc" in link}")
						if pmc_id == None and "ncbi.nlm.nih.gov/pmc" in link:
							result = link.rsplit('/', 2)  # Split only once from the right
							app.logger.info(result)
							
							last_split = result[-1] if len(str(result[-1])) > 3 else result[-2]
							pmc_id = str(last_split)
							app.logger.info(f"pmc_id : {pmc_id}")
       
    
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
			error_logger.info(f"Error processing entry: {e}")
			continue

	return articles,skipped

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
		error_logger.info(f"Error while parsing the PubMed XML: {e}")
		return None
	
	return article_data

