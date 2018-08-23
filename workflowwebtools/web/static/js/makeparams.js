/*"""
.. _makeparams-ref:

makeparams.js
+++++++++++++

This file contains the functions used to add parameters to the page when different actions are selected.
The fields added by this script are handled by the :py:mod:`WorkflowWebTools.manageactions` module.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/

function taskTable(opts, texts, taskNumber) {
    /*"""
    .. function:: taskTable(opts, texts, taskNumber)

    Creates a "table" for parameters to be filled in and returns the <div> these are contained in.

    :param dict opts: Each key is the name of the parameter.
                      Each value is the list of possible values for this parameter.
    :param list texts: A list of parameters that should be set by a text field.
    :param int taskNumber: Separates the different parameters for each task in ACDC.
    :returns: The <div> element that contains the table
    */
    var paramDiv = document.createElement('DIV');
    paramDiv.innerHTML = '';
    paramDiv.style.padding = '10px';

    for (key in opts) {
        var optionDiv = document.createElement('DIV');
        var keytext = document.createElement('b');
        keytext.innerHTML = key + ':';
        optionDiv.appendChild(keytext);

        for (opt in opts[key]) {

            var opttext = document.createTextNode('    ' + opts[key][opt] + '  ');
            optionDiv.appendChild(opttext);
            var option = document.createElement('INPUT');
            option.setAttribute('type', 'radio');
            option.setAttribute('name', 'param_' + taskNumber + '_' + key);
            option.setAttribute('value', opts[key][opt]);
            option.ondblclick = function() {
                this.checked = false;
            }
            optionDiv.appendChild(option);

        }

        paramDiv.appendChild(optionDiv);

    }

    for (itext in texts) {

        var inpDiv = document.createElement('DIV');
        var text = document.createElement('b');
        text.innerHTML = texts[itext] + ':  ';
        var inp = document.createElement('INPUT');
        inp.setAttribute('type', 'text');
        inp.setAttribute('name', 'param_' + taskNumber + '_' + texts[itext]);
        
        if (texts[itext] in param_defaults) {
            inp.setAttribute('value', param_defaults[texts[itext]]);
        }

        inpDiv.appendChild(text);
        inpDiv.appendChild(inp);
        paramDiv.appendChild(inpDiv);

    }

    return paramDiv;

}

function printSiteList(method, task, siteTableDiv) {
    var site_list_message = document.createElement('DIV');
    site_list_message.style.fontWeight='900';
    site_list_message.innerHTML = '<span style="color:red">Red sites</span> are sites in drain or disabled.';
    siteTableDiv.appendChild(site_list_message);

    for (site in sitelist) {
        var sitelistdiv = document.createElement('DIV');
        sitelistdiv.className = 'sitecheck';

        var isChecked = '';
        if (drain_statuses[sitelist[site]] == 'drain' ||
            drain_statuses[sitelist[site]] == 'disabled') {
            if (method.value == 'Ban')
                isChecked = ' checked';
            sitelistdiv.style.color = 'red';
        }

        if (method.value == 'Manual') {
            if (sites_for_task[task_list[task]].indexOf(sitelist[site]) >= 0) {
                isChecked = ' checked';
                sitelistdiv.style.fontWeight = 'bold';
            }
        }

        sitelistdiv.innerHTML = '<input type="checkbox" name="param_' + task + '_sites" value="' + 
            sitelist[site] + '"' + isChecked + '>' + sitelist[site] + '</input>';
        siteTableDiv.appendChild(sitelistdiv);
    }
    var clearBreak = document.createElement('BR');
    clearBreak.className = 'clear';
    siteTableDiv.appendChild(clearBreak);
}

function printSiteLists(method) {
    /*"""
    .. function:: printSiteLists(method)

      Sets the contents of the site tables under the "acdc" action
      based on the method of site selection subsequently selected.
    */

    // Purposefully go one past the task_list itself to pick up the All Steps' div for banning
    for (task = 0; task <= task_list.length; task++) {
        var siteTableDiv = document.getElementById('site_table_' + task);
        siteTableDiv.innerHTML = '';

        if ((method.value == 'Manual' && task != task_list.length) ||
            (method.value == 'Ban' && task == task_list.length))
            printSiteList(method, task, siteTableDiv);
    }
}

