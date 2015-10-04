;(function () {
	"use strict";

	var QuickFind = window.QuickFind = Ractive.extend({
		apiEndpoints: null,
		eventId: null,
		data: {
			results: null,
			search: null,
			loaded: null,
			currentSelectedIdx: 0,
			getUrlForResult: function () {}
		},

		oninit: function () {
			var ractive = this;
			ractive.observe('query', ractive.receiveQuery);
			ractive.set('getUrlForResult', this.getUrlForResult);
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
				search: query,
				event: ractive.eventId
			}, this.setResults.bind(ractive));
		}, 500, {leading: false}),

		setResults: function (data, status, jqXHR) {
			// After receiving list of orders, add them to Ractive's data:
			var ractive = this;
			// If the list is non-empty, make the first item keyboard-selected:
			if (!_.isEmpty(data)) {
				data[0].selected = true;
				this.currentSelectedIdx = 0;
			} else {
				this.currentSelectedIdx = null;
			}

			ractive.set('results', data);
			ractive.set('loaded', true);
		},

		getUrlForResult: function (result) {
			var ractive = this;
			return [location.origin, ractive.get('organizationSlug'), ractive.get('eventSlug'), "orders", result.code].join("/")
		},

		activateKeyboardEvents: function () {
			var ractive = this;
			// Activate the up and down and enter key behavior for selecting an order:
			$(window).on('keyup.quickfind', function (e) {
				var result,
					results = ractive.get('results'),
					currentIdx = ractive.currentSelectedIdx,
					nextIdx = currentIdx;

				// If there are no results, short-circuit:
				if (_.isEmpty(results)) return;
				// If it's not up, down, or enter, short-circuit:
				if (_.indexOf([38, 40, 13], e.which) === -1) return;

				// Enter:
				if (e.which === 13){
					result = results[currentIdx];
					window.location = ractive.getUrlForResult(result);
					return;
				}

				// Up:
				if (e.which === 38 && currentIdx > 0) {
					nextIdx = currentIdx - 1;
				}

				// Down:
				if (e.which == 40 && currentIdx < results.length) {
					nextIdx = currentIdx + 1;
				}

				ractive.set('results.' + currentIdx + '.selected', false);
				ractive.set('results.' + nextIdx + '.selected', true);
				ractive.currentSelectedIdx = nextIdx;
				return;
			});
		},

		deactivateKeyboardEvents: function () {
			// Deactivate keyboard behavior for selecting an order:
		}

	});
}());
