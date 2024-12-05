
import requests 
from pprint import pprint

response = requests.get("http://localhost:5000/researchrepository/")
cookie = dict(response.cookies)

print(cookie['Session-ID'], cookie['Session-SALT'])

sessionid = cookie['Session-ID']
sessionsalt = cookie['Session-SALT']


headers = {
    "API-ID":"43576556-30fd-483c-b95a-28da3a950388"
}
params = {
    'page': 2,
    'entry': 2
}


response = requests.get("http://localhost:5000/researchrepository/api/article/table", headers=headers, cookies=cookie, params= params)  # Use `requests.get`
pprint(response.json())