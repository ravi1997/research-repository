from pprint import pprint
import requests

def fetch_pubmed_article(pmid):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id={pmid}&retmode=json"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for errors
        data = response.json()
        return data["result"].get(str(pmid), {})
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

# Example usage
pmid = "35225509"  # Replace with the PMID you want to search for
article_data = fetch_pubmed_article(pmid)
pprint(article_data)