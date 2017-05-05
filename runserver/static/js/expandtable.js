

function expand_children(arrow, this_level, this_name, only_hide) {
    /*"""
    .. function:: expand_children(arrow, this_level, this_name, only_hide)

       This function expands or collapses the rows underneath a given header.
       The collapsing happens recursively.

       :param arrow: Is the span that holds an arrow icon. To be changed by this function
       :param this_level: Tells what level the row expansion is on. (0, 1, or 2, for example)
       :param this_name: Give the name of the row doing the expansion.
       :param only_hide: Set this to true for recursive collapsing. Prevents expansion when not desired.
    */

    if (arrow.innerHTML.charCodeAt(0) == '9654' && !only_hide)    // If sideways arrow and not only hiding
        arrow.innerHTML = '&#x25BC;';                             // Change to down arrow
    else                                                          // Otherwise
        arrow.innerHTML = '&#x25B6;';                             // Change to sideways

    var rows = document.getElementsByClassName('child_of_' + this_level + '_' + this_name);

    for (row = 0; row < rows.length; row++) {
        new_id = rows[row].id;
        if (rows[row].style.display == 'none' && !only_hide) {
            rows[row].style.display = '';
        } else {
            rows[row].style.display = 'none';
            if (parseInt(this_level) < 1) {
                expand_children(document.getElementById(new_id + '_span'),
                                (parseInt(this_level) + 1).toString(),
                                new_id, true);
            }
        }
    }
}
