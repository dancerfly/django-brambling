;(function () {
	"use strict";

	var Stepbar = window.components.Stepbar = Ractive.extend({

		isolated: true,
		data: function () {
			return {steps: []};
		},

		getStep: function (key) {
			// Return first step with matching key.
			// Returns an object with 'step' and 'index'.
			var steps = this.get('steps'),
				needleIndex = _.findIndex(steps, function (step) { return step.key === key; });
			return {step: steps[needleIndex], index: needleIndex};
		},

		setAccessible: function (key, val) {
			// Update `is_accessible` on specified step. If no val is provided, defaults to true.
			var val = (typeof(val) === "undefined") ? true : val,
				step = this.getStep(key);
			this.set('steps.' + step.index + '.is_accessible', val)
		},

		setCompleted: function (key, val) {
			// Update `is_completed` on specified step. If no val is provided, defaults to true.
			var val = (typeof(val) === "undefined") ? true : val,
				step = this.getStep(key);
			this.set('steps.' + step.index + '.is_completed', val)
		},

		setActive: function (key, val) {
			// Update `is_active` on specified step. If no val is provided, defaults to true.
			var val = (typeof(val) === "undefined") ? true : val,
				step = this.getStep(key),
				steps = this.get('steps');
			// Set all steps to inactive:
			newSteps = _.map(steps, function (step) { step.is_active = false; return step; })
			this.set('steps', newSteps);
			// Set specified step to active:
			this.set('steps.' + step.index + '.is_active', val)
		},

		getNextAfter: function (key, val) {
			// Get the next step that comes after the step with specified key.
			var step = this.getStep(key);
			return this.get('steps.'+(step.index+1));
		},

		getPreviousBefore: function (key, val) {
			// Get the previous step that comes before the step with specified key.
			var step = this.getStep(key);
			if (step.index === 0) return null;
			return this.get('steps.'+(step.index-1));
		}

	});

}());
