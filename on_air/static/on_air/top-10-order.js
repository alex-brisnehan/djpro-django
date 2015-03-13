/* Automaticly reordering javascript. This is *very* brittle. An update 
to Django or the underling models may break this.*/

function reorder() {
    var order = 1;
    $(".dynamic-albums").each(function(i, e){
        var id = e.id;
        // Only count those with an album
        if ($('#id_'+id+'-album_pk').val() == "") {
           $('#id_'+id+'-rank').val("");
           return;
        }
        // Skip those about to be deleted
        if ($('#id_'+id+'-DELETE').is(':checked')) {
           $('#id_'+id+'-rank').val("");
           return;
        }
        
        $('#id_'+id+'-rank').val(order);
        order++;
    })
}

$(function(){
$(".dynamic-albums").each(function(i, e){
    var id = e.id;
    
    //Make the rank look good. and skip on tab
    $('#id_'+id+'-rank').css({border: 'none', backgroundColor: 'transparent'}).attr('tabindex', '-1');
    
    //reorder on changes
    $('#id_'+id+'-album_artist').blur(reorder);
    $('#id_'+id+'-album_album').blur(reorder);
    $('#id_'+id+'-DELETE').change(reorder);
});

$(".dynamic-albums").parent().sortable({containment:'parent', update:reorder});

reorder();
});

