/*"""
.. _checkuser-ref:

checkuser.js
++++++++++++

JavaScript functions that are used when registering
a new user or reseting a password.
The password check is not done by any other part of the system,
but all other checks are performed by the Python backend on
submission for security purposes.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/


function checkPassword () {
    /*"""
    .. function:: checkPassword()

      Checks input fields with the ids #firstword and #secondword.
      If they match, sets the innerHTML of the div #confirmresult
      with a green positive message.
      Otherwise the div is filled with a red warning message.
    */

    var firstpass = document.getElementById('firstword').value;
    var secondpass = document.getElementById('secondword').value;

    var adjustthis = document.getElementById('confirmresult');
    if (secondpass.length === 0) {
        adjustthis.innerHTML = '';
    } else if (firstpass === secondpass) {
        adjustthis.style.color = 'Green';
        adjustthis.innerHTML = 'The passwords match!';
    } else {
        adjustthis.style.color = 'Red';
        adjustthis.innerHTML = 'The passwords don\'t match!';
    }
}

function validateForm () {
    /*"""
    .. function:: validateForm()

      Checks the form for registering a new user.
      The requirements for the form values are given
      in :ref:`new-user-ref`.
    */

    var form = document.forms['infoform'];
    var errorDir = document.getElementById('error');
    errorDir.innerHTML = '';
    errorDir.style.color = '#ff0000';

    var email = form['email'].value;
    var username = form['username'].value;
    var password = form['firstword'].value;
    var checkword = form['secondword'].value;

    var validDomain = false;

    for (iEmail in validEmails) {
        if (email.endsWith(validEmails[iEmail])) {
            validDomain = true;
        }
    }

    if (!validDomain) {
        errorDir.innerHTML += 'Email does not end in valid domain. <br>';
    }

    if (username.length === 0) {
        errorDir.innerHTML += 'Cannot have a blank username. <br>';
    }

    if (password.length === 0) {
        errorDir.innerHTML += 'Cannot have a blank password. <br>';
    }

    if (password != checkword) {
        errorDir.innerHTML += 'Passwords must match. <br>';
    }

    if (errorDir.innerHTML.length != 0) {
        return false;
    } else {
        return true;
    }
}
