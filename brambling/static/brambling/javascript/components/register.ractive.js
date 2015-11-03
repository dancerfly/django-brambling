(function () {
    "use strict";
    var Shop = window.components.Shop = Ractive.extend({
        apiEndpoints: null,
        eventId: null,
        data: {
        	activeStep: 'shop',
            has_cart: function(order) {
                var has_cart = false;
                if (order && order.bought_items) {
                    $.each(order.bought_items, function(idx, item) {
                        if (item.status == 'reserved') {
                            has_cart = true;
                            return false;
                        }
                    });
                }
                return has_cart;
            },
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
            format_money: function(amount, currency) {
                var symbol_map = {
                    USD: '$',
                    GBP: '£'
                };
                if (symbol_map[currency]) {
                    return symbol_map[currency] + amount;
                }
                return '' + amount + ' ' + currency;
            },
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
        loadItems: function() {
            var thisObj = this;
            $.getJSON(thisObj.apiEndpoints['item'], {
                event: thisObj.eventId
            }, function (data) {
                thisObj.set('items', data);
                $.each(data, function(itemIdx, item) {
                    $.each(item.images, function(imageIdx, image) {
                        $.getJSON(image.resize_endpoint, {r: "fit|100|100"}, function(data) {
                            thisObj.set('items.' + itemIdx + '.images.' + imageIdx + '.preview', data);
                        });
                        $.getJSON(image.resize_endpoint, {r: "fit|598|598"}, function(data) {
                            thisObj.set('items.' + itemIdx + '.images.' + imageIdx + '.closeup', data);
                        });
                    });
                });
            });
        },
        loadOrder: function() {
            var thisObj = this;
            $.ajax({
                url: thisObj.apiEndpoints['order'],
                method: 'post',
                data: {
                    event: thisObj.eventId
                },
                success: function(data) {
                    $.each(data, function(key, value) {
                        if (key === 'bought_items') {
                            if (typeof thisObj.get('order.bought_items') === 'undefined') {
                                thisObj.set('order.bought_items', []);
                            }
                            var ii = 0, jj = 0;
                            while (true) {
                                oldValue = thisObj.get('order.bought_items.' + ii);
                                newValue = value[jj];

                                // If neither value is set, we're done.
                                if (!newValue && !oldValue) {
                                    break;
                                }

                                // If we've reached the end of the new list,
                                // just remove items. We don't need to increment
                                // because it'll reference the next one.
                                if (!newValue) {
                                    thisObj.splice('order.bought_items', ii, 1);
                                    continue;
                                }

                                // If we've reached the end of the current list,
                                // just append. Increment both to keep appending.
                                if (!oldValue) {
                                    thisObj.push('order.bought_items', newValue);
                                    ii++;
                                    jj++;
                                    continue;
                                }

                                // If we're in the middle - skip identical items.
                                if (oldValue.id == newValue.id) {
                                    ii++;
                                    jj++;
                                    continue;
                                }

                                // If the new one was added *after* the old one,
                                // remove the old one.
                                if (newValue.added >= oldValue.added) {
                                    thisObj.splice('order.bought_items', ii, 1);
                                } else {
                                    // Otherwise insert the new one. This will get caught as
                                    // identical items on the next round.
                                    thisObj.splice('order.bought_items', ii, 1, newValue)
                                }
                            }
                        } else {
                            thisObj.set('order.' + key, value);
                        }
                    });
                    thisObj.countdown();
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

        addToCart: function(item_option) {
            var thisObj = this,
                order = thisObj.get('order');
            $.ajax({
                url: thisObj.apiEndpoints['boughtitem'],
                method: 'post',
                data: {
                    item_option: item_option.link,
                    order: order.link
                },
                success: function (data) {
                    thisObj.push('order.bought_items', data)
                    thisObj.loadItems();
                    thisObj.loadOrder();
                }
            })
        },
        removeFromCart: function(bought_item) {
            var thisObj = this;
            $.ajax({
                url: bought_item.link,
                method: 'delete',
                data: {},
                success: function(data) {
                    var bought_items = thisObj.get('order.bought_items'),
                        index = null;

                    $.each(bought_items, function(idx, item) {
                        if (item.link === bought_item.link) {
                            index = idx;
                            return false;
                        }
                    });
                    if (index !== null) {
                        thisObj.splice('order.bought_items', index, 1);
                    }
                    thisObj.loadItems();
                    thisObj.loadOrder();
                }
            });
        },
        oninit: function (options) {
            var thisObj = this;
            thisObj.observe("discountCode", function (newValue, oldValue) {
                thisObj.set('discountError', '');
                if (newValue) {
                    $.ajax({
                        url: thisObj.apiEndpoints['orderdiscount'],
                        method: 'post',
                        data: {
                            discount_code: newValue,
                            order: thisObj.get('order').link
                        },
                        success: function (data) {
                            thisObj.push('order.discounts', data)
                            thisObj.set('discountCode', '');
                            // TODO: At some point we may also want to display
                            // or at least have accessible the changes to BoughtItemDiscounts.
                        },
                        error: function (data) {
                            var data = data.responseJSON;
                            thisObj.set('discountError', data.non_field_errors[0])
                        }
                    })
                }
            });

            this.observe("countdownExpired", function(newValue, oldValue) {
                var $ele = $('#countdownExpiredModal');
                if (newValue) {
                    $ele.modal('show');
                } else {
                    $ele.modal('hide');
                }
            });

            this.loadEvent();
            this.loadOrder();
            this.loadItems();
        }
    });
}());
