from pprint import pprint
import rispy
from nbib import read_file


def fileReader(filepath):
	articles = []
	entries = None
	if filepath.endswith('.ris'):
		with open(filepath, 'r') as bibliography_file:    
			entries = rispy.load(bibliography_file)
	elif filepath.endswith('.nbib'):
		entries = read_file(filepath)

	for entry in entries:
		publication_type = entry.get('publication_types', None) or ['Journal Article']
		discriptor_list = []
		discriptor_list += (discriptor['descriptor'] for discriptor in (entry.get('descriptors', None) or []))
		keyword_list = []
		if len(discriptor_list) > 0:
			keyword_list += discriptor_list
		else:
			keyword_list += entry.get('keywords',None) or []
		keywords = []
		keywords += ({"keyword":keyword} for keyword in keyword_list)
	
		author_list = (entry.get('authors',None) or [])+(entry.get('first_authors',None) or [])	
		authors = [{"fullName": author,"sequence_number":idx+1} for idx, author in enumerate(author_list)]
			
			
  


fileReader('doc/pubmed-35225509 - single.nbib')
fileReader('doc/zotero Exported Items.ris')