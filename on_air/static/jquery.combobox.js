/***************************************************
 Native Combo Box
 by Peter of the Norse <RahmCoff@Radio1190.org>
 2011-04-14

 What is a combo box? It's a text box with a menu of
 selections. Useful when any value is possible, but
 a few are common. 
 
 It takes one required argument, either something that
 translates to a <select> element, or an array that it
 turns into a <select> element.
 
 example:
 $('[name=salutation]').combobox(['Mr.', 'Ms.', 'Dr.']);

 Issues:
 Looks like crap when input boxes or pop-up menus are 
 styled. There are other comboboxes for that.

 I know it uses the deprecated jQuery.browser methods,
 but there are important differnences between how
 browsers render. I wish there was a better way to find
 out which engine/OS/version we're on.
***************************************************/

jQuery.fn.combobox = function(select){
  //Build a select element
  if (select.constructor == Array) {
    var sel = jQuery('<select>');
    for (var key in select) {
      sel.append(jQuery('<option>').text(select[key]));
    }
  } else {
    var sel = jQuery(select);
    if (sel.length != 1) return;
 }
  
  sel.change(function() {
    var sel = jQuery(this);
    sel.prev().val(sel.val());
    sel.prev().select();
    sel.prev().attr('pop_up_selection', sel.attr('selectedIndex'));
    sel.attr('selectedIndex', -1);
  })
  sel.attr('tabindex', -2); //Don't get tabbed to

  
  this.each(function(i){
    var input = $(this);
    if (i>0) var menu = sel.clone(true); 
    else var menu = sel; //don't leave an extra lying around
    
    input.wrap(jQuery('<span></span>').css('position', 'relative'));
    input.after(menu);
    
    input.data('native-combobox', { selected_index: -1, typed_value: input.val() });

    input.css('margin-right', '16px');
    input.keydown(function(event) { 
      var input = $(this);
      var sel = input.next()[0];
      var data = input.data('native-combobox');
      if (event.keyCode == 40) {
        sel.selectedIndex = data.selected_index+1;
        data.selected_index = sel.selectedIndex;
	if (sel.selectedIndex != -1) {
          input.next().change();
        } else {
          input.val(data.typed_value);
        }
        return false;
      }
      if (event.keyCode == 38) {
        sel.selectedIndex = data.selected_index == -1 ? sel.length-1 : data.selected_index-1;
        data.selected_index = sel.selectedIndex;
	if (sel.selectedIndex != -1) {
          input.next().change();
        } else {
          input.val(data.typed_value);
        }
        return false;
      }
      data.typed_value = input.val();
    });
    var width = input.width() - 0;
    var style;
    
    //Might have to be updated depending on the version or OS.
    //Let me know when jQuery adds support for OS.
    if (jQuery.browser.msie) {
      style = {clip: 'rect(0 '+(width+22)+'px 30px '+(width+5)+'px)',
        position: 'absolute',
        left: 0,
        top: '1px',
        width: (width+22)+'px'};
    } else if (jQuery.browser.opera) {
      width = input.parent().width();
      style = {clip: 'rect(0 '+(width+2)+'px 30px '+(width-15)+'px)',
        position: 'absolute',
        left: 0,
        top: '1px',
        width: (width+2)+'px'};

    } else if (jQuery.browser.safari) {
      style = {clip: 'rect(0px, '+(width+18)+'px, 30px, '+(width+2)+'px)',
        position: 'absolute',
        right: '0',
        bottom: '0',
        width: (width+18)+'px'};
    } else { // Mozilla
      style = {clip: 'rect(0px, '+(width+22)+'px, 30px, '+(width+4)+'px)',
        position: 'absolute',
        right: '0',
        width: (width+22)+'px',
        top:'0'};
    }
    
    menu.attr('selectedIndex', -1);
    menu.css(style);
  });
  
  return this;
};
