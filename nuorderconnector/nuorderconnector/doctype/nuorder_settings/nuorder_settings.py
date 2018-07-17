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
        pass
        
	pass

def test():
    nu = nuOrder()
    nu.test()
    
