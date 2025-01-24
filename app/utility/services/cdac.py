from flask import current_app as app
import requests
from app.mylogger import error_logger

def call_third_party_api(search_mode, search_key, org_code, access_token):
    """
    Calls the third-party API with the given parameters.

    Args:
        search_mode (int): Search mode type (e.g., 2 for emp_id).
        search_key (str): The key to search for (e.g., employee ID).
        org_code (str): Organization code.
        access_token (str): Authorization token.

    Returns:
        Response: The HTTP response object from the third-party API.
    """
    api_url = app.config["CDAC_SERVER"]
    headers = {
        "Authorization": f"Bearer {access_token}",
        "searchMode": str(search_mode),
        "searchKey": search_key,
        "orgCode": org_code
    }

    try:
        app.logger.info(f"Calling third-party API at {api_url} with searchMode: {search_mode}, searchKey: {search_key}, orgCode: {org_code}")
        response = requests.post(api_url, headers=headers)
        app.logger.info(f"Third-party API response status: {response.status_code}")
        return response
    except requests.RequestException as e:
        error_logger.error(f"Error occurred while calling third-party API: {e}", exc_info=True)
        return None

def cdac_service(emp_id):
    """
    Fetches employee details using the CDAC API.

    Args:
        emp_id (str): Employee ID to search.

    Returns:
        dict/str: JSON data if the call is successful, otherwise an error message.
    """
    type_ = "emp_id"  # ["emp_id", "pan"]
    search_key = emp_id  # Employee ID or PAN
    search_mode = 2
    org_code = "33101"

    auth_url = app.config["CDAC_AUTH_SERVER"]
    auth_data = {
        "client_id": app.config["CDAC_USERNAME"],
        "client_secret": app.config["CDAC_PASSWORD"],
        "client_serID": app.config["CDAC_ID"]
    }

    try:
        # Call the authentication API
        app.logger.info("Calling CDAC authentication API...")
        response_auth = requests.post(auth_url, json=auth_data)
        app.logger.info(f"Authentication API response status: {response_auth.status_code}")

        if response_auth.status_code == 200:
            access_token = response_auth.json().get('access_token')
            if access_token:
                # Call the third-party API
                response_api = call_third_party_api(search_mode, search_key, org_code, access_token)
                if response_api and response_api.status_code == 200:
                    data = response_api.json()
                    app.logger.info("Successfully fetched data from the third-party API.")
                    return data
                else:
                    error_msg = f"Either employee ID is wrong or something went wrong. API Status Code: {response_api.status_code if response_api else 'No response'}"
                    error_logger.error(error_msg)
                    return error_msg
            else:
                error_logger.error("Access token not found in authentication response.")
                return "Something went wrong: Access token not found."
        else:
            error_logger.error(f"Authentication API failed. Status code: {response_auth.status_code}, Response: {response_auth.text}")
            return f"Something went wrong: Authentication failed."
    except requests.RequestException as e:
        error_logger.error(f"Error occurred during authentication or API call: {e}", exc_info=True)
        return "Something went wrong: Request failed."
