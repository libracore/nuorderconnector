// Copyright (c) 2018, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('nuOrder Settings', {
	refresh: function(frm) {
		// add test button
        /*frm.add_custom_button(__("Test"), function() {
			test(frm);
		});*/
        frm.add_custom_button(__("Get orders"), function() {
			get_orders(frm);
		}).addClass("btn-primary");
        frm.add_custom_button(__("Push customers"), function() {
			push_customers(frm);
		});
        frm.add_custom_button(__("Push items"), function() {
			push_items(frm);
		});
        frm.add_custom_button(__("Sync"), function() {
			sync(frm);
		}).addClass("btn-primary");
	},
	validate: function(frm) {
		frappe.call({
			method: 'check_connection',
			doc: frm.doc,
			freeze: true,
			freeze_message: __("Validating connection... Hang tight!"),
			async: false,
			callback: function(r) {
				if (r.message == false) {
					frappe.msgprint(__("Connection validation failed. Please check the credentials and the error log."),
						__("Validation"), );
					frappe.validated=false;
				} else {
					frappe.show_alert( __("Connection valid") );
				}
			}
		});		
	}
});

// test
function test(frm) {
    frappe.call({
		method: 'test',
		doc: frm.doc,
		callback: function(r) {
			frappe.show_alert( __("Test done: ") + r.message);
		}
	});
}

// get orders
function get_orders(frm) {
    frappe.call({
        method: 'get_orders',
        doc: frm.doc,
        callback: function(r) {
            frappe.show_alert( __("Orders read: ") + JSON.stringify(r.message));
        }
    });		
}

// push customers
function push_customers(frm) {
    frappe.call({
        method: 'push_customers',
        doc: frm.doc,
        callback: function(r) {
            frappe.show_alert( __("Customers written"));
        }
    });		
}

// push items
function push_items(frm) {
    frappe.call({
        method: 'push_items',
        doc: frm.doc,
        callback: function(r) {
            frappe.show_alert( __("Items written"));
        }
    });		
}

// sync
function sync(frm) {
    frappe.call({
        method: 'nuorderconnector.nuorderconnector.nuorder.queue_sync',
        callback: function(r) {
            frappe.msgprint( __("nuOrder queued for sync. Observe nuOrder log for details"));
        }
    });		
}
