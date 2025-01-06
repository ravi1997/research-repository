from pprint import pprint
from app.util import cdac_service


data = cdac_service("E1500065")

pprint(data)