/*"""
.. _piechart-ref:

piechart.js
+++++++++++

Contains the drawPieCharts function for the global errors page.

:author: Daniel Abercrombie <dabercro@mit.edu>
*/

var colors = ["#ff0000", "#00ff00", "#0000ff", "#00ffff", "#ff00ff", "#ffff00",
              "#808080", "#808000", "#800080", "#008080", "#000000",
              "#ff8000", "#ff0080", "#80ff00", "#00ff80", "#8000ff", "#0080ff",
              "#ff8080", "#80ff80", "#8080ff", "#ffff80", "#ff80ff", "#80ffff"];

function prepareRows() {

    // Send JSON information compressed, and uncompress it here!

    // https://stackoverflow.com/a/22675078/5941270
    // Decode base64 (convert ascii to binary)
    var strData     = atob(document.getElementById('table-data').innerHTML);
    // Convert binary string to character-number array
    var charData    = strData.split('').map(function(x){return x.charCodeAt(0);});
    // Turn number array into byte-array
    var binData     = new Uint8Array(charData);

    var data = JSON.parse(pako.inflate(binData, {to: 'string'}));

    var table = document.getElementById("errortable");

    data.forEach(function (obj) {
            var row_name = obj.name;
            var hiddenstuff = obj.hid;

            var row_obj = table.insertRow();

            var sub_rows = false;
            if (pievar != 'stepname')
                sub_rows = true;

            if (hiddenstuff) {
		if (!obj.is_wf)
		    sub_rows = false;

                var this_row_level = hiddenstuff[0] + 1;
                row_obj.className = 'child_of_' + hiddenstuff[0] + '_' + hiddenstuff[1];
            } else {
                this_row_level = 0;
                row_class = '';
            }

            if (row_name)
                row_obj.id = row_name;

            if (!row_name || row_obj.classList.length)
                row_obj.style = 'display: none;';

            var header = row_obj.appendChild(document.createElement('th'));
            header.className = obj.bg;

            if (sub_rows) {
                header.onclick = function () {
                    expand_children(this_row_level, row_name, false);
                };

                var tab_row = header.
                    appendChild(document.createElement('table')).
                    appendChild(document.createElement('tr'));

                var info_type = this_row_level ? 'workflow' : 'prepid';

                var reset_button = tab_row.
                    appendChild(document.createElement('td')).
                    appendChild(document.createElement('a'));

                reset_button.href = '/resetcache?' + info_type + '=' + row_name;
                reset_button.innerHTML = 'Reset';
                reset_button.onclick = function (event) {
                    event.stopPropagation();
                };

                tab_row.appendChild(document.createElement('th')).innerHTML =
                    '<span id="' + row_name + '_span">&#x25B6;</span>';
                header = tab_row.appendChild(document.createElement('th'));
            }

            if (obj.is_wf) {
                var ahref = header.appendChild(document.createElement('a'));
                ahref.href = '/seeworkflow/?workflow=' + row_name;
                ahref.innerHTML = row_name;
                ahref.onclick = function (event) {
                    event.stopPropagation();
                };
            } else
                header.innerHTML = row_name;

            var data = row_obj.appendChild(document.createElement('td'));
            var row = obj.row;
            data.align = 'center';
            data.innerHTML = row['total'] +
                '<span style="display: none;">' + JSON.stringify(row) + '</span>';
        });

}


