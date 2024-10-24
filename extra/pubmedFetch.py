import os
from metapub import PubMedFetcher



os.environ['NCBI_API_KEY'] = 'fdaf85434c8fce3e830d510732cd58f8ee08'
fetch = PubMedFetcher()
article = fetch.article_by_pmid('35225509')
print(article.title)
print(article.journal, article.year, article.volume, article.issue)
print(article.authors)
print(article.citation)