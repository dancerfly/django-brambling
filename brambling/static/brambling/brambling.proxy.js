/**
 * jQuery Proxy
 * @author Harris Lapiroff
 * @requires jQuery
 *
 * Copyright (c) 2015, Little Weaver Web Collective
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 *
 * Documentation
 * -------------
 *
 * Defines a declarative HTML syntax for triggering an event on one element
 * by receiving an event on another element.
 *
 * E.g., To trigger form submission on form #myForm when hovering over a div:
 *
 * <div data-proxy="#myForm" data-on="mouseover" data-trigger="submit">
 *     Careful! Hovering over me submits a form!
 * </div>
 *
 * <form id="myForm" href="" action="POST"></form>
 */

;(function($){
	var ProxyTrigger = function (el) {
		this.$el = $(el);
		this.init();
	}

	ProxyTrigger.prototype.init = function () {
		var that = this,
			$el = this.$el;
		this.$triggerEl = $($el.data('proxy'));
		this.on = $el.data('on');
		this.trigger = $el.data('trigger');

		$el.on(this.on, function (e) {
			that.$triggerEl.trigger(that.trigger);
			e.preventDefault();
		});
	}

	// Plugin Definition
	$.fn.proxytrigger = function () {
		return this.each(function () {
			var $this = $(this),
			data = $(this).data('proxy-trigger');
			if (!data) return $this.data('proxy-trigger', new ProxyTrigger(this));
		});
	}

	// HTML API
	$(function () {
		$('[data-proxy]').proxytrigger();
	});

}(jQuery));
