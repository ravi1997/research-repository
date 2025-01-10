
from flask import current_app as app
import requests
from app.models.user import Client
from app.util import get_base_url, getIP, setCookie


def settingSession(request,response):
    session_ID = request.cookies.get('Session-ID')

    if session_ID is not None:
        session = Client.query.filter_by(client_session_id = session_ID).first()
        if session is not None:
            if session.isValid():
                return response
    
    client_ip = getIP(request)
    server_url = get_base_url()
    url = f"{server_url}/api/public/generateSession"
    
    headers = {
        "API-ID":app.config.get('API_ID')
    }
    
    params = {
        'ip': client_ip
    }

    ses_response = requests.get(url, headers=headers,params=params) 
    session = ses_response.json()
    setCookie(response,'Session-ID',session['Session-ID'])
    setCookie(response,'Session-SALT',session['Session-SALT'])
    return response

