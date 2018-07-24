# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt
import json
import requests
from requests_oauthlib import OAuth1
import hashlib
import frappe
from datetime import datetime, timedelta
from frappe import _

class nuOrder():
    # static class variables
    consumer_key = ""
    consumer_secret = ""
    token = ""
    token_secret = ""
    host = "https://wholesale.sandbox1.nuorder.com"
    verify_ssl = True
    
    # constructor
    def __init__(self, host, consumer_key, consumer_secret, token, token_secret, verify_ssl=1):
        self.host = host
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token = token
        self.token_secret = token_secret
        if verify_ssl == 1:
            self.verify_ssl = True
        else:
            self.verify_ssl = False
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
        if payload:
            data = json.dumps(payload)
        else:
            data = None
        url = self.host + endpoint
        r = requests.get(url, auth=self.get_oauth(), data=data, headers=self.get_headers(), verify=self.verify_ssl)
        if r.status_code > 299:
            frappe.log_error("Get error {0} on {1}:\n{2}\n\n{3}".format(r.status_code, endpoint, payload, r.text))
            return None
        else:
            return r.json()

    # execute a put request
    def execute_put(self, endpoint, payload=None):
        data = json.dumps(payload)
        url = self.host + endpoint
        r = requests.put(url, auth=self.get_oauth(), data=data, headers=self.get_headers(), verify=self.verify_ssl)
        if r.status_code > 299:
            frappe.log_error("Put error {0} on {1}:\n{2}\n\n{3}".format(r.status_code, endpoint, payload, r.text))
        return r.json()

    # execute a post request
    def execute_post(self, endpoint, payload=None):
        if payload:
            data = json.dumps(payload)
        else:
            data=None
        url = self.host + endpoint
        r = requests.post(url, auth=self.get_oauth(), data=data, headers=self.get_headers(), verify=self.verify_ssl)
        if r.status_code > 299:
            frappe.log_error("Post error {0} on {1}:\n{2}\n\n{3}".format(r.status_code, endpoint, payload, r.text))
        return r.json()
    
    # check the connection
    def check_connection(self):
        url = self.host + "/api/orders/{status}/list".format(status="pending")
        r = requests.get(url, auth=self.get_oauth(), data=None, headers=self.get_headers(), verify=self.verify_ssl)
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
          "category": item.category or "",
          "brand_id": item.item_code,
          "sizes": sizes,
          "available_now": not item.disabled,
          "cancelled": False,
          "archived": item.disabled,
          "active": not item.disabled,
          "description": item.description or "",
          "available_from": self.get_date_string(item.available_start),
          "available_until": self.get_date_string(item.available_end),
          "order_closing": self.get_date_string(item.order_closing),
          "pricing": prices,
          "department": item.department or "",
          "division": item.division or "",
          "brand name": item.brand or ""
        }
        self.execute_put("/api/product/new/force", payload)
        return
    
    def get_date_string(self, date):
        if date:
            return "{0}/{1}/{2}".format(date.year, date.month, date.day)
        else:
            return ""

    """
    Create or update company records
      self
      company: ERPNext customer object
    """
    def update_company(self, company):
        customer = frappe.get_doc("Customer", company)
        addresses = self.get_addresses(customer.name)
        payload = {
          "name": company,
          "code": hashlib.md5(company).hexdigest(),
          "currency_code": customer.default_currency or "CHF",
          "addresses": addresses
        }
        self.execute_put("/api/company/new/force", payload)   
        return
    
    def get_addresses(self, customer_name):
        addresses = []
        adr_links = frappe.get_all("Dynamic Link", filters={'link_name': contact_name['name'], 'parenttype': 'Address'}, fields=['parent'])
        if adr_links:
            for address in adr_links:
                adr = frappe.get_doc("Address", address['parent'])
                addresses.append({
                    "display_name": adr.name,
                    "line_1": adr.address_line1,
                    "city": adr.city,
                    "zip": adr.pincode,
                    "country": adr.country
                })
        return addresses

    """
    Pull orders from nuOrder into ERPNext
    """    
    def get_orders(self):
        count = 0
        orders = []
        # get list of pending orders
        order_ids = self.execute_get("/api/orders/{status}/list".format(status="approved"))
        if order_ids:
            for order_id in order_ids:
                # read order information
                order = self.execute_get("/api/order/{id}".format(id=order_id))
                if order:
                    count += 1
                    # create order in ERPNext
                    customer = order['retailer']['retailer_name']
                    currency = order['currency_code']
                    items = []
                    for line_item in order['line_items']:
                        for size in line_item['sizes']:
                            try:
                                barcode = size['upc']
                                matches = frappe.get_all('Item', filters={'barcode': barcode}, fields=['name'])
                                if matches:
                                    items.append({'item_code': matches[0]['name'], 'qty': size['quantity'], 'rate': size['price']})
                            except:
                                frappe.log_error("nuOrder: Reading order failed: invalid data: {0}".format(size))
                    try:
                        new_so = frappe.get_doc({
                            "doctype": "Sales Order",
                            "customer": customer,
                            "items": items,
                            "delivery_date": (datetime.now() + timedelta(days=5)),
                            "currency": currency
                        })
                        new_so.insert()
                        frappe.db.commit()
                        orders.append(order_id)
                        # update status in nuOrder
                        self.execute_post("/api/order/{id}/{status}".format(id=order_id,status="processed"))
                    except Exception as e:
                        frappe.log_error("nuOrder: Insert order failed: {0} ({1})".format(order_id, e))

        return { 'count': count, 'orders': orders}

    # checks all items and pushes them to nuOrder
    def process_items_to_nuorder(self):
        count = 0;
        # process all single items
        items = self.get_single_items()
        if items:
            for item in items:
                barcode = frappe.get_value('Item', item[0], 'barcode')
                count += 1
                self.update_erp_item(item_code=item[0], color='None', sizes=[{'size': 'onesize', 'upc': barcode}])
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
                           `disabled` = 0"""
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
    nu = nuOrder(config.host, config.consumer_key, config.consumer_secret, config.token, config.token_secret, config.verify_ssl)
    
    # push customers
    customers = nu.get_customers()
    for customer in customers:
        nu.update_company(customer[0])
    
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

def test():
    #items = []
    #items.append({'item_code': 'Test1', 'qty': 1, 'rate': 15})
    #new_order = frappe.get_doc({"doctype": "Sales Order"})
    #new_order.customer = "Guest"
    #new_order.items = items
    #new_order.insert()
    new_so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": "Guest",
        "items": [
            {
                "item_code": "Test",
                "qty": 1,
                "rate": 15
            }
        ],
        "delivery_date": (datetime.now() + timedelta(days=5))
    })
    new_so.insert()
    frappe.db.commit()