function makeParamTable(action) {
    /*"""
    .. function:: makeParamTable(action)

      Offers the various options that are available for a given action.
    */

    var paramDiv = document.getElementById('actionparams');
    paramDiv.innerHTML = '';
    paramDiv.style.padding = '10px';

    var texts = [];
    var opts = {};

    var split_list = ['2x', '3x', '10x', '20x', '50x', '100x', '200x', 'max'];

    if (action.value == 'clone') {
        texts = [
                 'memory',
                 'cores'
                 ];
        opts = {
            'splitting': split_list
        };
    } else if (action.value == 'acdc') {
        texts = [
                 'memory',
                 'cores'
                 ];
        opts = {
            'xrootd': ['enabled', 'disabled'],
            'secondary': ['enabled', 'disabled'],
            'splitting': split_list
        };
    } else if (action.value == 'recovery') {
        texts = [
                 'memory',
                 'group',
                 'cores'
                 ];
        opts = {
            'xrootd': ['enabled', 'disabled'],
            'secondary': ['enabled', 'disabled'],
            'splitting': split_list
        };
    } else if (action.value == 'special') {
        opts = {
            'action': ['by-pass', 'force-complete', 'on-hold']
        };
        texts = [
                 'other',
                 ];
    }

    if (['acdc', 'recovery'].indexOf(action.value) >= 0) {
        // ACDC is the most complex action, and needs parameters for each task and sites.
        var methods = [
                       'Auto',
                       'Manual',
                       'Ban'
                       ];
        var methodsDiv = document.createElement('DIV');
        methodsDiv.innerHTML = '<h4>Site Selection Method:</h4>';
        methodsDiv.innerHTML += '<p>To see which sites are selected for this workflow under Auto, '
            + 'check what is automatically checked under Manual. '
            + 'Ban defaults to sites in drain. Same ban list applies to all tasks, '
            + 'which otherwise pick sites from Auto.</p>'
        for (method in methods) {
            var checked = (method == 0) ? ' checked' : '';
            methodsDiv.innerHTML += '<input type="radio" name="method" onclick="printSiteLists(this);" value="' 
                + methods[method] + '"' + checked + '>' + methods[method] + ' ';
        }
        paramDiv.appendChild(methodsDiv);

        var all_title = document.createElement('h3');
        all_title.innerHTML = 'All Steps (use this or fill all others)';
        paramDiv.appendChild(all_title);
        paramDiv.appendChild(taskTable(opts, texts, task_list.length));
        var siteTable = document.createElement('DIV');
        siteTable.id = 'site_table_' + task_list.length;
        paramDiv.appendChild(siteTable);

        for (task in task_list) {
            var taskName = task_list[task].split('/').slice(2).join('/');

            var taskHeader = document.createElement('DIV');

            var title = document.createElement('h3');
            title.innerHTML = '<a href="#' + task_list[task] + '">'
                + taskName + '</a>';

            var checkThis = document.createElement('SPAN');
            checkThis.innerHTML = 'Only do this task.';

            var checkBox = document.createElement('INPUT');
            checkBox.type = 'checkbox';
            checkBox.name = 'dotasks';
            checkBox.value = taskName;

            taskHeader.appendChild(title);
            taskHeader.appendChild(checkBox);
            taskHeader.appendChild(checkThis);

            paramDiv.appendChild(taskHeader);
            paramDiv.appendChild(taskTable(opts, texts, task));

            // This DIV is where the lists of sites will be printed, depending on the method selected
            var siteTable = document.createElement('DIV');
            siteTable.id = 'site_table_' + task;
            paramDiv.appendChild(siteTable);
        }
    } else {
        paramDiv.appendChild(taskTable(opts, texts, 0));
    }

}
