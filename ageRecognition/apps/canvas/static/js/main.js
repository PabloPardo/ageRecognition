(function (window, $) {
	'use strict';

	// Cache document for fast access.
	var document = window.document;


	function mainSlider() {
		$('.bxslider').bxSlider({
			pagerCustom: '#bx-pager',
			mode: 'fade',
			nextText: '',
			prevText: ''
		});
	}

	mainSlider();



	var $links = $(".bx-wrapper .bx-controls-direction a, #bx-pager a");
	$links.click(function(){
	   $(".slider-caption").removeClass('animated fadeInLeft');
	   $(".slider-caption").addClass('animated fadeInLeft');
	});

	$(".bx-controls").addClass('container');
	$(".bx-next").addClass('fa fa-angle-right');
	$(".bx-prev").addClass('fa fa-angle-left');


	$('a.toggle-menu').click(function(){
        $('.responsive .main-menu').toggle();
        return false;
    });

    $('.responsive .main-menu a').click(function(){
        $('.responsive .main-menu').hide();

    });

    $('.main-menu').singlePageNav();


})(window, jQuery);

function showValue(id, newValue)
{
	document.getElementById(id).innerHTML=newValue;
};


//Google Analytics code:
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-39111866-1', 'auto');
  ga('send', 'pageview');


// DROPZONE CONFIGURATION
//Dropzone.options.myAwesomeDropzone = {
//
//    // Properties configuration
//    autoProcessQueue: false,
//    paramName: "pic",
//    maxFiles: 10,
//    addRemoveLinks: true,
//
//    // The setting up of the dropzone
//    init: function() {
//        var myDropzone = this;
//
//        myDropzone.on("sending", function(file, xhr, formData) {
//            formData.append("pic", file);
//        });
//
//    }
//}
