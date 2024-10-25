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




        if entry['type_of_reference'] == 'JOUR' and author in authors and journal is not None:
            print('keywords : ',keywords)
            print('authors : ',authors)
            print('title : ',title)
            print('abstract : ',abstract)
            print('place_of_publication : ',place_of_publication)
            print('journal : ',journal)
            print('alternate_title1 : ',journal_abrevated)
            print('publication_date : ',publication_date)
            # print('start_page : ',entry.get('start_page',None))
            # print('end_page : ',entry.get('end_page',None))
            # print('volume : ',entry.get('volume',None))
            # print('number : ',entry.get('number',None))
            # print('doi : ',entry.get('doi',None))
            # print('issn : ',entry.get('issn',None))
            # print('file_attachments1 : ',entry.get('file_attachments1',None))
            # print('file_attachments2 : ',entry.get('file_attachments2',None))
            # print('urls : ',entry.get('urls',None))
            
            print('\n')