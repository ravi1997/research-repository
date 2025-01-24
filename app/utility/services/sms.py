from flask import current_app as app
import requests
from app.mylogger import error_logger



def send_sms(mobile, message):
    """
    Sends an SMS using the configured SMS service.

    Args:
        mobile (str): The recipient's mobile number.
        message (str): The message to send.

    Returns:
        int: HTTP status code from the SMS service response.
    """
    app.logger.info("Preparing to send SMS...")
    
    # Data for the POST request
    data = {
        'username': app.config.get('OTP_USERNAME'),
        'password': app.config.get('OTP_PASSWORD'),
        'senderid': app.config.get('OTP_SENDERID'),
        'mobileNos': mobile,
        'message': f'{message}',
        'templateid1': app.config.get('OTP_ID')
    }

    # Headers for the POST request
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # URL of the SMS service
    url = app.config.get('OTP_SERVER')

    try:
        app.logger.info(f"Sending SMS to {mobile}. URL: {url}, Data: {data}")
        
        # Send the POST request
        response = requests.post(url, data=data, headers=headers)
        
        
        app.logger.info(f"SMS sent to {mobile}. Response status: {response.status_code}")
        if response.status_code != 200:
            error_logger.warning(f"Failed to send SMS. Status code: {response.status_code}, Response: {response.text}")
        
        return response.status_code
    except requests.RequestException as e:
        error_logger.error(f"Error occurred while sending SMS to {mobile}: {e}", exc_info=True)
        return 500
