var count = 0;

function getDefaultReason(num) {

    return ''
        + 'Short Reason: <br>'
        + '<input type="text" name="shortreason' + num + '" id="shortreason' + num + '" '
        + 'onkeyup="checkReason(' + num + ')"></input> '
        + '<div style="color:#ff0000; width=12em;" id="reasonwarning' + num + '"></div>' 
        + '<br>'
        + 'Long Reason: <br>'
        + '<textarea name="longreason' + num + '" rows="10" id="longreason' + num + '"></textarea> <br>';

}

function addReason(divName) {

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
        + '<button type="button" onClick="removeReason(\'' + divName + '\',\'' + newdiv.id + '\');">'
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
    document.getElementById(divName).appendChild(newdiv);
    count++;

}

function removeReason(parentId,childId) {

    var parent = document.getElementById(parentId);
    var child = document.getElementById(childId);
    parent.removeChild(child);

}

function fillLongReason(number) {

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

function makeParamTable(action) {

    var paramDiv = document.getElementById('actionparams');
    paramDiv.innerHTML = '';
    paramDiv.style.padding = "10px";

    var paramTable = document.createElement('TABLE');
    var header = ['Parameter', 'Decrease', 'Same', 'Increase'];
    var params = [];

    if ( action.value == 'clone' ) {
        params = [
                  'splitting',
                  'memory',
                  'timeout',
                  ]
    } else if (action.value == 'recover') {
        params = [
                  'memory',
                  'timeouts',
                  ]
    }

    var headerRow = paramTable.insertRow(0);

    for (var iData = 0; iData < header.length; iData++) {
        var cell = headerRow.insertCell(iData);
        cell.innerHTML = header[iData];
    }

    for (var iParam = 0; iParam < params.length; iParam++) {
        var row = paramTable.insertRow(iParam + 1);
        var cell = row.insertCell(0);
        cell.innerHTML = params[iParam];
        for (var iOpt = 1; iOpt < header.length; iOpt++) {
            cell = row.insertCell(iOpt);
            if (header[iOpt] == 'Same')
                cell.innerHTML = '<input type="radio" name="param_'+params[iParam]+'" value="'+header[iOpt]+'" checked="checked">';
            else
                cell.innerHTML = '<input type="radio" name="param_'+params[iParam]+'" value="'+header[iOpt]+'">';
        }
    }

    if (params.length != 0) {

        paramDiv.appendChild(paramTable);

        var checklist = '<h4> Site List: </h4>';
        for (var iSite = 0; iSite < sitelist.length; iSite++)
            checklist += '<input type="checkbox" name="param_sites" value="'+sitelist[iSite]+'">'+sitelist[iSite]+'</input> <br>';

        var checkDiv = document.createElement('DIV');
        checkDiv.id = 'siteslistcheck';
        checkDiv.style.display = 'None';
        checkDiv.innerHTML = checklist;

        var checkShow = document.createElement('BUTTON');
        checkShow.type = 'button';
        checkShow.innerHTML = 'Show/Hide Sites';
        checkShow.onclick = function() {
            $('#siteslistcheck').toggle();
        };

        paramDiv.appendChild(checkShow);
        paramDiv.appendChild(checkDiv);

    }
}
