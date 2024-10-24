import rispy
filepath = 'doc/zotero Exported Items.ris'
with open(filepath, 'r') as bibliography_file:    
    entries = rispy.load(bibliography_file)

    for entry in entries:
        print(entry['title'])
        print(entry.get('authors', 'No authors available'))
        