/*"""
.. _addreason-ref:

addreason.js
++++++++++++

This file contains the functions used to add reasons to the :ref:`workflow-view-ref`
The fields added by this script are handled by the :py:mod:`WorkflowWebTools.reasonsmanip` module.

.. todo::

  This is some of the messiest code in the package.
  Need to impliment some JSLint check.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/

var count = 0;
/*"""
.. data:: count

   Keeps track of the number of reasons on a given page.   
*/  

function getDefaultReason(num) {
    /*"""
    .. function:: getDefaultReason(num)

      This function is used to generate a new reason on the :ref:`workflow-view-ref`.
      Each name and ID is unique so that the short and long reasons can be matched.

      :param int num: is a unique number for each reason submitted on the current page.
      :returns: the innerHTML for a reason div when a new one is generated.
      :rtype: str
    */

    return ''
        + 'Short Reason: <br>'
        + '<input type="text" name="shortreason' + num + '" id="shortreason' + num + '" '
        + 'onkeyup="checkReason(' + num + ')"></input> '
        + '<div style="color:#ff0000; width=12em;" id="reasonwarning' + num + '"></div>' 
        + '<br>'
        + 'Long Reason: <br>'
        + '<textarea name="longreason' + num + '" rows="10" id="longreason' + num + '"></textarea> <br>';

}

function addReason() {
    /*"""
    .. function:: addReason()

      Creates a new reason division and fills it with the result from :js:func:`getDefaultReason`.
      It increments :js:data:`count`. Finally, the division is appended to the "reasons" division.
    */

    var liststring = '';
    for (reason in shortlist) {
        liststring = liststring 
            + '<option value="' + shortlist[reason] + '">'
            + shortlist[reason]
            + '</option>'
    }

    var newdiv = document.createElement('div');
    newdiv.id = 'reason' + count;
    newdiv.style.padding = "1em";
    newdiv.innerHTML = ''
        + '<button type="button" onClick="removeReason(\'' + newdiv.id + '\');">'
        + '&#10006;</button> <br>'
        + 'Select reason: '
        + '<select name= "selectedreason" id="select' + count + '" onchange="fillLongReason(' + count + ')">'
        + '<option  value="none">New Reason</option>'
        + liststring
        + '</select> <br>';
    newdiv.style.float = "left";

    var reasontext = document.createElement('div');
    reasontext.id = 'reasontext' + count;
    reasontext.innerHTML = getDefaultReason(count);

    newdiv.appendChild(reasontext);
    document.getElementById('reasons').appendChild(newdiv);
    count++;

}

function removeReason(childId) {
    /*"""
    .. function:: removeReason(childId)

      Removes a reason from the "reasons" division.

      :param str childId: is the full ID of the child to remove.
    */

    var parent = document.getElementById('reasons');
    var child = document.getElementById(childId);
    parent.removeChild(child);

}

function fillLongReason(number) {
    /*"""
    .. function:: fillLongReason(number)

      If a short reason is selected from the select field,
      this function displays the long reason.

      :param int number: is the ID number of the reason to fill.
    */

    var fillthis = document.getElementById('reasontext' + number);
    var shortreason = document.getElementById('select' + number).value;

    if (shortreason == 'none') {
        fillthis.innerHTML = getDefaultReason(number);
    } else {
        fillthis.style.maxWidth = '12em';
        fillthis.innerHTML = '<h4>' + shortreason + '</h4> <p>' 
            + fullreasons[shortreason] + '</p>';
    }

}

function checkReason(num) {
    /*"""
    .. function:: checkReason(num)

      Checks if a short reason entered by the user is already taken or not.
      If it is taken, the function gives a warning message and displays
      the corresponding long reason.
    */

    var value = document.getElementById('shortreason' + num).value;
    var theWarning = document.getElementById('reasonwarning' + num);
    var longReason = document.getElementById('longreason' + num);

    if ($.inArray(value, shortlist) > -1) {
        theWarning.innerHTML = '<p>That short reason is taken! </p> '
            + '<h4>' + value + '</h4> <p>'
            + fullreasons[value] + '</p>';
        theWarning.style.maxWidth = '12em';
        longReason.style.display = 'None';
    } else {
        theWarning.innerHTML = '';
        longReason.style.display = '';
    }

}
