from datetime import datetime
from pprint import pprint
import uuid
from nbib import read_file

filepath = 'doc/pubmed-35225509 - single.nbib'


def nbibFileReader(filepath):
    articles = []
    entries = read_file(filepath)

    for entry in entries:
        publication_type = entry.get('publication_types', None) or []
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
                
        publication_date = (datetime.strptime(pub_date, "%Y %b") if pub_date else None)
                

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

        
        if 'Journal Article' in publication_type:
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
                "linking_issn":linking_issn,
                "electronic_issn":electronic_issn,
                "nlm_journal_id":nlm_journal_id,
                "links":links
            }
            articles.append(article)

    return articles
        