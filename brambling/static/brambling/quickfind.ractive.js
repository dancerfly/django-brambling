(function () {
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
			ractive.observe('query', ractive.getResults);
		},
		getResults: function (newValue, oldValue, keyPath) {
			var ractive = this;
			// Value gets set when ractive first runs, but we shouldn't fire this function:
			if (typeof(oldValue) === "undefined") return;
			$.get(this.apiEndpoints['ordersearch'], {
				search: newValue
			}, this.setResults.bind(ractive));
		},
		setResults: function (data, status, jqXHR) {
			var ractive = this;
			ractive.set('results', data);
			ractive.set('loaded', true);
			console.log(data);
		}
	});
}());
