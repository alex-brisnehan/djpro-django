jQuery( function(){ 
  jQuery('input.ages').combobox(['21+', '16+', 'All']);
  jQuery('input#id_location').combobox($('<select><option></option><option value="NIL">Not In Library</option><option>Vinyl 33</option><option>7" Vinyl</option><option>Vinyl Comp</option><option>Vinyl Soundtrack</option><option>Hip-Hop Wax</option><option>Metal</option><option>Reggae</option><option>Jazz Vinyl</option></select>'));
})
