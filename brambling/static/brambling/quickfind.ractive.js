;(function () {
	"use strict";

	var QuickFind = window.QuickFind = Ractive.extend({
		apiEndpoints: null,
		eventId: null,
		data: {
			results: null,
			search: null,
			loaded: null
		},

		oninit: function () {
			var ractive = this;
			ractive.observe('query', ractive.receiveQuery);
		},
		
		receiveQuery: function (newValue, oldValue, keyPath) {
			var ractive = this;
			// Value gets set when ractive first runs, but we shouldn't fire this function:
			if (typeof(oldValue) === "undefined") return;
			ractive.set('loaded', false);
			ractive.getResults(newValue);
		},

		getResults: _.throttle(function (query) {
			// Throttled, so this doesn't run more than twice per second:
			var ractive = this;
			// Fire GET request for list of orders:
			$.get(this.apiEndpoints['ordersearch'], {
				search: query
			}, this.setResults.bind(ractive));
		}, 500, {leading: false}),

		setResults: function (data, status, jqXHR) {
			// After receiving list of orders, add them to Ractive's data:
			var ractive = this;
			ractive.set('results', data);
			ractive.set('loaded', true);
		}

	});
}());
