# -*- coding: utf-8 -*-
# Copyright (c) 2018, libracore and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
from frappe import _

def get_data():
    return[
        {
            "label": _("Settings"),
            "icon": "octicon octicon-tools",
            "items": [
                   {
                       "type": "doctype",
                       "name": "nuOrder Settings",
                       "label": _("nuOrder Settings"),
                       "description": _("nuOrder Settings")
                   }
            ]
        },
        {
            "label": _("Log"),
            "icon": "octicon octicon-book",
            "items": [
                   {
                       "type": "doctype",
                       "name": "nuOrder Log",
                       "label": _("nuOrder Log"),
                       "description": _("nuOrder Log")
                   }
            ]
        }
    ]
