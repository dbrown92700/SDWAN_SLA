#!/usr/bin/env python3

import requests
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
Copyright (c) 2012 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
			https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""
__copyright__ = "Copyright (c) 2012 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
"""
Class with REST Api GET and POST libraries

Updated for vManage 19.2 to include Cross Site Scripting Token

Example: python rest_api_lib.py vmanage_hostname username password

PARAMETERS:
    vmanage_hostname : Ip address of the vmanage or the dns name of the vmanage
    username : Username to login the vmanage
    password : Password to login the vmanage

Note: All the three arguments are mandatory
"""


class VmanageRestApi:

    def __init__(self, vmanage_ip, username, password, verify=False):
        self.vmanage_ip = vmanage_ip
        self.session = None
        # If the vmanage has a certificate signed by a trusted authority change verify to True
        self.verify = verify
        self.token = None
        self.cookie = None
        self.login(self.vmanage_ip, username, password)


    def login(self, vmanage_ip, username, password):

        base_url_str = f'https://{vmanage_ip}/'
        login_action = '/j_security_check'
        login_data = {'j_username': username, 'j_password': password}
        login_url = base_url_str + login_action
        self.session = requests.session()
        response = self.session.post(url=login_url, data=login_data, verify=self.verify)
        self.cookie = response.cookies
        self.token = self.get_request('/client/token')

    def get_request(self, mount_point, headers={'Content-Type': 'application/json'}, params=''):

        url = f"https://{self.vmanage_ip}/dataservice{mount_point}"
        headers['X-XSRF-TOKEN'] = self.token
        headers['Cookie'] = f'JSESSIONID={self.cookie["JSESSIONID"]}'
        response = self.session.get(url, headers=headers, params=params, verify=self.verify)
        data = response.content.decode('utf-8')
        try:
            data = json.loads(data)
        except:
            pass
        return data

    def post_request(self, mount_point, payload: dict, headers={'Content-Type': 'application/json'}):

        url = f"https://{self.vmanage_ip}/dataservice{mount_point}"
        payload = json.dumps(payload)
        headers['X-XSRF-TOKEN'] = self.token
        headers['Cookie'] = f'JSESSIONID={self.cookie["JSESSIONID"]}'
        response = self.session.post(url=url, data=payload, headers=headers, verify=self.verify)
        data = json.loads(response.content)
        return data

    def put_request(self, mount_point, payload, headers={'Content-Type': 'application/json'}):

        url = f"https://{self.vmanage_ip}/dataservice{mount_point}"
        payload = json.dumps(payload)
        headers['X-XSRF-TOKEN'] = self.token
        headers['Cookie'] = f'JSESSIONID={self.cookie["JSESSIONID"]}'
        response = self.session.put(url=url, data=payload, headers=headers, verify=self.verify)
        return response

    def delete_request(self, mount_point):

        url = f"https://{self.vmanage_ip}/dataservice{mount_point}"
        headers = {'Content-Type': 'application/json'}
        headers['X-XSRF-TOKEN'] = self.token
        headers['Cookie'] = f'JSESSIONID={self.cookie["JSESSIONID"]}'
        response = self.session.delete(url=url, headers=headers, verify=self.verify)
        data = json.loads(response.content)
        return data

    def logout(self):
        url = f"https://{self.vmanage_ip}/logout?nocache"
        headers = {'Content-Type': 'x-www-form-urlencoded'}
        headers['X-XSRF-TOKEN'] = self.token
        headers['Cookie'] = f'JSESSIONID={self.cookie["JSESSIONID"]}'
        response = self.session.post(url, headers=headers, verify=self.verify)
        return response
