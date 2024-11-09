import requests

def download_nbib(pmid, filename):
    # Construct the URL for the E-utilities API
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}"
    
    # Send a GET request to fetch the content
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Write the content to a .nbib file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(response.content.decode('UTF-8'))
        print(f"Downloaded {filename} successfully.")
    else:
        print(f"Failed to download. HTTP Status Code: {response.status_code}")


import xml.etree.ElementTree as ET

def parse_pubmed_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    articles = []
    
    for article in root.findall("PubmedArticle"):
        article_data = {}

        # Extract core fields
        article_data["PMID"] = article.find(".//PMID").text
        article_data["Title"] = article.find(".//ArticleTitle").text
        article_data["Journal"] = article.find(".//Journal/Title").text
        article_data["ISOAbbreviation"] = article.find(".//ISOAbbreviation").text
        article_data["Volume"] = article.find(".//JournalIssue/Volume").text
        article_data["Issue"] = article.find(".//JournalIssue/Issue").text
        article_data["PubYear"] = article.find(".//PubDate/Year").text
        article_data["PubMonth"] = article.find(".//PubDate/Month").text
        article_data["Pagination"] = article.find(".//Pagination/MedlinePgn").text
        article_data["Abstract"] = article.find(".//Abstract/AbstractText").text

        article_data["publication_types"] = [pubType.text for pubType in article.findall(".//PublicationTypeList/PublicationType")]
        

        # Extract Authors
        authors = []
        for author in article.findall(".//Author"):
            last_name = author.find("LastName").text
            fore_name = author.find("ForeName").text
            initials = author.find("Initials").text
            affiliations = [affiliation.text for affiliation in author.findall(".//AffiliationInfo/Affiliation")]
            authors.append(
                {
                    'author':f"{last_name}, {fore_name}",
                    'author_abrevated':f"{last_name} {initials}",
                    'affiliations':affiliations
                }    
            )
        article_data["Authors"] = authors

        # Extract Keywords
        keywords = []
        for keyword in article.findall(".//Keyword"):
            keywords.append(keyword.text)
        article_data["Keywords"] = keywords

        # Extract Mesh Headings
        mesh_headings = []
        for mesh in article.findall(".//MeshHeading/DescriptorName"):
            mesh_headings.append(mesh.text)
        article_data["MeshHeadings"] = mesh_headings

        # Extract Article IDs (PubMed, DOI, PMC, etc.)
        article_ids = {}
        for article_id in article.findall(".//ArticleId"):
            id_type = article_id.get("IdType")
            article_ids[id_type] = article_id.text
        article_data["ArticleIDs"] = article_ids

        # Extract GrantList information if available
        grants = []
        for grant in article.findall(".//Grant"):
            grant_id = grant.find("GrantID").text if grant.find("GrantID") is not None else "N/A"
            agency = grant.find("Agency").text if grant.find("Agency") is not None else "N/A"
            country = grant.find("Country").text if grant.find("Country") is not None else "N/A"
            grants.append(f"{grant_id} ({agency}, {country})")
        article_data["GrantList"] = grants

        # Extract Publication Status
        pub_status = article.find(".//PublicationStatus")
        article_data["PublicationStatus"] = pub_status.text if pub_status is not None else "N/A"

        # Extract References
        references = []
        for reference in article.findall(".//Reference"):
            citation = reference.find("Citation").text if reference.find("Citation") is not None else "N/A"
            references.append(citation)
        article_data["ReferenceList"] = references

        articles.append(article_data)

    return articles

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

# Parse the XML and convert to NBIB
download_nbib(pmid, input_xml)
nbib_data = parse_pubmed_xml(input_xml)

# print(nbib_data)

# Save the NBIB data to a file
save_to_nbib(nbib_data, output_nbib)

print(f"Conversion complete! NBIB file saved as: {output_nbib}")
