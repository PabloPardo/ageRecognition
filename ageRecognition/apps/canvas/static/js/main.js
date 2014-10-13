
function showValue(id, newValue)
{
	document.getElementById(id).innerHTML=newValue;
}

function showSave() {
   document.getElementById('save').style.visibility = 'visible';
}

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

function rmFormSubmit(id_rm) {

    var csrftoken = getCookie('csrftoken');
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", "/gallery/"+id_rm, false);
    xmlhttp.setRequestHeader("X-CSRFToken", csrftoken);
    xmlhttp.send();

    if (xmlhttp.status === 200) {
        location.reload();
    }
}

function hideSave() {
   document.getElementById('save').style.visibility = 'hidden';
}

//Google Analytics code:
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-39111866-1', 'auto');
  ga('send', 'pageview');



