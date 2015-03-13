function artist_combo(name) {
    var art = jQuery("#id_"+name+"_artist");
    var alb = jQuery("#id_"+name+"_album");
    var pk = jQuery("#id_"+name+"_pk");
    
    art.autocomplete({
        source:'/djpro/artist-list/',
        minLength:3, 
        change: function(event, ui){
            alb.val('');
            pk.val('');
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
    
    alb.autocomplete({
        source: function(request, response){
            $.getJSON('/djpro/album-list/', {artist: art.val(), album: alb.val()}, response);
        }, 
        minLength:3, 
        select: function(event, ui){
             pk.val(ui.item.id);
        },
        change: function(event, ui){
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
    alb.data('autocomplete')._renderItem = function(ul, item){
        var link = jQuery("<a></a>");
        link.text(item.value + " #" + item.location);
        return jQuery("<li></li>").data('item.autocomplete', item).append(link).appendTo(ul);
    };
}
