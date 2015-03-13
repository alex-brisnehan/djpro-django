/* This is always presented to the user as "Play". Takes a song id 
passes it to the playlist edit form to let it deal with it.*/
function add_to_playlist(id, played_recently) {
    if (!window.opener || !window.opener.document.forms) {
        window.alert("There is a problem with the playlist. Please close this tab and add the song manually.");
        return;
    }
    if (played_recently && !confirm("This song or artist has been played recently. Are you sure you want to play it again?")) {
        return;
    }
    var form = window.opener.document.forms['edit_form']
    form['song_id'].value = id;
    window.opener.change();
    window.close();
}

/* Called from the actual song_form where the data is taken from. */
function add_new_song() {
    $.post("/djpro/onair/add_song/", 
      $('#song_form').serialize(), 
      function(data){if (data[0] == '<')
                     {$('#song_list').append(data);$('#song_form')[0].reset();}
                     else
                     {window.alert(data)};}
    );
    
}

// Attach CSRF to all AJAX calls. 
$('html').ajaxSend(function(event, xhr, settings) {
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
    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
        // Only send the token to relative URLs i.e. locally.
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});
