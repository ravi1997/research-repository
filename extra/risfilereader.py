import rispy
from datetime import datetime

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



