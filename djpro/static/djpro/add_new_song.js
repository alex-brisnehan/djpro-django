function add_new_song() {
    if ($('#song_form')[0].song.value == "") return;
    $.post("/djpro/album/add_song/", 
           $('#song_form').serialize(), 
           function(data){
               if (data.trim()[0] == '<') {
                   $('#song_list').append(data);
                   $('#song_form')[0].reset();
               } else {
                   window.alert(data);
               }
           }
    );
    
}
