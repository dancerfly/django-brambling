/**
 * Brambling Slug
 * @author Harris Lapiroff
 * @requires jQuery,
 *           Django Contrib Admin prepopulate.js,
 *           Django Contrib Admin urlify.js
 *
 * This is very Brambling-specific and currently refers specifically to
 * Brambling-specific field names from the event create and event update forms.
 *
 * Copyright (c) 2020, Harris Lapiroff
 * All rights reserved.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 *
 */

(function () {
    "use strict";

    var FIELD_SELECTOR = '#id_slug',
        DEPENDENCY_SELECTORS = ['#id_name'];

    $(function () {
        $(FIELD_SELECTOR).prepopulate(DEPENDENCY_SELECTORS);
    });
}());
