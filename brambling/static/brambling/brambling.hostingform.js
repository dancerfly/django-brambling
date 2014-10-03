/**
 * Brambling Slug
 * @author Harris Lapiroff
 * @requires jQuery
 *
 * This is very Brambling-specific and currently refers specifically to
 * Brambling-specific field names and classes.
 *
 * Copyright (c) 2014, Little Weaver Web Collective
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 *
 */

(function () {
    "use strict";

    var HOSTING_FORM_SEL = '#HostingFormTable',
        SPACES_INPUTS_SEL = '[id$="-spaces"]',
        SPACES_MAX_INPUTS_SEL = '[id$="-spaces_max"]',
        SPACES_ALL_INPUTS_SEL = [SPACES_INPUTS_SEL, SPACES_MAX_INPUTS_SEL].join(","),
        FILL_ALL_BTN_SEL = "#FillAllButton",
        brambling = window.brambling;

    brambling.hosting_form = {};

    brambling.hosting_form.fillFromFirstField = function () {
        // Fill all fields with the value in the first field.
        var value = brambling.hosting_form.$firstField.val();
        brambling.hosting_form.$spacesInputsAll.val(value);
    };

    brambling.hosting_form.fillFromFirstRow = function () {
        // Fill all rows with the values from the first field in their column.
        var spaces_val = brambling.hosting_form.$firstField.val(),
            spaces_max_val = brambling.hosting_form.$firstMaxField.val();
        brambling.hosting_form.$spacesInputs.val(spaces_val);
        brambling.hosting_form.$spacesInputsMax.val(spaces_max_val);
    };

    $(function () {
        // All this stuff should be run once the DOM is ready.

        // Let's lasso all the elements we wanna play with:
        brambling.hosting_form.$el = $(HOSTING_FORM_SEL);
        brambling.hosting_form.$fillAllButton = brambling.hosting_form.$el.find(FILL_ALL_BTN_SEL);
        brambling.hosting_form.$spacesInputs = brambling.hosting_form.$el.find(SPACES_INPUTS_SEL);
        brambling.hosting_form.$spacesInputsMax = brambling.hosting_form.$el.find(SPACES_MAX_INPUTS_SEL);
        brambling.hosting_form.$spacesInputsAll = brambling.hosting_form.$el.find(SPACES_ALL_INPUTS_SEL);
        brambling.hosting_form.$firstField = brambling.hosting_form.$spacesInputs.eq(0);
        brambling.hosting_form.$firstMaxField = brambling.hosting_form.$spacesInputsMax.eq(0);
        brambling.hosting_form.mode = "untouched"; // options are "untouched", "max_touched", "touched"

        brambling.hosting_form.$fillAllButton.on('click', function (e) {
            // On clicking the button, fill all rows.
            brambling.hosting_form.fillFromFirstRow();
            e.preventDefault();
        });

        brambling.hosting_form.$firstField.on('change.hosting_form_u keypress.hosting_form_u keyup.hosting_form_u blur.hosting_form_u', function (e) {
            if (brambling.hosting_form.mode == "untouched") {
                // If no other fields on this form have been touched, fill all with this value:
                brambling.hosting_form.fillFromFirstField();
            } else if (brambling.hosting_form.mode == "max_touched") {
                // If both columns have been touched, fill all fields with their corresponding column head:
                brambling.hosting_form.fillFromFirstRow();
            } else if (brambling.hosting_form.mode == "touched") {
                // If other fields have been touched, unbind the events:
                brambling.hosting_form.$firstField.off('.hosting_form_u');
            }
        });

        brambling.hosting_form.$firstMaxField.on('change.hosting_form_u keypress.hosting_form_u keyup.hosting_form_u blur.hosting_form_u', function (e) {
            // Change the mode, since we've now touched the max field:
            if (brambling.hosting_form.mode == "untouched") brambling.hosting_form.mode = "max_touched";
            if (brambling.hosting_form.mode == "max_touched") {
                // If only the first rows have been touched, fill all others from the first row:
                brambling.hosting_form.fillFromFirstRow();
            } else if (brambling.hosting_form.mode == "touched") {
                // If other fields have been touched, unbind the events:
                brambling.hosting_form.$firstMaxField.off('.hosting_form_u');
            }
        });

        // The first time a field is touched that's not the top two fields, set the mode to "touched"
        brambling.hosting_form.$spacesInputsAll
            .not(brambling.hosting_form.$firstField)
            .not(brambling.hosting_form.$firstMaxField)
            .one('change.hosting_form', function (e) {
                brambling.hosting_form.mode = "touched";
            });

        // If a spaces field is updated and is larger than the max field, bump the max field up to match.
        brambling.hosting_form.$spacesInputs.on('change.hosting_form keypress.hosting_form keyup.hosting_form blur.hosting_form', function (e) {
            var $this = $(this),
                $maxField = $this.parents('td').next().find(SPACES_MAX_INPUTS_SEL);

            if (parseInt($this.val()) > parseInt($maxField.val())) {
                $maxField.val($this.val());
                $maxField.trigger('change');
            }
        });

        // Check if any of the fields are non-zero. If they are, switch straight to "touched" mode.
        brambling.hosting_form.$spacesInputsAll.each(function () {
            var $this = $(this);
            if (parseInt($this.val()) != 0) {
                brambling.hosting_form.mode = "touched";
                return false; // break
            };
        });
    }); // end domready

}());
