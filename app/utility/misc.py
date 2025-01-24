from datetime import datetime
import secrets
import string
from urllib.parse import urlparse
from flask import current_app as app



def is_valid_url(url):
	parsed = urlparse(url)
	return all([parsed.scheme, parsed.netloc])


def getIP(request):
	x_forwarded_for = request.headers.get('X-Forwarded-For')
	if x_forwarded_for:
		# Take the first IP if there are multiple IPs listed
		client_ip = x_forwarded_for.split(',')[0]
	else:
		client_ip = request.remote_addr
	client = request.args.get('ip', client_ip, type=str)



def to_date(date_string): 
	try:
		return datetime.strptime(date_string, "%Y-%m-%d").date()
	except ValueError:
		raise ValueError('{} is not valid date in the format YYYY-MM-DD'.format(date_string))


def getNewSalt(length: int = 16) -> str:
	characters = string.ascii_letters + string.digits
	salt = ''.join(secrets.choice(characters) for _ in range(length))
	return salt


def get_base_url():
	# Get the host and port from the app's configuration
	host = "127.0.0.1" # Default to localhost if not set
	port = app.config.get("PORT", 5000)  # Default port is 5000

	# Determine the scheme based on whether the app is running in debug mode or not
	scheme = "http"
	
	# Construct the base URL
	base_url = f"{scheme}://{host}:{port}/"
	return base_url

def setCookie(response,name,value,httponly=True):
	response.set_cookie(name,value, httponly=httponly, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  
