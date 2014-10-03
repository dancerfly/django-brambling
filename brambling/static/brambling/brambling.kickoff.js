// A happy little namespace for us to use:
(function () { var brambling = window.brambling = {}; }());

// From https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
$.ajaxSetup({
    crossDomain: false, // obviates need for sameOrigin test
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$(function() {

    // Prevent disabled links from doing anything.
    $('.disabled a').on('click', function(e){e.preventDefault();});

    // Add tooltips to elements with class "tipped".
    $('.tipped').tooltip();

    // Add popovers to elements with class "popover-dismiss".
    $('.popped').popover({trigger: "focus"});

    // Bind some brambling-specific events to the countdown timer.
    $('[data-countdown="timer"]').on("updated.countdown", function (e, data) {
        var alert,
            alert_levels = [
                "alert-info",
                "alert-warning",
                "alert-danger"
            ];
        // Give different colors at < 3 and > 0 minutes left.
        if (data.days == 0 && data.hours == 0) {
            if (data.minutes < 3 && data.minutes > 0) {
                alert = $(this).closest(".alert");
                if (alert.hasClass(alert_levels[0])) alert.removeClass(alert_levels[0]).addClass(alert_levels[1]);
            } else if (data.minutes < 1 && data.seconds > 0) {
                alert = $(this).closest(".alert");
                if (alert.hasClass(alert_levels[0])) alert.removeClass(alert_levels[0]).addClass(alert_levels[2]);
                if (alert.hasClass(alert_levels[1])) alert.removeClass(alert_levels[1]).addClass(alert_levels[2]);
            }
        }
    });
    // Upon countdown completion, display a modal which cannot be dismissed.
    $('[data-countdown="timer"]').on("completed.countdown", function (e) {
        $("#countdownCompleteModal").modal({
            keyboard: false,
            show: true,
            backdrop: "static"
        });
    });

});
