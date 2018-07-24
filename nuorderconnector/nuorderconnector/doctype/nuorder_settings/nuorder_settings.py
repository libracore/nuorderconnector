# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from nuorderconnector.nuorderconnector.nuorder import nuOrder 

class nuOrderSettings(Document):
    @frappe.whitelist()
    def test(self):
        frappe.msgprint("Observe the console, error log and the nuOrder log for output")
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret, self.verify_ssl)
        #count = nu.process_items_to_nuorder()
        count = 1
        nu.get_orders()
        return count
        
    def check_connection(self):
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret, self.verify_ssl)
        return nu.check_connection()
        
    def get_orders(self):
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret, self.verify_ssl)
        return nu.get_orders()

    def push_customers(self):
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret, self.verify_ssl)
        nu.get_orders()
        # push customers
        customers = nu.get_customers()
        for customer in customers:
            nu.update_company(customer[0])
        return

    def push_items(self):
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret, self.verify_ssl)
        nu.process_items_to_nuorder()
        return
        
	pass

def test():
    nu = nuOrder()
    nu.test()
    
