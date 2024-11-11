from datetime import datetime
import uuid
import requests
import xml.etree.ElementTree as ET


def save_to_nbib(articles, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(f"PMID- {article.get('PMID', '')}\n")
            f.write(f"TI  - {article.get('Title', '')}\n")
            f.write(f"JT  - {article.get('Journal', '')}\n")
            f.write(f"TA  - {article.get('ISOAbbreviation', '')}\n")
            f.write(f"VI  - {article.get('Volume', '')}\n")
            f.write(f"IP  - {article.get('Issue', '')}\n")
            f.write(f"DP  - {article.get('PubYear', '')} {article.get('PubMonth', '')}\n")
            f.write(f"PG  - {article.get('Pagination', '')}\n")
            f.write(f"PT  - " + "\nPT  - ".join(article.get('publication_types',[])) + "\n")
            
            for author in article.get("Authors", []):
                f.write(f"FAU - {author['author']}\n")
                f.write(f"AU  - {author['author_abrevated']}\n")
                f.write(f"AD  - " + "\nAD  - ".join(author.get('affiliations',[])) + "\n")
            f.write(f"AB  - {article.get('Abstract', '')}\n")
            f.write("MH  - " + "\nMH  - ".join(article.get('MeshHeadings', [])) + "\n")
            f.write("KW  - " + "\nKW  - ".join(article.get('Keywords', [])) + "\n")
            
            # Write Article IDs
            for id_type, id_value in article.get("ArticleIDs", {}).items():
                f.write(f"ID  - {id_type}: {id_value}\n")

            # Write Grant Information
            f.write("GR  - " + "\nGR  - ".join(article.get("GrantList", [])) + "\n")

            # Write Publication Status
            f.write(f"PST - {article.get('PublicationStatus', '')}\n")

            # Write References
            f.write("RF  - " + "\nRF  - ".join(article.get("ReferenceList", [])) + "\n")
            
            f.write("ER  - \n\n")  # End of Record



# Example usage
pmid = '35225509'  # Replace with the actual PMID
input_xml = 'pubmed_data.xml'  # Your PubMed XML file
output_nbib = 'pubmed_data.nbib'  # Desired output NBIB file

nbib_data = {}

# print(nbib_data)

# Save the NBIB data to a file
save_to_nbib(nbib_data, output_nbib)

print(f"Conversion complete! NBIB file saved as: {output_nbib}")
