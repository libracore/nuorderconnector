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
        frappe.msgprint("Test!")
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret)
        count = nu.process_items_to_nuorder()
        return count
        
    def check_connection(self):
        nu = nuOrder(self.host, self.consumer_key, self.consumer_secret, self.token, self.token_secret)
        return nu.check_connection()
        
	pass

def test():
    nu = nuOrder()
    nu.test()
    
