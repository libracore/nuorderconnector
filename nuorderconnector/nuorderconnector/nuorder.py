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
    
    def get_oauth(self):
        return OAuth1(self.consumer_key, self.consumer_secret, self.token, self.token_secret)
    
    def get_headers(self):
        return {'content-type': 'application/json'}
                          
    # execute a get request
    def execute_get(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        r = requests.put(url, auth=get_oauth(), data=json.dumps(payload), headers=get_headers())
        return r.json

    # execute a put request
    def execute_put(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        url = self.host + endpoint
        r = requests.put(url, auth=get_oauth(), data=json.dumps(payload), headers=get_headers())
        return r.json

    # execute a post request
    def execute_post(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        url = self.host + endpoint
        r = requests.post(url, auth=get_oauth(), data=json.dumps(payload), headers=get_headers())
        return r.json
                
    """ create or update a product
          self
          item: ERPNext item object
          color: color of the item
          sizes: list of dicts as [{ "size": "L", "upc": "12345"}, { "size": "L", "upc": "12345"}]
          prices: dict of dicts as {"CHF": {"wholesale": 10, "retail": 20, "disabled": False }, "EUR": {"wholesale": 10, "retail": 20, "disabled": False}}
    """
    def update_product(self, item, color, sizes, prices):
        payload = {
          "style_number": item.item_code,
          "season": item.season,
          "color": color,
          "name": item.item_name,
          "external_id": item.item_code,
          "category": item.category,
          "brand_id": item.item_code,
          "sizes": sizes,
          "available_now": not item.disabled,
          "cancelled": False,
          "archived": item.disabled,
          "active": not item.disabled,
          "description": item.description,
          "available_from": item.available_start,
          "available_until": item.available_end,
          "order_closing": item.order_closing,
          "pricing": prices
        }
        self.execute_put("/api/product/new/force", payload)
        return
        
    """
    Create or update company records
      self
      company: ERPNext customer object
    """
    def update_company(self, company):
        payload = {
          "name": company.name,
          "code": hashlib.md5(name).hexdigest()
        }
        self.execute_put("/api/company/new/force", payload)    
        return
    
    """
    Pull orders from nuOrder into ERPNext
    """    
    def get_orders(self):
        # get list of pending orders
        order_ids = execute_get("/api/orders/{status}/list".format(status="pending"))
        if order_ids:
            for order_id in order_ids:
                # read order information
                order = execute_get("/api/order/{id}".format(id=order_id))
                if order:
                    # create order in ERPNext
                    # TODO MAP ORDER STRUCTURE
                    new_order = frappe.get_doc({"doctype": "Sales Order"})
                    new_order.comment = comment
                    new_order.insert()
                    frappe.db.commit()
                    
                    # update status in nuOrder
                    execute_post("/api/order/{id}/{status}".format(id=order_id,status="processed"))
        return

def test():
    nu = nuOrder()
    nu.test()
    
