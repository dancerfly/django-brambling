(function ($) {
	"use strict";

	var Shorten = function (el, options) {
		this.$el = $(el);
		this.options = $.extend({}, Shorten.DEFAULTS, this.$el.data(), options);
		this.init();
	};

	Shorten.DEFAULTS = {
		lines: 3,
		moreText: "See More",
		lessText: "See Less",
		moreHtml: "<a href='#' class='shorten-more'>{label}</a>",
		lessHtml: "<a href='#' class='shorten-less'>{label}</a>",
		animationOptionsOpen: {duration: 400},
		animationOptionsClose: {duration: 400}
	}

	Shorten.log = function () {
		/*global console:true */
		if (window.console && console.log)
			console.log('[shorten] ' + Array.prototype.join.call(arguments, ' ') );
	};

	Shorten.prototype.init = function () {
		var line_height = this.get_line_height(),
			shorten_height = line_height * this.options.lines,
			that = this;

		// If the element is already shorter than the specified number of lines,
		// short-circuit.
		if (this.$el.height() <= shorten_height) return;

		// Create more trigger.
		this.$more = $(this.options.moreHtml.replace("{label}", this.options.moreText));
		this.$more.on('click', function (e) {
			that.open(true);
			e.preventDefault();
		});

		// Create less trigger.
		this.$less = $(this.options.lessHtml.replace("{label}", this.options.lessText));
		this.$less.on('click', function (e) {
			that.close(true);
			e.preventDefault();
		});

		// Append the triggers.
		this.$el.after(this.$more).after(this.$less);

		// Shorten the element.
		this.$el.css("overflow", "hidden");
		this.close();

		// Whenever the window resizes, we should clear the natural height cache.
		$(window).on('resize', function () {
			that._natural_height = null;
		});

		// Log
		Shorten.log("Instantiated.");

		return this;
	};

	Shorten.prototype.get_line_height = function () {
		// Return the line-height inside the element.
		var testy = $('<div>X</div>').appendTo(this.$el),
			height = testy.height();
		testy.remove();
		return height;
	};

	Shorten.prototype.get_shorten_height = function () {
		return this.get_line_height() * this.options.lines;
	};

	Shorten.prototype.get_natural_height = function () {
		var saved_height = this.$el.height();
		// If the natural height isn't cached, calculate it.
		if (!this._natural_height) {
			// Let the element spread out.
			this.$el.height("auto");
			// Cache the natural height.
			this._natural_height = this.$el.height();
			// Return the element to its previous height.
			this.$el.height(saved_height);
		}
		return this._natural_height;
	};

	Shorten.prototype.open =  function (animate) {
		var dest = {height: "auto"};
		if (animate) {
			dest = {height: this.get_natural_height()};
			this.$el.animate(dest, this.options.animationOptionsOpen);
			Shorten.log("Element animated to expanded.");
		} else {
			this.$el.css(dest);
			Shorten.log("Element expanded immediately.");
		}
		this.$more.hide();
		this.$less.show();
		return this;
	};

	Shorten.prototype.close = function (animate) {
		var shorten_height = this.get_shorten_height(),
			dest = {height: shorten_height};
		if (animate) {
			this.$el.animate(dest, this.options.animationOptionsClose);
			Shorten.log("Element animated to shortened.");
		} else {
			this.$el.css(dest);
			Shorten.log("Element shortened immediately.");
		}
		this.$more.show();
		this.$less.hide();
		return this;
	};

	// jQuery API
	$.fn.shorten = function (options, arg) {
		return this.each(function () {
			var $this = $(this),
				data = $(this).data('shortened'),
				options_ = typeof options == 'object' && options,
				method;
			// Instatiate formset on element if it not already.
			if (!data) return $this.data('shortened', new Shorten(this, options_));
			// If a string was passed to the function, interpret as an API command.
			if (typeof options == 'string') {
			method = $.fn.shorten.API[options];
			return data[method](arg);
			}
		});
	};

	$.fn.shorten.API = {
		'open': 'open',
		'close': 'close'
	}

	// HTML Data API

	$(function () {
		$('.shortened').shorten();
	});

}(jQuery));
