/*"""
.. describe:: addreason.js

This file contains the functions used to add reasons to the :ref:`workflow-view-ref`
as well as adding parameters to the page when different actions are selected.
The fields added by this script are handled by the :py:mod:`WorkflowWebTools.reasonsmanip`
and :py:mod:`WorkflowWebTools.manageactions` modules.

.. todo::

  This is some of the messiest code in the package.
  Need to impliment some JSLint check.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/

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

function addReason() {

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

    var parent = document.getElementById('reasons');
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

function makeTable(entries, header) {

    header.unshift('Parameter');
    var paramTable = document.createElement('TABLE');
    var headerRow = paramTable.insertRow(0);
        
    for (var iData = 0; iData < header.length; iData++) {
        var cell = headerRow.insertCell(iData);
        cell.innerHTML = '<b>' + header[iData] + '</b>';
    }
        
    for (var iParam = 0; iParam < entries.length; iParam++) {
        var row = paramTable.insertRow(iParam + 1);
        var cell = row.insertCell(0);
        cell.innerHTML = entries[iParam];
        for (var iOpt = 1; iOpt < header.length; iOpt++) {
            cell = row.insertCell(iOpt);
            if (header[iOpt] == 'Same' || header[iOpt] == 'False')
                cell.innerHTML = '<input type="radio" name="param_'+entries[iParam]+'" value="'+header[iOpt]+'" checked="checked">';
            else
                cell.innerHTML = '<input type="radio" name="param_'+entries[iParam]+'" value="'+header[iOpt]+'">';
        }
    }

    return paramTable
}

function makeParamTable(action) {

    var paramDiv = document.getElementById('actionparams');
    paramDiv.innerHTML = '';
    paramDiv.style.padding = "10px";

    var params = [];
    var bools = [];
    var texts = [];
    var opts = {};

    if ( action.value == 'clone' ) {
        params = [
                  'splitting',
                  'memory',
                  'timeout',
                  ];
        bools = [
                 'invalidate',
                 ];
        texts = [
                 'group',
                 'max_memory',
                 ];
    } else if (action.value == 'recover') {
        params = [
                  'memory',
                  'timeouts',
                  ];
        bools = [
                 'replica',
                 'trustsite'
                 ];
        texts = [
                 'LFN',
                 'ERA',
                 'procstring',
                 'procversion',
                 ];
        opts = {
            Activity: [
                     'reprocessing',
                     'production',
                     'test',
                     ]
                };
    } else if (action.value == 'investigate') {
        texts = [
                 'other',
                 ]
    }

    if (params.length != 0) {
        paramDiv.appendChild(makeTable(params, ['Decrease', 'Same', 'Increase']));
    }

    if (bools.length != 0) {
        paramDiv.appendChild(makeTable(bools, ['True', 'False']));
    }

    for (key in opts) {
        var optionDiv = document.createElement("DIV");
        var keytext = document.createElement("b");
        keytext.innerHTML = key + ': <br>';
        optionDiv.appendChild(keytext);
        for (opt in opts[key]) {

            var opttext = document.createTextNode('    ' + opts[key][opt] + '  ');
            optionDiv.appendChild(opttext);
            var option = document.createElement("INPUT");
            option.setAttribute("type", "radio");
            option.setAttribute("name", "param_" + key);
            option.setAttribute("value", opts[key][opt]);
            optionDiv.appendChild(option);

        }
        paramDiv.appendChild(optionDiv);
    }

    for (itext in texts) {
        var inpDiv = document.createElement("DIV");
        inpDiv.style.padding = '0.5em';
        var text = document.createTextNode(texts[itext] + '  ');
        var inp = document.createElement("INPUT");
        inp.setAttribute("type", "text");
        inp.setAttribute("name", "param_" + texts[itext]);
        inpDiv.appendChild(text)
        inpDiv.appendChild(inp)
        paramDiv.appendChild(inpDiv)
    }

    if (params.length != 0) {

        var checkDiv = document.createElement('DIV');
        checkDiv.id = 'siteslistcheck';
        checkDiv.innerHTML = '<h4> Site List: </h4>';

        for (var iSite = 0; iSite < sitelist.length; iSite++) {
            var paramdiv = document.createElement('DIV');
            paramdiv.className = 'sitecheck'
            paramdiv.innerHTML = '<input type="checkbox" name="param_sites" value="'+sitelist[iSite]+'">'+sitelist[iSite]+'</input>';
            checkDiv.appendChild(paramdiv);
        }

        checkDiv.innerHTML += '<br style="clear:both;">'

        var checkShow = document.createElement('BUTTON');
        checkShow.type = 'button';
        checkShow.innerHTML = 'Hide/Show Sites';
        checkShow.onclick = function() {
            $('#siteslistcheck').toggle();
        };

        paramDiv.appendChild(checkShow);
        paramDiv.appendChild(checkDiv);

    }
}
