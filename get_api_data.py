import requests
import json

class NxOnyxApi:
    def __init__(self, domain, username, password, tenantId):
        self.__domain = domain
        self.__username = username
        self.__password = password
        self.__tenantId = tenantId
        self.__token = self.getToken()

    def getToken(self):
        url = f"{self.__domain}/api/TokenAuth/Authenticate"

        payload = json.dumps({
            "userNameOrEmailAddress": self.__username,
            "password": self.__password
        })
        headers = {
            'Abp.TenantId': self.__tenantId,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            if response.status_code == 200:
                token = response.json().get('result').get('accessToken')
                # print("Accessed bearer token and connection successful : {}".format(token))
                return token
            else:
                response = requests.post(url, headers=headers, data=payload)
                raise Exception(f"Connection failed with status code: {response.status_code}, {response.json()}")

        except requests.exceptions.RequestException as e:
            raise ValueError("An error occurred in getToken:\n" + str(e))


    def getTree(self):
        url = f"{self.__domain}/api/services/app/OProjects/GetTree"
        headers = {
            'Abp.TenantId': self.__tenantId,
            'Accept': 'text/plain',
            'Authorization': f'Bearer {self.__token}'
        }
        try:
            response = requests.get(url, headers=headers)
            response_json = response.json()
            if response.status_code == 200:
                tree = response_json.get('result')
                return tree
            else:
                raise Exception(f"GetTree failed with status code: {response.status_code}, {response_json}")
        except requests.exceptions.RequestException as e:
            raise ValueError("An error occurred :\n" + str(e))