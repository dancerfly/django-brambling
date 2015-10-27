var Attendees = Ractive.extend({
	apiEndpoints: null,
	eventId: null,
	data: {
		activeStep: 'attendees',
		linebreaks: function(text) {
			// for now w/e.
			return text;
		},
		pluralize: function(num, suffix) {
			suffix = 's';
			if (num === 1) {
				suffix = '';
			}
			return suffix;
		},
		grouped: function(items) {
			var map = {},
				list = [];
			$.each(items, function (idx, item) {
				if (!map[item.item_name]) {
					map[item.item_name] = [];
				}
				map[item.item_name].push(item);
			});
			$.each(map, function (item_name, item_options) {
				list.push({
					'item_name': item_name,
					'boughtitems': item_options.sort(function (a, b) {
						return a.item_option_name.localeCompare(b.item_option_name);
					})
				});
			});
			list.sort(function (a, b) {
				return a.item_name.localeCompare(b.item_name);
			});
			return list;
		}
	},
	linkToKeypath: function (link) {
		var parsed = URI(link);
		return parsed.path().substr(1);
	},

	loadEvent: function() {
		var thisObj = this;
		$.getJSON(thisObj.apiEndpoints['event'] + thisObj.eventId + '/', function(data) {
			thisObj.set('event', data);
		});
	},
	loadOrder: function() {
		var thisObj = this;
		return $.ajax({
			url: thisObj.apiEndpoints['order'],
			method: 'post',
			cache: false,
			data: {
				event: thisObj.eventId
			},
			success: function(data) {
				if (typeof data.bought_items === 'undefined') {
					data.bought_items = [];
				}
				thisObj.set('order', data);
				thisObj.countdown();
			}
		});
	},
	loadBoughtItems: function(order) {
		var thisObj = this;
		$.ajax({
			url: thisObj.apiEndpoints['boughtitem'],
			method: 'get',
			cache: false,
			data: {
				order: order.id,
				status: ['reserved', 'unpaid', 'bought']
			},
			success: function (data) {
				thisObj.set('boughtitems', data);
			}
		});
	},
	loadAttendees: function(order) {
		var thisObj = this;
		$.ajax({
			url: thisObj.apiEndpoints['attendee'],
			method: 'get',
			cache: false,
			data: {
				order: order.id
			},
			success: function (data) {
				thisObj.set('attendees', data);
			}
		});
	},
	deleteAttendee: function (attendee) {
		var thisObj = this,
			order = thisObj.get('order'),
			attendees = thisObj.get('attendees'),
			boughtitems = thisObj.get('boughtitems'),
			removeIndex = null;
		$.each(attendees, function (idx, att) {
			if (att.id == attendee.id) {
				removeIndex = idx;
				return false;
			}
		});
		$.each(boughtitems, function (idx, item) {
			if (item.attendee == attendee.link) {
				item.attendee = null;
			}
		});
		thisObj.set('boughtitems', boughtitems);
		if (removeIndex !== null) {
			thisObj.splice('attendees', removeIndex, 1);
		}
		$.ajax({
			url: attendee.link,
			method: 'delete',
			cache: false,
			data: {
				order: order.id,
			}
		});
	},

	toggleSelectedItem: function (item) {
		var selectedItem = this.get('selectedItem');
		if (selectedItem && selectedItem.id != item.id) return;

		if (this.event) this.event.original.stopPropagation();

		if (!selectedItem) {
			this.set('selectedItem', item);
		} else {
			this.set('selectedItem', undefined);
		}
	},

	assignSelectedItem: function (item, attendee) {
		if (!item) {
			return;
		}
		var thisObj = this,
			boughtitems = thisObj.get('boughtitems'),
			realItem = undefined;
		$.each(boughtitems, function (idx, boughtitem) {
			if (boughtitem.id == item.id) realItem = boughtitem;
		});

		if (!realItem) return;

		realItem.attendee = attendee ? attendee.link : null;
		thisObj.set({
			'boughtitems': boughtitems,
			'selectedItem': null
		});
		$.ajax({
			url: realItem.link,
			method: 'patch',
			cache: false,
			data: {
				order: thisObj.get('order').link,
				attendee: realItem.attendee
			}
		});
	},
	countdown: function() {
		var thisObj = this,
			startStr = thisObj.get('order.cart_start_time'),
			cartTimeout = thisObj.get('event.cart_timeout');
		if (!startStr || !cartTimeout) {
			thisObj.set('countdown', undefined);
			return;
		}
		var startDate = new Date(startStr),
			now = new Date(),
			elapsed = now - startDate,
			remaining = cartTimeout * 60 * 1000 - elapsed;

		if (remaining < 0) {
			// cart has expired. show modal / clear cart.
			thisObj.set('countdownExpired', true);
			thisObj.loadOrder();
			return;
		}

		var seconds_left = Math.floor(remaining / 1000),
			countdown = {
				seconds: seconds_left % 60,
				minutes: Math.floor(seconds_left/60) % 60,
				hours: Math.floor(seconds_left/3600) % 24,
				days: Math.floor(seconds_left/86400)
			};
		thisObj.set('countdown', countdown);

		setTimeout(function() {
			thisObj.countdown();
		}, 1000);
	},

	oninit: function (options) {
		var thisObj = this;
		this.observe("countdownExpired", function(newValue, oldValue) {
			var $ele = $('#countdownExpiredModal');
			if (newValue) {
				$ele.modal('show');
			} else {
				$ele.modal('hide');
			}
		});

		this.loadEvent();
		this.loadOrder().then(function() {
			thisObj.loadAttendees(thisObj.get('order'));
			thisObj.loadBoughtItems(thisObj.get('order'));
		});
	}
});
