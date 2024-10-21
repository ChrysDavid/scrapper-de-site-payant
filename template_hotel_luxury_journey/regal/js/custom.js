(function (jQuery) {
    "use strict";
    // Parallax Backgrounds
    jQuery.stellar({
        horizontalScrolling: false,
        scrollProperty: 'scroll',
        positionProperty: 'position'
    });
    // Generals Backgrounds
    jQuery('.bg-image').each(function(){
        var url = jQuery(this).attr("data-image");
        if(url){
            jQuery(this).css("background-image", "url(" + url + ")");
        }
    });
    // Search Overlay
    jQuery('.top-search').on('click',function(e){
        e.preventDefault();
        jQuery('.search-overlay').show();
    });
    jQuery('button.search-close').on('click',function(e){
        e.preventDefault();
        jQuery('.search-overlay').hide();
    });
    // BG Color
    jQuery('section,div').each(function(){
        var bg_color = jQuery(this).attr("data-color");
        if(bg_color){
            jQuery(this).css("background-color", "" + bg_color + "");
        }
    });
    // Image Pop Up
    window.Lightbox = new jQuery().visualLightbox({
        autoPlay: false,
        borderSize: 7,
        classNames: 'lbox',
        closeLocation: 'top',
        descSliding: true,
        enableRightClick: false,
        enableSlideshow: true,
        pauseLocation: 'imageContainerMain',
        prefix: 'vlb1',
        resizeSpeed: 7,
        slideTime: 4,
        startZoom: true
    });
  
    // Isotope Gallery/Rooms
    var jQuerycontainer = jQuery('.portfolioContainer');
    jQuerycontainer.imagesLoaded().progress( function() {
        jQuerycontainer.isotope({
            itemSelector: '.port-item',
            animationOptions: {
                duration: 1000,
                easing: 'linear',
                queue: false
            },
            percentPosition: true,
            masonry: {
                columnWidth: '.port-item'
            }
        });
    });
    // Site Pre Loader -- also uncomment the div in the header and the css style for #preloader
    jQuery(window).load(function(){
        jQuery('#preloader').fadeOut(
            'slow',
            function(){
                jQuery(this).remove();
            });
    });
    // Calculate Container Width For Safari
    var jQuerywindow = jQuery(window).on('resize', function(){
        if (navigator.userAgent.indexOf('Safari') != -1 &&
            navigator.userAgent.indexOf('Chrome') == -1) {
            jQuery('.portfolioContainer').each(function(){
                var width = jQuery(window).width();
                if ((width > 767)) {
                    jQuery(this).addClass('margin-0-auto');
                    var widtho = jQuery(this).width();
                    var calc_width = widtho - 15;
                    jQuery(this).css('width',calc_width+'px');
                }
            });
        }
    }).trigger('resize');
    if (navigator.userAgent.indexOf('Safari') != -1 &&
        navigator.userAgent.indexOf('Chrome') == -1) {
        jQuery('.portfolioContainer').each(function(){
            var width = jQuery(window).width();
            if ((width > 767)) {
                jQuery(this).addClass('margin-0-auto');
                var widtho = jQuery(this).width();
                var calc_width = widtho - 15;
                jQuery(this).css('width',calc_width+'px');
            }
        });
    }
    // Gallery/Rooms Overlay
    jQuery( ".portfolioContainer .inner" ).hover(
        function() {
            jQuery(this).find('.overlay-body').slideDown();
            jQuery(this).find('.outer-overlay').css('opacity',1);
        }, function() {
            jQuery(this).find('.overlay-body').slideUp();
            jQuery(this).find('.outer-overlay').css('opacity',0);
        }
    );
    // Single Room Slider Thumbs
    jQuery('.slider-thumbs').each(function(){
        var count = jQuery(this).children().length;
        var percent = 100/count;
        if(count > 3){
            jQuery(this).find('li').css("width", "" + percent + "%");
        }
    });// Animated Progress Bar
    jQuery('.progress-bars').waypoint(function() {
            jQuery('.progress').each(function(){
                jQuery(this).find('.progress-bar').animate({
                    width:jQuery(this).attr('data-percent')
                },200);
            });},
        {
            offset: '100%',
            triggerOnce: true
        });
    // WOW
    new WOW().init();
})(jQuery);