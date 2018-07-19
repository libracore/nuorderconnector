// Copyright (c) 2018, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('nuOrder Settings', {
	refresh: function(frm) {
		// add test button
        frm.add_custom_button(__("Test"), function() {
			test(frm);
		}).addClass("btn-error");
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
			console.log("Test done: " + r.message);
		}
	});
}
