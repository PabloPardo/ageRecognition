function showMenu() {
    // TODO: When hiding the menu and enlarging the window, the menu still hidden.
    var menu = document.getElementsByClassName('main-menu');
    if (menu[0].style.display == "block"){
        menu[0].style.display = "none";
    } else {
        menu[0].style.display = "block";
    }
}

function showValue(id, newValue)
{
	document.getElementById(id).value=newValue;
}
function showValue1(id, newValue)
{
	document.getElementById(id).innerHTML=newValue;
}

var lsLabeled = new Array(0);
function enableSubmit(nimg, id){
    var found = false;
    for(var i=0;i<lsLabeled.length;i++){
        if(lsLabeled[i] == id){
            found = true;
            break;
        }
    }

    if(!found) lsLabeled.push(id);
    if(lsLabeled.length >= nimg){
        document.getElementById('submitButton').disabled = false;
    }
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
        location.reload(true);
    }
}

function calculateScore(id_value, gt) {
    var guess = document.getElementById(id_value).innerHTML;
    var error = Math.abs(parseInt(guess) - gt);
    var score;
    if(error > 10) {
        score = 5;
    }
    else {
        score = 3*(10 - error);
    }
    return score;
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



