/*
* jquery-backgroundMove master by sameera liyanage
* License MIT
$('element').backgroundMove();
*/
(function($) {
    $.fn.backgroundMove = function(options) {
        var defaults = {
                movementStrength: '50'
            },
            options = $.extend(defaults, options);

        var $this = $(this);

        var movementStrength = options.movementStrength;
        var height = movementStrength / $(window).height();
        var width = movementStrength / $(window).width();
        $this.mousemove(function(e) {
            var pageX = e.pageX - ($(window).width() / 2);
            var pageY = e.pageY - ($(window).height() / 2);
            var newvalueX = width * pageX * -1 - 25;
            var newvalueY = height * pageY * -1 - 50;
            $this.css("background-position", newvalueX + "px     " + newvalueY + "px");
        });

    }
})(jQuery);


/* Jquery Init */
(function($) {
    "use strict";

    $(document).on('ready', function() {
        $('.background-move').backgroundMove({
            movementStrength: '50'
        });
    }); // end document ready function
})(jQuery); // End jQuery