function drawPies () {
    /*"""
    .. function:: drawPies()

      This function finds multiple canvases and draws pie charts onto them.
      The number of errors for each canvas are by a JSON string hidden
      in the table with id 'errortable'.
      The piecharts are split with the largest contributer always having the same color.
      The radius of the piechart is a fraction of the canvas size,
      determined by the following equation:

      .. math::

        \frac{r}{r_{canvas}} = \frac{n_{errors}}{n_{errors} + 10}
    */

    // Not really a set, but we'll sort it at the end to get unique values
    var columns = new Array();
    var pies = new Array();
    // Get the tbody element inside of the <table> tags
    var table = document.getElementById("errortable").firstElementChild;
    for (var row in table.children) {
        // Only child elements
        if (table.children[row].lastElementChild) {
            // Get the span at the end of the row, and load the JSON object
            var row_obj = JSON.parse(table.children[row].lastElementChild.lastElementChild.innerHTML);
            for (var col in row_obj.errors) {
                columns.push(col);
                for (var pie in row_obj.errors[col])
                    pies.push(pie);
            }
            continue;
        }
    }

    var uniq = function (full) {
        var output = new Array();
        full.sort().forEach(function(val) {
                if (val != output[output.length - 1])
                    output.push(val);
            });
        return output;
    }

    var uniq_cols = uniq(columns);
    var uniq_pies = uniq(pies);

    // Insert a header for the table
    var head = table.insertBefore(document.createElement('tr'), table.firstElementChild);
    head.appendChild(document.createElement('td')).innerHTML = '' +
        '<span style="color:#0000ff;">Select orientation:</span>' +
        '<form>' +
        '<table style="border-collapse: separate; border-spacing: 0.5em;">' +
        '<tr>' +
        '<td></td><th>Row</th><th>Group By</th>' +
        '</tr>' +
        '<tr>' +
        '<td><input type="radio" name="pievar" value="stepname"></td><td>errorcode</td><td>site name</td>' +
        '</tr>' +
        '<tr>' +
        '<td><input type="radio" name="pievar" value="sitename"></td><td>workflow</td><td>error code</td>' +
        '</tr>' +
        '<tr>' +
        '<td><input type="radio" name="pievar" value="errorcode"></td><td>workflow</td><td>site name</td>' +
        '</tr>' +
        '</table>' +
        '<input type="submit" value="Submit">' +
        '</form>';

    var toth = head.appendChild(document.createElement('th'));
    toth.className = 'rotate';
    toth.innerHTML = 'Total';

    uniq_cols.forEach(function(col) {
            var collabel = head.appendChild(document.createElement('th'));
            collabel.className = 'rotate';
            if (ready[col])
                collabel.className += ' ' + ready[col];
            var innerspan = collabel.appendChild(document.createElement('div')).appendChild(document.createElement('span'));
            innerspan.innerHTML = col;
        });

    var canvases = []; // An array that we will fill with canvases to draw on
    var pies = {};     // An object that we will use to sort the pie variables

    for (var i_row in table.children) {
        var row = table.children[i_row];
        if (row.id) {
            var row_obj = JSON.parse(row.lastElementChild.lastElementChild.innerHTML);
            uniq_cols.forEach(function(col) {
                    var anchor = document.createElement('a');
                    var canvas = document.createElement('canvas')
                    canvas.width = '20';
                    canvas.height = '20';

                    anchor.appendChild(canvas);

                    // Count the size of the pie here and create canvas and sorting objects
                    var count = function (obj) {
                        output = 0;
                        for (var pie in obj) {
                            var num = obj[pie];
                            if (pie in pies)
                                pies[pie] += num;
                            else  // Otherwise, create entry
                                pies[pie] = num;

                            output += num;
                        }

                        if (output)
                            canvases.push({obj: obj, canvas: canvas, total: output})

                        return output;
                    } (row_obj.errors[col]);

                    if (count != 0) {
                        switch(pievar) {
                        case 'stepname':
                            anchor.href = 'listpage?errorcode=' + row.id + '&sitename=' + col;
                            break;
                        case 'errorcode':
                            anchor.href = 'listpage?workflow=' + row.id + '&sitename=' + col;
                            break;
                        default:
                            anchor.href = 'listpage?workflow=' + row.id + '&errorcode=' + col;
                        }
                        anchor.target = '_blank';
                    }
                    else
                        anchor.innerHTML = '';

                    var td = row.appendChild(document.createElement('td'));
                    td.align = 'center';
                    td.appendChild(anchor); //.appendChild(canvas);

                });
        }
    }

    // Sort the colors
    var pies_list = [];
    for (var pie in pies)
        pies_list.push({pie: pie, num: pies[pie]});

    // Sort with the largest numbers first
    pies_list.sort(function(a, b) {return b.num - a.num});
    // Map pie chart values to colors
    var color_map = {};
    var n_colors = Math.min(colors.length, pies_list.length)
    for (var index = 0; index < n_colors; index++)
        color_map[pies_list[index].pie] = colors[index];

    // Draw all of our pie charts
    canvases.forEach(function (canv) {
            var total = canv.total;
            var canvas = canv.canvas;
            canvas.title = 'Total: ' + total;
            var context = canvas.getContext("2d");
            var centerX = canvas.width/2;
            var centerY = canvas.height/2;
            var radius = Math.min(centerX, centerY) * total/(10 + total);

            var currangle = 0;

            for (var key in color_map) {
                if (canv.obj.hasOwnProperty(key)) {
                    var nextangle = currangle + 2 * Math.PI * canv.obj[key]/total;
                    context.beginPath();
                    context.arc(centerX, centerY, radius, currangle, nextangle);
                    context.lineTo(centerX, centerY);
                    context.fillStyle = color_map[key];
                    context.fill();
                    currangle = nextangle;
                }
            }
        });

}

function pieProduction () {
    prepareRows();
    drawPies();
    document.getElementById('wait-message').style.display = 'none';
}
