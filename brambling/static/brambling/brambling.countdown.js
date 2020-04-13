/**
 * jQuery Countdown
 * @author Harris Lapiroff
 * @requires jQuery
 *
 * Copyright (c) 2020, Harris Lapiroff
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 *
 * Documentation
 * -------------
 *
 * Events
 * ======
 *
 * * initialized.countdown -- Triggered when a coundown is first initialized.
 * * pre_update.countdown  -- Triggered just before the countdown is updated.
 *                            Receives a data  object with seconds, minutes,
 *                            hours, and days.
 * * updated.countdown     -- Triggered after the countdown is updated. Receives
 *                            a data object with seconds, minutes, hours, days.
 * * completed.countdown   -- Triggered when the countdown reaches
 *                            0 days 0:00:00.
 */

(function () {
	var Countdown = function (el) {
		this.$el = $(el);
		this.init();
	};

	Countdown.prototype.init = function () {
		var countdown = this;

		this.$seconds = this.$el.find('[data-countdown="seconds"]');
		this.$minutes = this.$el.find('[data-countdown="minutes"]');
		this.$hours = this.$el.find('[data-countdown="hours"]');
		this.$days = this.$el.find('[data-countdown="days"]');


		// Store when the counter started. We'll use this to calculate how
		// long it has been since the original values. This is more robust than
		// simply decrementing once per second since javascript timeouts
		// are not reliably accurate.
		this.started = new Date();

		this.original_values = {
			seconds: parseInt(this.$seconds.html()) || 0,
			minutes: parseInt(this.$minutes.html()) || 0,
			hours: parseInt(this.$hours.html()) || 0,
			days: parseInt(this.$days.html()) || 0
		}

		this.total_original_seconds = 0;
		this.total_original_seconds += this.original_values.seconds;
		this.total_original_seconds += this.original_values.minutes * 60;
		this.total_original_seconds += this.original_values.hours * 3600;
		this.total_original_seconds += this.original_values.days * 86400;

		this.set_timeout();

		if (window.console && console.log) console.log("[countdown] Countdown timer initialized.");

		this.$el.trigger("initialized.countdown");

		return this;
	};

	Countdown.prototype.ms_since_start = function () {
		var current_time = new Date();
		return current_time - this.started;
	};

	Countdown.prototype.set_timeout = function () {
		var countdown = this;
		// setInterval is evil. Long live setTimeout.
		this.timeout = window.setTimeout(function () {
			countdown.update();
		}, 1000);
	};

	Countdown.prototype.update = function () {
		var countdown = this,
			ms_since_start = this.ms_since_start(),
			s_since_start = Math.floor(ms_since_start/1000),
			seconds_left = Math.max(0, this.total_original_seconds - s_since_start),
			new_values = {
				seconds: seconds_left % 60,
				minutes: Math.floor(seconds_left/60) % 60,
				hours: Math.floor(seconds_left/3600) % 24,
				days: Math.floor(seconds_left/86400)
			};
		this.$el.trigger("pre_update.countdown", [new_values]);
		// Update the element:
		this.$seconds.html(new_values.seconds < 10 ? "0" + new_values.seconds : new_values.seconds); // always pad to two digits
		this.$minutes.html(new_values.minutes < 10 && (new_values.hours || new_values.days) ? "0" + new_values.minutes : new_values.minutes); // pad to two digits if there are days or hours present
		this.$hours.html(new_values.hours);
		this.$days.html(new_values.days);
		this.$el.trigger("updated.countdown", [new_values]);
		// If seconds left is zero, trigger completed:
		if (seconds_left === 0) {
			this.$el.trigger("completed.countdown");
			if (window.console && console.log) console.log("[countdown] Countdown timer completed.");
		}
		// Set a new timeout, unless the timer has run out:
		if (seconds_left > 0) this.set_timeout()
	};

	// Plugin Definition

	$.fn.countdown = function () {
		return this.each(function () {
			var $this = $(this),
			data = $(this).data('countdown-timer');
			if (!data) return $this.data('countdown-timer', new Countdown(this));
		});
	};

	// HTML Data API

	$(function () {
		$('[data-countdown="timer"]').countdown();
	});

}());
