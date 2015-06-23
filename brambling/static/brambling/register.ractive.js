var Shop = Ractive.extend({
    apiEndpoints: null,
    eventId: null,
    data: {
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
        fetchObject: function(link) {
            return this.fetchObject(link);
        }
    },
    linkToKeypath: function (link) {
        var parsed = URI(link);
        return parsed.path().substr(1);
    },
    removeObject: function(obj) {
        var keypath = this.linkToKeypath(obj.link);
        this.set('store.' + keypath, undefined);
    },
    storeObject: function(obj) {
        var keypath = this.linkToKeypath(obj.link);
        this.set('store.' + keypath, obj);
    },
    fetchObject: function(link) {
        var keypath = this.linkToKeypath(link);
        return this.get('store.' + keypath);
    },

    loadEvent: function() {
        var thisObj = this;
        $.getJSON(thisObj.apiEndpoints['event'] + thisObj.eventId + '/', function(data) {
            thisObj.storeObject(data);
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
                thisObj.storeObject(data);
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
                thisObj.removeObject(bought_item);
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
                        thisObj.storeObject(data);
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

// URI parsing
/*! URI.js v1.15.1 http://medialize.github.io/URI.js/ */
/* build contains: URI.js */
(function(p,v){"object"===typeof exports?module.exports=v(require("./punycode"),require("./IPv6"),require("./SecondLevelDomains")):"function"===typeof define&&define.amd?define(["./punycode","./IPv6","./SecondLevelDomains"],v):p.URI=v(p.punycode,p.IPv6,p.SecondLevelDomains,p)})(this,function(p,v,u,l){function d(a,b){var c=1<=arguments.length,f=2<=arguments.length;if(!(this instanceof d))return c?f?new d(a,b):new d(a):new d;if(void 0===a){if(c)throw new TypeError("undefined is not a valid argument for URI");
a="undefined"!==typeof location?location.href+"":""}this.href(a);return void 0!==b?this.absoluteTo(b):this}function r(a){return a.replace(/([.*+?^=!:${}()|[\]\/\\])/g,"\\$1")}function w(a){return void 0===a?"Undefined":String(Object.prototype.toString.call(a)).slice(8,-1)}function h(a){return"Array"===w(a)}function C(a,b){var c={},d,g;if("RegExp"===w(b))c=null;else if(h(b))for(d=0,g=b.length;d<g;d++)c[b[d]]=!0;else c[b]=!0;d=0;for(g=a.length;d<g;d++)if(c&&void 0!==c[a[d]]||!c&&b.test(a[d]))a.splice(d,
1),g--,d--;return a}function z(a,b){var c,d;if(h(b)){c=0;for(d=b.length;c<d;c++)if(!z(a,b[c]))return!1;return!0}var g=w(b);c=0;for(d=a.length;c<d;c++)if("RegExp"===g){if("string"===typeof a[c]&&a[c].match(b))return!0}else if(a[c]===b)return!0;return!1}function D(a,b){if(!h(a)||!h(b)||a.length!==b.length)return!1;a.sort();b.sort();for(var c=0,d=a.length;c<d;c++)if(a[c]!==b[c])return!1;return!0}function F(a){return escape(a)}function A(a){return encodeURIComponent(a).replace(/[!'()*]/g,F).replace(/\*/g,
"%2A")}function x(a){return function(b,c){if(void 0===b)return this._parts[a]||"";this._parts[a]=b||null;this.build(!c);return this}}function E(a,b){return function(c,d){if(void 0===c)return this._parts[a]||"";null!==c&&(c+="",c.charAt(0)===b&&(c=c.substring(1)));this._parts[a]=c;this.build(!d);return this}}var G=l&&l.URI;d.version="1.15.1";var e=d.prototype,q=Object.prototype.hasOwnProperty;d._parts=function(){return{protocol:null,username:null,password:null,hostname:null,urn:null,port:null,path:null,
query:null,fragment:null,duplicateQueryParameters:d.duplicateQueryParameters,escapeQuerySpace:d.escapeQuerySpace}};d.duplicateQueryParameters=!1;d.escapeQuerySpace=!0;d.protocol_expression=/^[a-z][a-z0-9.+-]*$/i;d.idn_expression=/[^a-z0-9\.-]/i;d.punycode_expression=/(xn--)/i;d.ip4_expression=/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;d.ip6_expression=/^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$/;
d.find_uri_expression=/\b((?:[a-z][\w-]+:(?:\/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?\u00ab\u00bb\u201c\u201d\u2018\u2019]))/ig;d.findUri={start:/\b(?:([a-z][a-z0-9.+-]*:\/\/)|www\.)/gi,end:/[\s\r\n]|$/,trim:/[`!()\[\]{};:'".,<>?\u00ab\u00bb\u201c\u201d\u201e\u2018\u2019]+$/};d.defaultPorts={http:"80",https:"443",ftp:"21",gopher:"70",ws:"80",wss:"443"};d.invalid_hostname_characters=
/[^a-zA-Z0-9\.-]/;d.domAttributes={a:"href",blockquote:"cite",link:"href",base:"href",script:"src",form:"action",img:"src",area:"href",iframe:"src",embed:"src",source:"src",track:"src",input:"src",audio:"src",video:"src"};d.getDomAttribute=function(a){if(a&&a.nodeName){var b=a.nodeName.toLowerCase();return"input"===b&&"image"!==a.type?void 0:d.domAttributes[b]}};d.encode=A;d.decode=decodeURIComponent;d.iso8859=function(){d.encode=escape;d.decode=unescape};d.unicode=function(){d.encode=A;d.decode=
decodeURIComponent};d.characters={pathname:{encode:{expression:/%(24|26|2B|2C|3B|3D|3A|40)/ig,map:{"%24":"$","%26":"&","%2B":"+","%2C":",","%3B":";","%3D":"=","%3A":":","%40":"@"}},decode:{expression:/[\/\?#]/g,map:{"/":"%2F","?":"%3F","#":"%23"}}},reserved:{encode:{expression:/%(21|23|24|26|27|28|29|2A|2B|2C|2F|3A|3B|3D|3F|40|5B|5D)/ig,map:{"%3A":":","%2F":"/","%3F":"?","%23":"#","%5B":"[","%5D":"]","%40":"@","%21":"!","%24":"$","%26":"&","%27":"'","%28":"(","%29":")","%2A":"*","%2B":"+","%2C":",",
"%3B":";","%3D":"="}}},urnpath:{encode:{expression:/%(21|24|27|28|29|2A|2B|2C|3B|3D|40)/ig,map:{"%21":"!","%24":"$","%27":"'","%28":"(","%29":")","%2A":"*","%2B":"+","%2C":",","%3B":";","%3D":"=","%40":"@"}},decode:{expression:/[\/\?#:]/g,map:{"/":"%2F","?":"%3F","#":"%23",":":"%3A"}}}};d.encodeQuery=function(a,b){var c=d.encode(a+"");void 0===b&&(b=d.escapeQuerySpace);return b?c.replace(/%20/g,"+"):c};d.decodeQuery=function(a,b){a+="";void 0===b&&(b=d.escapeQuerySpace);try{return d.decode(b?a.replace(/\+/g,
"%20"):a)}catch(c){return a}};var t={encode:"encode",decode:"decode"},y,B=function(a,b){return function(c){try{return d[b](c+"").replace(d.characters[a][b].expression,function(c){return d.characters[a][b].map[c]})}catch(f){return c}}};for(y in t)d[y+"PathSegment"]=B("pathname",t[y]),d[y+"UrnPathSegment"]=B("urnpath",t[y]);t=function(a,b,c){return function(f){var g;g=c?function(a){return d[b](d[c](a))}:d[b];f=(f+"").split(a);for(var e=0,m=f.length;e<m;e++)f[e]=g(f[e]);return f.join(a)}};d.decodePath=
t("/","decodePathSegment");d.decodeUrnPath=t(":","decodeUrnPathSegment");d.recodePath=t("/","encodePathSegment","decode");d.recodeUrnPath=t(":","encodeUrnPathSegment","decode");d.encodeReserved=B("reserved","encode");d.parse=function(a,b){var c;b||(b={});c=a.indexOf("#");-1<c&&(b.fragment=a.substring(c+1)||null,a=a.substring(0,c));c=a.indexOf("?");-1<c&&(b.query=a.substring(c+1)||null,a=a.substring(0,c));"//"===a.substring(0,2)?(b.protocol=null,a=a.substring(2),a=d.parseAuthority(a,b)):(c=a.indexOf(":"),
-1<c&&(b.protocol=a.substring(0,c)||null,b.protocol&&!b.protocol.match(d.protocol_expression)?b.protocol=void 0:"//"===a.substring(c+1,c+3)?(a=a.substring(c+3),a=d.parseAuthority(a,b)):(a=a.substring(c+1),b.urn=!0)));b.path=a;return b};d.parseHost=function(a,b){var c=a.indexOf("/"),d;-1===c&&(c=a.length);if("["===a.charAt(0))d=a.indexOf("]"),b.hostname=a.substring(1,d)||null,b.port=a.substring(d+2,c)||null,"/"===b.port&&(b.port=null);else{var g=a.indexOf(":");d=a.indexOf("/");g=a.indexOf(":",g+1);
-1!==g&&(-1===d||g<d)?(b.hostname=a.substring(0,c)||null,b.port=null):(d=a.substring(0,c).split(":"),b.hostname=d[0]||null,b.port=d[1]||null)}b.hostname&&"/"!==a.substring(c).charAt(0)&&(c++,a="/"+a);return a.substring(c)||"/"};d.parseAuthority=function(a,b){a=d.parseUserinfo(a,b);return d.parseHost(a,b)};d.parseUserinfo=function(a,b){var c=a.indexOf("/"),f=a.lastIndexOf("@",-1<c?c:a.length-1);-1<f&&(-1===c||f<c)?(c=a.substring(0,f).split(":"),b.username=c[0]?d.decode(c[0]):null,c.shift(),b.password=
c[0]?d.decode(c.join(":")):null,a=a.substring(f+1)):(b.username=null,b.password=null);return a};d.parseQuery=function(a,b){if(!a)return{};a=a.replace(/&+/g,"&").replace(/^\?*&*|&+$/g,"");if(!a)return{};for(var c={},f=a.split("&"),g=f.length,e,m,n=0;n<g;n++)e=f[n].split("="),m=d.decodeQuery(e.shift(),b),e=e.length?d.decodeQuery(e.join("="),b):null,q.call(c,m)?("string"===typeof c[m]&&(c[m]=[c[m]]),c[m].push(e)):c[m]=e;return c};d.build=function(a){var b="";a.protocol&&(b+=a.protocol+":");a.urn||!b&&
!a.hostname||(b+="//");b+=d.buildAuthority(a)||"";"string"===typeof a.path&&("/"!==a.path.charAt(0)&&"string"===typeof a.hostname&&(b+="/"),b+=a.path);"string"===typeof a.query&&a.query&&(b+="?"+a.query);"string"===typeof a.fragment&&a.fragment&&(b+="#"+a.fragment);return b};d.buildHost=function(a){var b="";if(a.hostname)b=d.ip6_expression.test(a.hostname)?b+("["+a.hostname+"]"):b+a.hostname;else return"";a.port&&(b+=":"+a.port);return b};d.buildAuthority=function(a){return d.buildUserinfo(a)+d.buildHost(a)};
d.buildUserinfo=function(a){var b="";a.username&&(b+=d.encode(a.username),a.password&&(b+=":"+d.encode(a.password)),b+="@");return b};d.buildQuery=function(a,b,c){var f="",g,e,m,n;for(e in a)if(q.call(a,e)&&e)if(h(a[e]))for(g={},m=0,n=a[e].length;m<n;m++)void 0!==a[e][m]&&void 0===g[a[e][m]+""]&&(f+="&"+d.buildQueryParameter(e,a[e][m],c),!0!==b&&(g[a[e][m]+""]=!0));else void 0!==a[e]&&(f+="&"+d.buildQueryParameter(e,a[e],c));return f.substring(1)};d.buildQueryParameter=function(a,b,c){return d.encodeQuery(a,
c)+(null!==b?"="+d.encodeQuery(b,c):"")};d.addQuery=function(a,b,c){if("object"===typeof b)for(var f in b)q.call(b,f)&&d.addQuery(a,f,b[f]);else if("string"===typeof b)void 0===a[b]?a[b]=c:("string"===typeof a[b]&&(a[b]=[a[b]]),h(c)||(c=[c]),a[b]=(a[b]||[]).concat(c));else throw new TypeError("URI.addQuery() accepts an object, string as the name parameter");};d.removeQuery=function(a,b,c){var f;if(h(b))for(c=0,f=b.length;c<f;c++)a[b[c]]=void 0;else if("RegExp"===w(b))for(f in a)b.test(f)&&(a[f]=void 0);
else if("object"===typeof b)for(f in b)q.call(b,f)&&d.removeQuery(a,f,b[f]);else if("string"===typeof b)void 0!==c?"RegExp"===w(c)?!h(a[b])&&c.test(a[b])?a[b]=void 0:a[b]=C(a[b],c):a[b]===c?a[b]=void 0:h(a[b])&&(a[b]=C(a[b],c)):a[b]=void 0;else throw new TypeError("URI.removeQuery() accepts an object, string, RegExp as the first parameter");};d.hasQuery=function(a,b,c,f){if("object"===typeof b){for(var e in b)if(q.call(b,e)&&!d.hasQuery(a,e,b[e]))return!1;return!0}if("string"!==typeof b)throw new TypeError("URI.hasQuery() accepts an object, string as the name parameter");
switch(w(c)){case "Undefined":return b in a;case "Boolean":return a=Boolean(h(a[b])?a[b].length:a[b]),c===a;case "Function":return!!c(a[b],b,a);case "Array":return h(a[b])?(f?z:D)(a[b],c):!1;case "RegExp":return h(a[b])?f?z(a[b],c):!1:Boolean(a[b]&&a[b].match(c));case "Number":c=String(c);case "String":return h(a[b])?f?z(a[b],c):!1:a[b]===c;default:throw new TypeError("URI.hasQuery() accepts undefined, boolean, string, number, RegExp, Function as the value parameter");}};d.commonPath=function(a,b){var c=
Math.min(a.length,b.length),d;for(d=0;d<c;d++)if(a.charAt(d)!==b.charAt(d)){d--;break}if(1>d)return a.charAt(0)===b.charAt(0)&&"/"===a.charAt(0)?"/":"";if("/"!==a.charAt(d)||"/"!==b.charAt(d))d=a.substring(0,d).lastIndexOf("/");return a.substring(0,d+1)};d.withinString=function(a,b,c){c||(c={});var f=c.start||d.findUri.start,e=c.end||d.findUri.end,k=c.trim||d.findUri.trim,m=/[a-z0-9-]=["']?$/i;for(f.lastIndex=0;;){var n=f.exec(a);if(!n)break;n=n.index;if(c.ignoreHtml){var h=a.slice(Math.max(n-3,0),
n);if(h&&m.test(h))continue}var h=n+a.slice(n).search(e),l=a.slice(n,h).replace(k,"");c.ignore&&c.ignore.test(l)||(h=n+l.length,l=b(l,n,h,a),a=a.slice(0,n)+l+a.slice(h),f.lastIndex=n+l.length)}f.lastIndex=0;return a};d.ensureValidHostname=function(a){if(a.match(d.invalid_hostname_characters)){if(!p)throw new TypeError('Hostname "'+a+'" contains characters other than [A-Z0-9.-] and Punycode.js is not available');if(p.toASCII(a).match(d.invalid_hostname_characters))throw new TypeError('Hostname "'+
a+'" contains characters other than [A-Z0-9.-]');}};d.noConflict=function(a){if(a)return a={URI:this.noConflict()},l.URITemplate&&"function"===typeof l.URITemplate.noConflict&&(a.URITemplate=l.URITemplate.noConflict()),l.IPv6&&"function"===typeof l.IPv6.noConflict&&(a.IPv6=l.IPv6.noConflict()),l.SecondLevelDomains&&"function"===typeof l.SecondLevelDomains.noConflict&&(a.SecondLevelDomains=l.SecondLevelDomains.noConflict()),a;l.URI===this&&(l.URI=G);return this};e.build=function(a){if(!0===a)this._deferred_build=
!0;else if(void 0===a||this._deferred_build)this._string=d.build(this._parts),this._deferred_build=!1;return this};e.clone=function(){return new d(this)};e.valueOf=e.toString=function(){return this.build(!1)._string};e.protocol=x("protocol");e.username=x("username");e.password=x("password");e.hostname=x("hostname");e.port=x("port");e.query=E("query","?");e.fragment=E("fragment","#");e.search=function(a,b){var c=this.query(a,b);return"string"===typeof c&&c.length?"?"+c:c};e.hash=function(a,b){var c=
this.fragment(a,b);return"string"===typeof c&&c.length?"#"+c:c};e.pathname=function(a,b){if(void 0===a||!0===a){var c=this._parts.path||(this._parts.hostname?"/":"");return a?(this._parts.urn?d.decodeUrnPath:d.decodePath)(c):c}this._parts.path=this._parts.urn?a?d.recodeUrnPath(a):"":a?d.recodePath(a):"/";this.build(!b);return this};e.path=e.pathname;e.href=function(a,b){var c;if(void 0===a)return this.toString();this._string="";this._parts=d._parts();var f=a instanceof d,e="object"===typeof a&&(a.hostname||
a.path||a.pathname);a.nodeName&&(e=d.getDomAttribute(a),a=a[e]||"",e=!1);!f&&e&&void 0!==a.pathname&&(a=a.toString());if("string"===typeof a||a instanceof String)this._parts=d.parse(String(a),this._parts);else if(f||e)for(c in f=f?a._parts:a,f)q.call(this._parts,c)&&(this._parts[c]=f[c]);else throw new TypeError("invalid input");this.build(!b);return this};e.is=function(a){var b=!1,c=!1,f=!1,e=!1,k=!1,m=!1,h=!1,l=!this._parts.urn;this._parts.hostname&&(l=!1,c=d.ip4_expression.test(this._parts.hostname),
f=d.ip6_expression.test(this._parts.hostname),b=c||f,k=(e=!b)&&u&&u.has(this._parts.hostname),m=e&&d.idn_expression.test(this._parts.hostname),h=e&&d.punycode_expression.test(this._parts.hostname));switch(a.toLowerCase()){case "relative":return l;case "absolute":return!l;case "domain":case "name":return e;case "sld":return k;case "ip":return b;case "ip4":case "ipv4":case "inet4":return c;case "ip6":case "ipv6":case "inet6":return f;case "idn":return m;case "url":return!this._parts.urn;case "urn":return!!this._parts.urn;
case "punycode":return h}return null};var H=e.protocol,I=e.port,J=e.hostname;e.protocol=function(a,b){if(void 0!==a&&a&&(a=a.replace(/:(\/\/)?$/,""),!a.match(d.protocol_expression)))throw new TypeError('Protocol "'+a+"\" contains characters other than [A-Z0-9.+-] or doesn't start with [A-Z]");return H.call(this,a,b)};e.scheme=e.protocol;e.port=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0!==a&&(0===a&&(a=null),a&&(a+="",":"===a.charAt(0)&&(a=a.substring(1)),a.match(/[^0-9]/))))throw new TypeError('Port "'+
a+'" contains characters other than [0-9]');return I.call(this,a,b)};e.hostname=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0!==a){var c={};d.parseHost(a,c);a=c.hostname}return J.call(this,a,b)};e.host=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a)return this._parts.hostname?d.buildHost(this._parts):"";d.parseHost(a,this._parts);this.build(!b);return this};e.authority=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a)return this._parts.hostname?
d.buildAuthority(this._parts):"";d.parseAuthority(a,this._parts);this.build(!b);return this};e.userinfo=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a){if(!this._parts.username)return"";var c=d.buildUserinfo(this._parts);return c.substring(0,c.length-1)}"@"!==a[a.length-1]&&(a+="@");d.parseUserinfo(a,this._parts);this.build(!b);return this};e.resource=function(a,b){var c;if(void 0===a)return this.path()+this.search()+this.hash();c=d.parse(a);this._parts.path=c.path;this._parts.query=
c.query;this._parts.fragment=c.fragment;this.build(!b);return this};e.subdomain=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a){if(!this._parts.hostname||this.is("IP"))return"";var c=this._parts.hostname.length-this.domain().length-1;return this._parts.hostname.substring(0,c)||""}c=this._parts.hostname.length-this.domain().length;c=this._parts.hostname.substring(0,c);c=new RegExp("^"+r(c));a&&"."!==a.charAt(a.length-1)&&(a+=".");a&&d.ensureValidHostname(a);this._parts.hostname=
this._parts.hostname.replace(c,a);this.build(!b);return this};e.domain=function(a,b){if(this._parts.urn)return void 0===a?"":this;"boolean"===typeof a&&(b=a,a=void 0);if(void 0===a){if(!this._parts.hostname||this.is("IP"))return"";var c=this._parts.hostname.match(/\./g);if(c&&2>c.length)return this._parts.hostname;c=this._parts.hostname.length-this.tld(b).length-1;c=this._parts.hostname.lastIndexOf(".",c-1)+1;return this._parts.hostname.substring(c)||""}if(!a)throw new TypeError("cannot set domain empty");
d.ensureValidHostname(a);!this._parts.hostname||this.is("IP")?this._parts.hostname=a:(c=new RegExp(r(this.domain())+"$"),this._parts.hostname=this._parts.hostname.replace(c,a));this.build(!b);return this};e.tld=function(a,b){if(this._parts.urn)return void 0===a?"":this;"boolean"===typeof a&&(b=a,a=void 0);if(void 0===a){if(!this._parts.hostname||this.is("IP"))return"";var c=this._parts.hostname.lastIndexOf("."),c=this._parts.hostname.substring(c+1);return!0!==b&&u&&u.list[c.toLowerCase()]?u.get(this._parts.hostname)||
c:c}if(a)if(a.match(/[^a-zA-Z0-9-]/))if(u&&u.is(a))c=new RegExp(r(this.tld())+"$"),this._parts.hostname=this._parts.hostname.replace(c,a);else throw new TypeError('TLD "'+a+'" contains characters other than [A-Z0-9]');else{if(!this._parts.hostname||this.is("IP"))throw new ReferenceError("cannot set TLD on non-domain host");c=new RegExp(r(this.tld())+"$");this._parts.hostname=this._parts.hostname.replace(c,a)}else throw new TypeError("cannot set TLD empty");this.build(!b);return this};e.directory=
function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a||!0===a){if(!this._parts.path&&!this._parts.hostname)return"";if("/"===this._parts.path)return"/";var c=this._parts.path.length-this.filename().length-1,c=this._parts.path.substring(0,c)||(this._parts.hostname?"/":"");return a?d.decodePath(c):c}c=this._parts.path.length-this.filename().length;c=this._parts.path.substring(0,c);c=new RegExp("^"+r(c));this.is("relative")||(a||(a="/"),"/"!==a.charAt(0)&&(a="/"+a));a&&"/"!==a.charAt(a.length-
1)&&(a+="/");a=d.recodePath(a);this._parts.path=this._parts.path.replace(c,a);this.build(!b);return this};e.filename=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a||!0===a){if(!this._parts.path||"/"===this._parts.path)return"";var c=this._parts.path.lastIndexOf("/"),c=this._parts.path.substring(c+1);return a?d.decodePathSegment(c):c}c=!1;"/"===a.charAt(0)&&(a=a.substring(1));a.match(/\.?\//)&&(c=!0);var f=new RegExp(r(this.filename())+"$");a=d.recodePath(a);this._parts.path=
this._parts.path.replace(f,a);c?this.normalizePath(b):this.build(!b);return this};e.suffix=function(a,b){if(this._parts.urn)return void 0===a?"":this;if(void 0===a||!0===a){if(!this._parts.path||"/"===this._parts.path)return"";var c=this.filename(),f=c.lastIndexOf(".");if(-1===f)return"";c=c.substring(f+1);c=/^[a-z0-9%]+$/i.test(c)?c:"";return a?d.decodePathSegment(c):c}"."===a.charAt(0)&&(a=a.substring(1));if(c=this.suffix())f=a?new RegExp(r(c)+"$"):new RegExp(r("."+c)+"$");else{if(!a)return this;
this._parts.path+="."+d.recodePath(a)}f&&(a=d.recodePath(a),this._parts.path=this._parts.path.replace(f,a));this.build(!b);return this};e.segment=function(a,b,c){var d=this._parts.urn?":":"/",e=this.path(),k="/"===e.substring(0,1),e=e.split(d);void 0!==a&&"number"!==typeof a&&(c=b,b=a,a=void 0);if(void 0!==a&&"number"!==typeof a)throw Error('Bad segment "'+a+'", must be 0-based integer');k&&e.shift();0>a&&(a=Math.max(e.length+a,0));if(void 0===b)return void 0===a?e:e[a];if(null===a||void 0===e[a])if(h(b)){e=
[];a=0;for(var m=b.length;a<m;a++)if(b[a].length||e.length&&e[e.length-1].length)e.length&&!e[e.length-1].length&&e.pop(),e.push(b[a])}else{if(b||"string"===typeof b)""===e[e.length-1]?e[e.length-1]=b:e.push(b)}else b?e[a]=b:e.splice(a,1);k&&e.unshift("");return this.path(e.join(d),c)};e.segmentCoded=function(a,b,c){var e,g;"number"!==typeof a&&(c=b,b=a,a=void 0);if(void 0===b){a=this.segment(a,b,c);if(h(a))for(e=0,g=a.length;e<g;e++)a[e]=d.decode(a[e]);else a=void 0!==a?d.decode(a):void 0;return a}if(h(b))for(e=
0,g=b.length;e<g;e++)b[e]=d.decode(b[e]);else b="string"===typeof b||b instanceof String?d.encode(b):b;return this.segment(a,b,c)};var K=e.query;e.query=function(a,b){if(!0===a)return d.parseQuery(this._parts.query,this._parts.escapeQuerySpace);if("function"===typeof a){var c=d.parseQuery(this._parts.query,this._parts.escapeQuerySpace),e=a.call(this,c);this._parts.query=d.buildQuery(e||c,this._parts.duplicateQueryParameters,this._parts.escapeQuerySpace);this.build(!b);return this}return void 0!==
a&&"string"!==typeof a?(this._parts.query=d.buildQuery(a,this._parts.duplicateQueryParameters,this._parts.escapeQuerySpace),this.build(!b),this):K.call(this,a,b)};e.setQuery=function(a,b,c){var e=d.parseQuery(this._parts.query,this._parts.escapeQuerySpace);if("string"===typeof a||a instanceof String)e[a]=void 0!==b?b:null;else if("object"===typeof a)for(var g in a)q.call(a,g)&&(e[g]=a[g]);else throw new TypeError("URI.addQuery() accepts an object, string as the name parameter");this._parts.query=
d.buildQuery(e,this._parts.duplicateQueryParameters,this._parts.escapeQuerySpace);"string"!==typeof a&&(c=b);this.build(!c);return this};e.addQuery=function(a,b,c){var e=d.parseQuery(this._parts.query,this._parts.escapeQuerySpace);d.addQuery(e,a,void 0===b?null:b);this._parts.query=d.buildQuery(e,this._parts.duplicateQueryParameters,this._parts.escapeQuerySpace);"string"!==typeof a&&(c=b);this.build(!c);return this};e.removeQuery=function(a,b,c){var e=d.parseQuery(this._parts.query,this._parts.escapeQuerySpace);
d.removeQuery(e,a,b);this._parts.query=d.buildQuery(e,this._parts.duplicateQueryParameters,this._parts.escapeQuerySpace);"string"!==typeof a&&(c=b);this.build(!c);return this};e.hasQuery=function(a,b,c){var e=d.parseQuery(this._parts.query,this._parts.escapeQuerySpace);return d.hasQuery(e,a,b,c)};e.setSearch=e.setQuery;e.addSearch=e.addQuery;e.removeSearch=e.removeQuery;e.hasSearch=e.hasQuery;e.normalize=function(){return this._parts.urn?this.normalizeProtocol(!1).normalizePath(!1).normalizeQuery(!1).normalizeFragment(!1).build():
this.normalizeProtocol(!1).normalizeHostname(!1).normalizePort(!1).normalizePath(!1).normalizeQuery(!1).normalizeFragment(!1).build()};e.normalizeProtocol=function(a){"string"===typeof this._parts.protocol&&(this._parts.protocol=this._parts.protocol.toLowerCase(),this.build(!a));return this};e.normalizeHostname=function(a){this._parts.hostname&&(this.is("IDN")&&p?this._parts.hostname=p.toASCII(this._parts.hostname):this.is("IPv6")&&v&&(this._parts.hostname=v.best(this._parts.hostname)),this._parts.hostname=
this._parts.hostname.toLowerCase(),this.build(!a));return this};e.normalizePort=function(a){"string"===typeof this._parts.protocol&&this._parts.port===d.defaultPorts[this._parts.protocol]&&(this._parts.port=null,this.build(!a));return this};e.normalizePath=function(a){var b=this._parts.path;if(!b)return this;if(this._parts.urn)return this._parts.path=d.recodeUrnPath(this._parts.path),this.build(!a),this;if("/"===this._parts.path)return this;var c,e="",g,k;"/"!==b.charAt(0)&&(c=!0,b="/"+b);b=b.replace(/(\/(\.\/)+)|(\/\.$)/g,
"/").replace(/\/{2,}/g,"/");c&&(e=b.substring(1).match(/^(\.\.\/)+/)||"")&&(e=e[0]);for(;;){g=b.indexOf("/..");if(-1===g)break;else if(0===g){b=b.substring(3);continue}k=b.substring(0,g).lastIndexOf("/");-1===k&&(k=g);b=b.substring(0,k)+b.substring(g+3)}c&&this.is("relative")&&(b=e+b.substring(1));b=d.recodePath(b);this._parts.path=b;this.build(!a);return this};e.normalizePathname=e.normalizePath;e.normalizeQuery=function(a){"string"===typeof this._parts.query&&(this._parts.query.length?this.query(d.parseQuery(this._parts.query,
this._parts.escapeQuerySpace)):this._parts.query=null,this.build(!a));return this};e.normalizeFragment=function(a){this._parts.fragment||(this._parts.fragment=null,this.build(!a));return this};e.normalizeSearch=e.normalizeQuery;e.normalizeHash=e.normalizeFragment;e.iso8859=function(){var a=d.encode,b=d.decode;d.encode=escape;d.decode=decodeURIComponent;try{this.normalize()}finally{d.encode=a,d.decode=b}return this};e.unicode=function(){var a=d.encode,b=d.decode;d.encode=A;d.decode=unescape;try{this.normalize()}finally{d.encode=
a,d.decode=b}return this};e.readable=function(){var a=this.clone();a.username("").password("").normalize();var b="";a._parts.protocol&&(b+=a._parts.protocol+"://");a._parts.hostname&&(a.is("punycode")&&p?(b+=p.toUnicode(a._parts.hostname),a._parts.port&&(b+=":"+a._parts.port)):b+=a.host());a._parts.hostname&&a._parts.path&&"/"!==a._parts.path.charAt(0)&&(b+="/");b+=a.path(!0);if(a._parts.query){for(var c="",e=0,g=a._parts.query.split("&"),k=g.length;e<k;e++){var h=(g[e]||"").split("="),c=c+("&"+d.decodeQuery(h[0],
this._parts.escapeQuerySpace).replace(/&/g,"%26"));void 0!==h[1]&&(c+="="+d.decodeQuery(h[1],this._parts.escapeQuerySpace).replace(/&/g,"%26"))}b+="?"+c.substring(1)}return b+=d.decodeQuery(a.hash(),!0)};e.absoluteTo=function(a){var b=this.clone(),c=["protocol","username","password","hostname","port"],e,g;if(this._parts.urn)throw Error("URNs do not have any generally defined hierarchical components");a instanceof d||(a=new d(a));b._parts.protocol||(b._parts.protocol=a._parts.protocol);if(this._parts.hostname)return b;
for(e=0;g=c[e];e++)b._parts[g]=a._parts[g];b._parts.path?".."===b._parts.path.substring(-2)&&(b._parts.path+="/"):(b._parts.path=a._parts.path,b._parts.query||(b._parts.query=a._parts.query));"/"!==b.path().charAt(0)&&(c=(c=a.directory())?c:0===a.path().indexOf("/")?"/":"",b._parts.path=(c?c+"/":"")+b._parts.path,b.normalizePath());b.build();return b};e.relativeTo=function(a){var b=this.clone().normalize(),c,e,g,h;if(b._parts.urn)throw Error("URNs do not have any generally defined hierarchical components");
a=(new d(a)).normalize();c=b._parts;e=a._parts;g=b.path();h=a.path();if("/"!==g.charAt(0))throw Error("URI is already relative");if("/"!==h.charAt(0))throw Error("Cannot calculate a URI relative to another relative URI");c.protocol===e.protocol&&(c.protocol=null);if(c.username===e.username&&c.password===e.password&&null===c.protocol&&null===c.username&&null===c.password&&c.hostname===e.hostname&&c.port===e.port)c.hostname=null,c.port=null;else return b.build();if(g===h)return c.path="",b.build();
a=d.commonPath(b.path(),a.path());if(!a)return b.build();e=e.path.substring(a.length).replace(/[^\/]*$/,"").replace(/.*?\//g,"../");c.path=e+c.path.substring(a.length);return b.build()};e.equals=function(a){var b=this.clone();a=new d(a);var c={},e={},g={},k;b.normalize();a.normalize();if(b.toString()===a.toString())return!0;c=b.query();e=a.query();b.query("");a.query("");if(b.toString()!==a.toString()||c.length!==e.length)return!1;c=d.parseQuery(c,this._parts.escapeQuerySpace);e=d.parseQuery(e,this._parts.escapeQuerySpace);
for(k in c)if(q.call(c,k)){if(!h(c[k])){if(c[k]!==e[k])return!1}else if(!D(c[k],e[k]))return!1;g[k]=!0}for(k in e)if(q.call(e,k)&&!g[k])return!1;return!0};e.duplicateQueryParameters=function(a){this._parts.duplicateQueryParameters=!!a;return this};e.escapeQuerySpace=function(a){this._parts.escapeQuerySpace=!!a;return this};return d});

// Ractive slide transition

!function(t,e){"object"==typeof exports&&"undefined"!=typeof module?module.exports=e():"function"==typeof define&&define.amd?define(e):t.Ractive.transitions.slide=e()}(this,function(){"use strict";function t(t,e){var d;e=t.processParams(e,o),t.isIntro?(d=t.getStyle(i),t.setStyle(n)):(t.setStyle(t.getStyle(i)),d=n),t.setStyle("overflowY","hidden"),t.animateStyle(d,e).then(t.complete)}var e=t,o={duration:300,easing:"easeInOut"},i=["height","borderTopWidth","borderBottomWidth","paddingTop","paddingBottom","marginTop","marginBottom"],n={height:0,borderTopWidth:0,borderBottomWidth:0,paddingTop:0,paddingBottom:0,marginTop:0,marginBottom:0};return e});

// Ractive fade transition

!function(e,t){"object"==typeof exports&&"undefined"!=typeof module?module.exports=t():"function"==typeof define&&define.amd?define(t):e.Ractive.transitions.fade=t()}(this,function(){"use strict";function e(e,t){var i;t=e.processParams(t,n),e.isIntro?(i=e.getStyle("opacity"),e.setStyle("opacity",0)):i=0,e.animateStyle("opacity",i,t).then(e.complete)}var t=e,n={delay:0,duration:300,easing:"linear"};return t});

// Ractive tap support
(function (global, factory) {
    typeof exports === 'object' && typeof module !== 'undefined' ? module.exports = factory() :
    typeof define === 'function' && define.amd ? define(factory) :
    global.Ractive.events.tap = factory()
}(this, function () { 'use strict';

    // maximum milliseconds between down and up before cancel

    var ractive_events_tap = tap;

    var DISTANCE_THRESHOLD = 5; // maximum pixels pointer can move before cancel
    var TIME_THRESHOLD = 400;
    function tap(node, callback) {
        return new ractive_events_tap__TapHandler(node, callback);
    }

    var ractive_events_tap__TapHandler = function ractive_events_tap__TapHandler(node, callback) {
        this.node = node;
        this.callback = callback;

        this.preventMousedownEvents = false;

        this.bind(node);
    };

    ractive_events_tap__TapHandler.prototype = {
        bind: function bind(node) {
            // listen for mouse/pointer events...
            if (window.navigator.pointerEnabled) {
                node.addEventListener("pointerdown", handleMousedown, false);
            } else if (window.navigator.msPointerEnabled) {
                node.addEventListener("MSPointerDown", handleMousedown, false);
            } else {
                node.addEventListener("mousedown", handleMousedown, false);
            }

            // ...and touch events
            node.addEventListener("touchstart", handleTouchstart, false);

            // native buttons, and <input type='button'> elements, should fire a tap event
            // when the space key is pressed
            if (node.tagName === "BUTTON" || node.type === "button") {
                node.addEventListener("focus", handleFocus, false);
            }

            node.__tap_handler__ = this;
        },

        fire: function fire(event, x, y) {
            this.callback({
                node: this.node,
                original: event,
                x: x,
                y: y
            });
        },

        mousedown: function mousedown(event) {
            var _this = this;

            if (this.preventMousedownEvents) {
                return;
            }

            if (event.which !== undefined && event.which !== 1) {
                return;
            }

            var x = event.clientX;
            var y = event.clientY;

            // This will be null for mouse events.
            var pointerId = event.pointerId;

            var handleMouseup = function (event) {
                if (event.pointerId != pointerId) {
                    return;
                }

                _this.fire(event, x, y);
                cancel();
            };

            var handleMousemove = function (event) {
                if (event.pointerId != pointerId) {
                    return;
                }

                if (Math.abs(event.clientX - x) >= DISTANCE_THRESHOLD || Math.abs(event.clientY - y) >= DISTANCE_THRESHOLD) {
                    cancel();
                }
            };

            var cancel = function () {
                _this.node.removeEventListener("MSPointerUp", handleMouseup, false);
                document.removeEventListener("MSPointerMove", handleMousemove, false);
                document.removeEventListener("MSPointerCancel", cancel, false);
                _this.node.removeEventListener("pointerup", handleMouseup, false);
                document.removeEventListener("pointermove", handleMousemove, false);
                document.removeEventListener("pointercancel", cancel, false);
                _this.node.removeEventListener("click", handleMouseup, false);
                document.removeEventListener("mousemove", handleMousemove, false);
            };

            if (window.navigator.pointerEnabled) {
                this.node.addEventListener("pointerup", handleMouseup, false);
                document.addEventListener("pointermove", handleMousemove, false);
                document.addEventListener("pointercancel", cancel, false);
            } else if (window.navigator.msPointerEnabled) {
                this.node.addEventListener("MSPointerUp", handleMouseup, false);
                document.addEventListener("MSPointerMove", handleMousemove, false);
                document.addEventListener("MSPointerCancel", cancel, false);
            } else {
                this.node.addEventListener("click", handleMouseup, false);
                document.addEventListener("mousemove", handleMousemove, false);
            }

            setTimeout(cancel, TIME_THRESHOLD);
        },

        touchdown: function touchdown() {
            var _this = this;

            var touch = event.touches[0];

            var x = touch.clientX;
            var y = touch.clientY;

            var finger = touch.identifier;

            var handleTouchup = function (event) {
                var touch = event.changedTouches[0];

                if (touch.identifier !== finger) {
                    cancel();
                    return;
                }

                event.preventDefault(); // prevent compatibility mouse event

                // for the benefit of mobile Firefox and old Android browsers, we need this absurd hack.
                _this.preventMousedownEvents = true;
                clearTimeout(_this.preventMousedownTimeout);

                _this.preventMousedownTimeout = setTimeout(function () {
                    _this.preventMousedownEvents = false;
                }, 400);

                _this.fire(event, x, y);
                cancel();
            };

            var handleTouchmove = function (event) {
                var touch;

                if (event.touches.length !== 1 || event.touches[0].identifier !== finger) {
                    cancel();
                }

                touch = event.touches[0];
                if (Math.abs(touch.clientX - x) >= DISTANCE_THRESHOLD || Math.abs(touch.clientY - y) >= DISTANCE_THRESHOLD) {
                    cancel();
                }
            };

            var cancel = function () {
                _this.node.removeEventListener("touchend", handleTouchup, false);
                window.removeEventListener("touchmove", handleTouchmove, false);
                window.removeEventListener("touchcancel", cancel, false);
            };

            this.node.addEventListener("touchend", handleTouchup, false);
            window.addEventListener("touchmove", handleTouchmove, false);
            window.addEventListener("touchcancel", cancel, false);

            setTimeout(cancel, TIME_THRESHOLD);
        },

        teardown: function teardown() {
            var node = this.node;

            node.removeEventListener("pointerdown", handleMousedown, false);
            node.removeEventListener("MSPointerDown", handleMousedown, false);
            node.removeEventListener("mousedown", handleMousedown, false);
            node.removeEventListener("touchstart", handleTouchstart, false);
            node.removeEventListener("focus", handleFocus, false);
        }
    };

    function handleMousedown(event) {
        this.__tap_handler__.mousedown(event);
    }

    function handleTouchstart(event) {
        this.__tap_handler__.touchdown(event);
    }

    function handleFocus() {
        this.addEventListener("keydown", handleKeydown, false);
        this.addEventListener("blur", handleBlur, false);
    }

    function handleBlur() {
        this.removeEventListener("keydown", handleKeydown, false);
        this.removeEventListener("blur", handleBlur, false);
    }

    function handleKeydown(event) {
        if (event.which === 32) {
            // space key
            this.__tap_handler__.fire();
        }
    }

    return ractive_events_tap;

}));
