function checkPassword () {
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
    var form = document.forms['actionform'];
    var errorDir = document.getElementById('error');
    errorDir.innerHTML = '';

    var email = form['email'].value;
    var username = form['username'].value;
    var password = form['firstword'].value;
    var checkword = form['secondword'].value;

    if (!(email.endsWith('@cern.ch') || email.endsWith('@fnal.gov'))) {
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
    }
}
