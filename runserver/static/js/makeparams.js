/*"""
.. _makeparams-ref:

makeparams.js
+++++++++++++

This file contains the functions used to add parameters to the page when different actions are selected.
The fields added by this script are handled by the :py:mod:`WorkflowWebTools.manageactions` module.

.. todo::

  This is some of the messiest code in the package.
  Need to impliment some JSLint check.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/

function taskTable(opts, texts, taskNumber) {

    var paramDiv = document.createElement("DIV");
    paramDiv.innerHTML = '';
    paramDiv.style.padding = "10px";

    for (key in opts) {
        var optionDiv = document.createElement("DIV");
        var keytext = document.createElement("b");
        keytext.innerHTML = key + ':';
        optionDiv.appendChild(keytext);

        for (opt in opts[key]) {

            var opttext = document.createTextNode('    ' + opts[key][opt] + '  ');
            optionDiv.appendChild(opttext);
            var option = document.createElement("INPUT");
            option.setAttribute("type", "radio");
            option.setAttribute("name", "param_" + taskNumber + "_" + key);
            option.setAttribute("value", opts[key][opt]);
            optionDiv.appendChild(option);

        }

        paramDiv.appendChild(optionDiv);

    }

    for (itext in texts) {

        var inpDiv = document.createElement("DIV");
        var text = document.createElement("b");
        text.innerHTML = texts[itext] + ':  ';
        var inp = document.createElement("INPUT");
        inp.setAttribute("type", "text");
        inp.setAttribute("name", "param_" + taskNumber + "_" + texts[itext]);
        
        if (texts[itext] in param_defaults) {
            inp.setAttribute("value", param_defaults[texts[itext]]);
        }

        inpDiv.appendChild(text);
        inpDiv.appendChild(inp);
        paramDiv.appendChild(inpDiv);

    }

    return paramDiv;

}

function makeParamTable(action) {
    /*"""
    .. function:: makeParamTable(action)

      Offers the various options that are available for a given action.

      :param str action: is the action which is currently selected
                         on the :ref:`workflow-view-ref`.
    */

    var paramDiv = document.getElementById('actionparams');
    paramDiv.innerHTML = '';
    paramDiv.style.padding = "10px";

    var texts = [];
    var opts = {};

    var print_site_list = false;

    if (action.value == 'clone') {
        texts = [
                 'memory',
                 ];
        opts = {
            'splitting': ['2x', '3x', 'max']
        };
    } else if (action.value == 'recover') {
        texts = [
                 'memory',
                 ];
        opts = {
            'xrootd': ['enabled', 'disabled'],
            'splitting': ['2x', '3x', 'max'],
        };
        print_site_list = true;
    } else if (action.value == 'investigate') {
        texts = [
                 'other',
                 ];
    }

    if (action.value == 'recover') {
        var all_title = document.createElement("h3");
        all_title.innerHTML = 'All Steps (use this or fill all others)'
        paramDiv.appendChild(all_title);
        paramDiv.appendChild(taskTable(opts, texts, task_list.length));

        for (task in task_list) {
            var title = document.createElement("h3");
            title.innerHTML = '<a href="#' + task_list[task] + '">'
                + task_list[task].split('/').slice(2).join('/')
                + '</a>';
            paramDiv.appendChild(title);
            paramDiv.appendChild(taskTable(opts, texts, task));

            if (print_site_list) {
                for (site in sitelist) {
                    var sitelistdiv = document.createElement('DIV');
                    sitelistdiv.className = 'sitecheck';

                    var isChecked = '';
                    if (sites_for_task[task_list[task]].indexOf(sitelist[site]) >= 0)
                        isChecked = ' checked';

                    sitelistdiv.innerHTML = '<input type="checkbox" name="param_' + task + '_sites" value="' + 
                        sitelist[site] + '"' + isChecked + '>' + sitelist[site] + '</input>';
                    paramDiv.appendChild(sitelistdiv);
                }
                var clearBreak = document.createElement('BR');
                clearBreak.className = 'clear';
                paramDiv.appendChild(clearBreak);
            }
        }
    } else {
        paramDiv.appendChild(taskTable(opts, texts, 0));
    }

}
