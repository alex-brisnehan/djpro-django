jQuery(function($){
    $('input.artist').each(function(i){
        $(this).autocomplete({
            source: '/djpro/artist-list/', 
            minLength: 3,
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
    });
    
    $('input.opt_artist').each(function(i){
        $(this).autocomplete({
            source: '/djpro/artist-list/',
            minLength: 3
        });
    });
})
