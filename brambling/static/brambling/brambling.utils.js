// Some simple Javascript utilities to be used wherever:

;(function () {
	"use strict";

	// Filters to be used in Ractive mustaches:
	brambling.filters = {
		// Wraps a bit of text in an element:
		highlight: function (needle, haystack, open_tag, close_tag) {
			var open = open_tag || "<mark class='highlight'>",
			 	close = close_tag || "</mark>",
				pos = 0,
				returnVal = haystack,
				needle = needle.toLowerCase();

			if (!needle) return;

			// Find all occurrences:
			while (pos !== -1) {
				pos = haystack.toLowerCase().indexOf(needle, pos);
				if (pos === -1) break;
				returnVal = returnVal.substring(0, pos) + open + returnVal.substring(pos, pos + needle.length) + close + returnVal.substring(pos + needle.length);
				pos = pos + needle.length + open.length + close.length;
			}

			return returnVal;
		}
	};

}());
