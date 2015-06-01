var ractive = new Ractive({
        el: '#ractiveContainer',
        template: '#ractiveTemplate',
        data: {
            editable_by_user: dancerfly.editable_by_user,
            has_cart: function(order) {
                var has_cart = false;
                $.each(order.bought_items, function(idx, item) {
                    if (item.status == 'reserved') {
                        has_cart = true;
                        return false;
                    }
                });
                return has_cart;
            },
            fetch: function(link) {
                return state[link];
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
                return '' + amount + ' ' + currency;
            }
        }
    }),
    state = {};

$.getJSON(dancerfly.apiEndpoints['event'] + dancerfly.currentEventId + '/', function(data) {
    ractive.set('event', data);
    state[data.link] = data
});

$.getJSON(dancerfly.apiEndpoints['item'], {
    event: dancerfly.currentEventId
}, function (data) {
    ractive.set('items', data);
    $.each(data, function(idx, item) {
        state[item.link] = item;
        $.each(item.images, function(idx, image) {
            state[item.link] = image;
        });
        $.each(item.options, function(idx, option) {
            state[item.link] = option;
        });
    });
});

$.getJSON(dancerfly.apiEndpoints['order'], {
    event: dancerfly.currentEventId,
    user: dancerfly.currentUserId
}, function (data) {
    ractive.set('order', data[0]);
});
