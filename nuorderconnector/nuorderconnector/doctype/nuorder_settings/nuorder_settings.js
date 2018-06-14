// Copyright (c) 2018, libracore and contributors
// For license information, please see license.txt

frappe.ui.form.on('nuOrder Settings', {
	refresh: function(frm) {
		// add test button
        frm.add_custom_button(__("Test"), function() {
			test(frm);
		}).addClass("btn-error");
	}
});

// test
function test(frm) {
    frappe.call({
		method: 'test',
		doc: frm.doc,
		callback: function(r) {
			
		}
	});
}
