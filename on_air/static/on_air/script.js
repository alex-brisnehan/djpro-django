$(document).ajaxError(
    function() { alert('A significant problem has occured. While the engineers try to figure it out, why don\'t you try reloading the page.'); }
);

function insert(id){
    var callback = function(data, status){
        var line = $(data).hide()
        $('#line_'+id.replace('.','\\.')).after(line)
        line.show('blind');
        line.showLine();
        console.log(line);
    }
    
    $.ajaxQueue({type: 'POST', url: 'insert/', data: {'id':id}, success: callback, dataType: 'html'});
};

function del(id){
    var callback = function(data, status){
        var line = $('#line_'+data.replace('.', '\\.'))
        line.hide('blind').remove()
    };
    $.ajaxQueue({type: 'POST', url: 'delete/', data: {'id':id}, success: callback, dataType: 'text'});
};

function play(id){
    var callback = function(data, status){
        for (result in data) {
            var line = $('#line_'+result);
            line.children('.time').text(data[result]);
            if (data[result]) {
                line.attr('class', 'played');
                line.children('.play').html('Played');
            } else if (line.attr('class') == 'played') {
                line.attr('class', 'odd');
                line.children('.play').html('Play');
            }
        }
    }
    $.ajaxQueue({type: 'POST', url: 'play/', data: {'id':id}, success: callback, dataType: 'json'});
}

// Show the manual edit form
function edit(id){
    var form = $('#edit_form');
    if (form[0].line.value == id) {
        change();
        return;
    }
    
    var art = form.children('[name=artist]');
    var son = form.children('[name=song]');
    var line = $('#line_'+id).children('.info');
    
    form.insertBefore(line);
    
    form.show();
    art.show();
    son.show();
    art.focus();
    
    form[0].line.value = id;
    form[0].artist.value = line.children('.artist').text();
    art.select();
    // Trim the #location from the end of the song
    var match = line.children('.song').text().match("^(.+) #[^#]+$")
    form[0].song.value = match ? match[1] : "";
    form[0].song_id.value = null;
}

// change the song based on the the manual edit form
function change(form){
    
    if (!form) form = document.getElementById('edit_form');
    
    if (!form.song_id.value && !form.artist.value) {
        $(form).hide();
        form.line.value = null;
        return;
    }
    
    var callback = function(data, status, request) {
        $('#line_'+data.id).children('.info').html(data.song);
        $('#line_'+data.id).children('.concert').html(data.concert);
        $('#line_'+data.id).showLine();
        
        $(form).hide();
        form.song_id.value = null;
        form.line.value = null;
    }
    
    $.ajaxQueue({type: 'POST', url: 'change/', data: $(form).serialize(), success: callback, dataType: 'json'});
    
    return false;
}

function update_tt(){
    var callback = function(data, status, request){
        for(var i in data) {
            var line = $('#line_'+data[i].id);
            line.children('.info').html(data[i].song);
            line.children('.concert').html(data[i].concert);
            line.children('.time').text(data[i].played);
            line.attr('class', 'played');
            line.children('.play').html('Played');
            line.showLine();
        }
    }

    $.ajaxQueue({type: 'GET', url: 'tune_tracker_update/', success: callback, dataType: 'json'});
}
setInterval(update_tt, 1000);

jQuery.fn.showLine = function() {
    // Calculate the top and bottom of the line and window
    var line_top = this.offset().top;
    var line_bottom = line_top + this.outerHeight() + 18; // height of insert tab
    var win_top = $(window).scrollTop() + 45; //std height of the header
    var win_bottom = win_top + $(window).height();
    
    // If any of the line is hidden, move to show them all
    if (line_top < win_top) {
        var new_top = line_top - 54;
    } else if (line_bottom > win_bottom) {
        var new_top = line_bottom - $(window).height() + 9;
    } else {
        return;
    }
    
    // And animate it.
    $('body, html').animate({scrollTop: new_top}, 400);
};

$(function(){
    
    // Allow drag & drop reordering.
    $('#list').sortable({axis:'y', containment: 'parent', scroll: false, distance: 4, cancel: 'a,select',
        start: function(event, ui){
            // Make a note of the original position in case somthing goes wrong
            if (ui.item.prev().length) {
                ui.item.attr('return_to', ui.item.prev().attr('id').substring(5));
            } else {
                ui.item.attr('return_to', 'top');
            }
        },
     
        update: function(event, ui){
            var after = ui.item.prev().attr('id').substring(5);
            var id = ui.item.attr('id').substring(5);
         
            var fail = function(data, status){
                var old = ui.item.attr('return_to');
                if (old == 'top') {
                    ui.item.parent().prepend(ui.item);
                } else {
                    $('#line_'+old).after(ui.item);
                }
            };
        
            var callback = function(data, status) {
                for (result in data) {
                    var line = $('#line_'+result);
                    line.children('.time').text(data[result]);
                    if (data[result]) {
                        line.attr('class', 'played');
                    } else if (line.attr('class') == 'played') {
                        line.attr('class', 'odd');
                    }
                }
            }
        
            $.ajaxQueue({type: 'POST', url: 'move/', data: {'id':id, 'after':after}, error: fail, success:callback, dataType:'json'})
        }
    });
    
    // Autocomplete the artist in the manual field
    $('input[name=artist]').autocomplete({
        source: '/djpro/artist-list/',
        minLength:3,
        change: function(event, ui){
            $('input[name=song]').val('');
            $('input[name=song_id]').val('');
            if (ui.item || this.value == '') { return false; }
            var input = $(this);
            var menu = input.data('autocomplete').menu;
            var match = false;
            menu.element.children().each(function(i){
                if ($(this).data('item.autocomplete').value.toLowerCase() == input.val().toLowerCase()) {
                    match = true;
                    return false;
                }
            });
            if ( !match )
                input.val( menu.element.children(':first-child').data('item.autocomplete').value );
        }
    });
    
    // Autocomplete the song
    $('input[name=song]').autocomplete({
        source: function(request, response) {
            $.getJSON('/djpro/onair/song-list/', {artist: $('input[name=artist]').val(), song: $('input[name=song]').val()}, response);
        },
        minLength:3, 
        select: function( event, ui ){
            $('input[name=song_id]').val(ui.item.id);
        },
        change: function(event, ui){
            if (ui.item || this.value == '') { return false; }
            var input = $(this);
            var menu = input.data('autocomplete').menu;
            var match = false;
            menu.element.children().each(function(i){
                var item = $(this).data('item.autocomplete');
                if (item.value.toLowerCase() == input.val().toLowerCase()) {
                    $('input[name=song_id]').val( item.id );
                    match = true;
                    return false;
                }
            });
            if ( !match ) {
                input.val( menu.element.children(':first-child').data('item.autocomplete').value );
                $('input[name=song_id]').val( menu.element.children(':first-child').data('item.autocomplete').id );
            }
        }
    });
    
    // Jump to start of editable
    $(window).scrollTop($('#list').offset().top-189);
    
});

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

