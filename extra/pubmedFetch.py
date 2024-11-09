from datetime import datetime
import os
from pprint import pprint
os.environ['NCBI_API_KEY'] = 'fdaf85434c8fce3e830d510732cd58f8ee08'
from metapub import PubMedFetcher

# pubmed_id


fetch = PubMedFetcher()
article = fetch.article_by_pmid('35225509')
# print(f"publication type : {article.publication_types}")
# print(f"keywords : {article.keywords}")
# print(f"title : {article.title}")
# print(f"Journal : {article.journal}, Year : {article.year}, volume : {article.volume}, issue : {article.issue}")
# for author in article.author_list:
#     print(f"authors : {author}")
# pprint(article.xml)

publication_type_list = list(article.publication_types.values())

if 'Journal Article' in publication_type_list:
	publication_type = []
	publication_type += ({'publication_type':publication} for publication in publication_type_list)

	keyword_list = article.keywords
	keywords = []

	
	keywords += ({"keyword":str(keyword)} for keyword in keyword_list)
	
	authors = [{"fullName": author.collective_name, "author_abbreviated": f"{author.last_name}, {author.initials}", "affiliations": author.affiliations, "sequence_number":idx + 1} for idx, author in enumerate(article.author_list)]
	title = article.title
	abstract = article.abstract
	
	journal = article.journal
 
	# journal_abrevated
	
	publication_date = datetime(year=int(article.year),month=1,day=1) 
	pages = article.pages

	journal_volume = article.volume
	journal_issue = article.issue
	
	pmc_id = str(article.pmc)
	pii = article.pii
	doi = article.doi
	# print(article.url)
			
			
	links = []
				
	# if urls:
	# 	links += ({"link": link} for link in urls)

else:
	print("Not an article")