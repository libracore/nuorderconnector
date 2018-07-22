# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt
import json
import requests
from requests_oauthlib import OAuth1
import hashlib
import frappe
from datetime import datetime

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
        url = self.host + endpoint
        r = requests.get(url, auth=self.get_oauth(), data=json.dumps(payload), headers=self.get_headers())
        return r.json()

    # execute a put request
    def execute_put(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        url = self.host + endpoint
        r = requests.put(url, auth=self.get_oauth(), data=json.dumps(payload), headers=self.get_headers())
        return r.json()

    # execute a post request
    def execute_post(self, endpoint, payload=None):
        data = json.dumps(payload).encode()
        url = self.host + endpoint
        r = requests.post(url, auth=self.get_oauth(), data=json.dumps(payload), headers=self.get_headers())
        return r.json()
    
    # check the connection
    def check_connection(self):
        url = self.host + "/api/orders/{status}/list".format(status="pending")
        r = requests.get(url, auth=self.get_oauth(), data=None, headers=self.get_headers())
        if r.status_code == 200:
            return True
        else:
            frappe.log_error("nuOrder connection failed: http error {0}\n{1}".format(r.status_code, r.json()))
            return False
        
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
        #self.execute_put("/api/product/new/force", payload)
        frappe.log_error("{0}".format(payload))
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
        #self.execute_put("/api/company/new/force", payload) 
        frappe.log_error("{0}".format(payload))   
        return
    
    """
    Pull orders from nuOrder into ERPNext
    """    
    def get_orders(self):
        count = 0
        # get list of pending orders
        order_ids = execute_get("/api/orders/{status}/list".format(status="pending"))
        if order_ids:
            for order_id in order_ids:
                # read order information
                order = execute_get("/api/order/{id}".format(id=order_id))
                if order:
                    count += 1
                    # create order in ERPNext
                    customer = order['retailer']['retailer_name']
                    items = []
                    for line_item in order['line_items']:
                        for size in line_item['sizes']:
                            barcode = size['upc']
                            matches = frappe.get_all('Item', filters={'barcode': barcode}, fields=['name'])
                            if matches:
                                items.append({'item_code': matches[0]['name'], 'qty': size['quantity'], 'rate': size['price']})
                    new_order = frappe.get_doc({"doctype": "Sales Order"})
                    new_order.customer = customer
                    new_order.items = items
                    new_order.insert()
                    frappe.db.commit()
                    
                    # update status in nuOrder
                    execute_post("/api/order/{id}/{status}".format(id=order_id,status="processed"))
        return count

    # checks all items and pushes them to nuOrder
    def process_items_to_nuorder(self):
        count = 0;
        # process all single items
        items = self.get_single_items()
        if items:
            for item in items:
                barcode = frappe.get_value('Item', item[0], 'barcode')
                count += 1
                self.update_erp_item(item_code=item[0], color='None', sizes=[{'size': '-', 'upc': barcode}])
        # process variants
        templates = self.get_template_items()
        if templates:
            for template in templates:
                # get all colors of this template
                colors = self.get_colors(template[0])
                for color in colors:
                    # get all size items for this color
                    items = self.get_items_by_color(template[0], color[0])
                    if items:
                        sizes = []
                        for item in items:
                            barcode = frappe.get_value('Item', item[0], 'barcode')
                            size_code = self.get_size_code(item[0])
                            if size_code and barcode:
                                sizes.append({'size': size_code[0], 'upc': barcode})
                        # add record
                        count += 1
                        self.update_erp_item(
                            item_code=items[0][0], 
                            color=color[0], 
                            sizes=sizes
                        )
        return count
        
    def update_erp_item(self, item_code, color, sizes):
        item = frappe.get_doc("Item", item_code)
        prices = frappe.get_all("Item Price", filters={'item_code': item_code, 'selling': 1}, fields=['currency', 'price_list_rate'])
        if prices:            
            self.update_product(
                item=item, 
                color=color, 
                sizes=sizes, 
                prices={
                    "{0}".format(prices[0]['currency']): {
                        "wholesale": prices[0]['price_list_rate'], 
                        "retail": item.retail_rate, 
                        "disabled": 0 
                    }
                }
            )  
        else:
            #skipped, no prices found
            log("Price missing", "Item {0} is missing a price record and was not uploaded.".format(item_code), "Error")
        return
        
    def get_single_items(self):
        sql_query = """SELECT `name` 
                       FROM `tabItem`
                       WHERE 
                          `has_variants` = 0 
                          AND `variant_of` IS NULL
                          AND `disabled` = 0
                          AND `is_sales_item` = 1
                          AND `publish_on_nuorder` = 1"""
        items = frappe.db.sql(sql_query, as_list=True)
        if items:
            return items
        else:
            return None
        
    def get_template_items(self):
        sql_query = """SELECT `name` 
                       FROM `tabItem`
                       WHERE 
                          `has_variants` = 1 
                          AND `variant_of` IS NULL
                          AND `disabled` = 0
                          AND `is_sales_item` = 1
                          AND `publish_on_nuorder` = 1"""
        items = frappe.db.sql(sql_query, as_list=True)
        if items:
            return items
        else:
            return None
            
    def get_colors(self, template_item_code):
        sql_query = """SELECT DISTINCT(`attribute_value`) 
                       FROM `tabItem Variant Attribute`
                       WHERE 
                          `parenttype` = 'Item' 
                          AND (`parent` IN (SELECT `name` FROM `tabItem` WHERE `variant_of` = '{template}'))
                        AND (`attribute` LIKE '%colour%' OR `attribute` LIKE '%color%')""".format(template=template_item_code)
        colors = frappe.db.sql(sql_query, as_list=True)
        if colors:
            return colors
        else:
            return None
       
    def get_items_by_color(self, template_item_code, color):
        sql_query = """SELECT `parent` 
                       FROM `tabItem Variant Attribute`
                       WHERE 
                           `parenttype` = 'Item' 
                           AND (`parent` IN (SELECT `name` FROM `tabItem` WHERE `variant_of` = '{template}'))
                           AND (`attribute` LIKE '%colour%' OR `attribute` LIKE '%color%')
                           AND `attribute_value` = '{color}'""".format(template=template_item_code, color=color)
        items = frappe.db.sql(sql_query, as_list=True)
        if items:
            return items
        else:
            return None
    
    def get_size_code(self, item_code):
        sql_query = """SELECT `attribute_value` 
                       FROM `tabItem Variant Attribute`
                       WHERE 
                           `parenttype` = 'Item' 
                           AND `parent` = '{item_code}'
                           AND `attribute` LIKE '%size%'
                        LIMIT 1""".format(item_code=item_code)
        sizes = frappe.db.sql(sql_query, as_list=True)
        if sizes:
            return sizes[0]
        else:
            return None        

    def get_customers(self):
        sql_query = """SELECT `name` 
                       FROM `tabCustomer`
                       WHERE 
                           `disabled` = 0""".format(item_code=item_code)
        customers = frappe.db.sql(sql_query, as_list=True)
        return customers


# synchronise
@frappe.whitelist()
def queue_sync():
    log(title= _("Starting nuOrder sync"), 
           description= ( _("Starting to sync nuOrder")),
           status="Running")
           
    enqueue("nuorderconnector.nuorderconnector.nuorder.sync",
        queue='long',
        timeout=15000)
    return

def sync():
    config = frappe.get_single("nuOrder Settings")
    nu = nuOrder(config.host, config.consumer_key, config.consumer_secret, config.token, config.token_secret)
    
    # push customers
    customers = nu.get_customers()
    for customer in customers:
        nu.update_company(customer)
    
    # push products
    product_count = nu.process_items_to_nuorder()
    
    # read orders
    order_count = nu.get_orders()
    
    # success log
    log(title= _("nuOrder sync complete"), 
        description= ( _("Sync of {0} customers, {1} products and {2} orders completed.")).format(
            len(customers), product_count, order_count), 
        status="Completed")
        
    return

def log(title, description="", status="Information"):
    new_log = frappe.get_doc({'doctype': 'nuOrder Log'}, ignore_patterns=True)
    new_log.title = title
    new_log.description = description
    new_log.status = status
    new_log.date = datetime.now()
    new_log.insert()
    frappe.db.commit()
    return
