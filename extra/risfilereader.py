import rispy
filepath = 'doc/zotero Exported Items.ris'
author = "Gupta, Vivek"



with open(filepath, 'r') as bibliography_file:    
    entries = rispy.load(bibliography_file)

    for entry in entries:
        publication_type = ['JOURNAL']
        keywords = entry.get('keywords',None) or []
        authors = (entry.get('authors',None) or [])+(entry.get('first_authors',None) or [])
        
        title = entry.get('title',None) or entry.get('primary_title',None)
        abstract = entry.get('abstract',None)

        place_of_publication = entry.get('place_published',None)
        journal = entry.get('journal',None) or entry.get('journal_name',None) or entry.get('secondary_title',None)

        journal_abrevated = entry.get('alternate_title1',None)
        publication_date = entry.get('date',None)
        
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
        if entry['type_of_reference'] == 'JOUR' and author in authors and journal is not None:
            print('keywords : ',keywords)
            print('authors : ',authors)
            print('title : ',title)
            print('abstract : ',abstract)
            print('place_of_publication : ',place_of_publication)
            print('journal : ',journal)
            print('journal_abrevated : ',journal_abrevated)
            print('publication_date : ',publication_date)
            print('pages : ',pages)
            print('journal_volume : ',journal_volume)
            print('number : ',journal_issue)
            print('pubmed_id : ',pubmed_id)
            print('pmc_id : ',pmc_id)
            print('pii : ',pii)
            print('doi : ',doi)
            print('print_issn : ',print_issn)
            print('electronic_issn : ',electronic_issn)
            print('linking_issn : ',linking_issn)
            print('nlm_journal_id : ',nlm_journal_id)
            print('links : ',links)
            
            print('\n')