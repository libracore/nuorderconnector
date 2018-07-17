# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt
import json
import requests
from requests_oauthlib import OAuth1
import hashlib

class nuOrder():
    # static class variables
    consumer_key = ""
    consumer_secret = ""
    token = ""
    token_secret = ""
    host = "https://wholesale.sandbox1.nuorder.com"
    
    # constructor
    def __init__(self, host, consumer_key, consumer_secret, token, token_secret):
        self.host = host
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token = token
        self.token_secret = token_secret
        return
    
    # test function
    def test(self):
        print("Test")
        return
    
    # execute a get request
    def execute_get(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        print("Data: {0}".format(data))

        auth = OAuth1(self.consumer_key, self.consumer_secret,
                      self.token = token, self.token_secret)
        headers = {'content-type': 'application/json'}
        r = requests.put(url, auth=auth, data=json.dumps(payload), headers=headers)

        print("Response: {0}".format(r.json()))
        return r.json

    # execute a put request
    def execute_put(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        print("Data: {0}".format(data))

        auth = OAuth1(self.consumer_key, self.consumer_secret,
                      self.token = token, self.token_secret)
        headers = {'content-type': 'application/json'}
        url = self.host + endpoint
        r = requests.put(url, auth=auth, data=json.dumps(payload), headers=headers)

        print("Response: {0}".format(r.json()))
        return r.json
        
    def create_product(self, item):
        payload = {
          "style_number": item.item_code,
          "season": "spring/summer",
          "color": "all black",
          "name": item.item_name,
          "external_id": item.item_code,
          "category": item.item_group,
          "brand_id": "{0}".format(item.item_code),
          "unique_key": item.item_code,
          "sizes": [
            {
              "size": "OS",
              "size_group": "A1",
              "pricing": {
                "USD": {
                  "wholesale": 10,
                  "retail": 12.1,
                  "disabled": False
                }
              }
            }
          ],
          "size_groups": [
            "[ group1, group2, group3 ]"
          ],
          "available_now": False,
          "images": [
            "[599611906873730001745011]"
          ],
          "cancelled": False,
          "archived": False,
          "active": True,
          "description": "awesome product",
          "available_from": "2017/08/30",
          "available_until": "2019/08/30",
          "order_closing": "2017-09-12 00:00:00.000Z",
          "pricing": {
            "USD": {
              "wholesale": 10,
              "retail": 12.1,
              "disabled": False
            }
          },
          "seasons": [
            "[spring, summer, 2018]"
          ]
        }
        self.execute_put("/api/product/new", payload)
        return
        
    def create_company(self):
        payload = {
          "name": name,
          "code": hashlib.md5(name).hexdigest()
        }
        self.execute_put("/api/company/new", payload)    
        return

def test():
    nu = nuOrder()
    nu.test()
    
