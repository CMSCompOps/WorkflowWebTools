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

function drawPieCharts() {
    /*"""
    .. function:: drawPieCharts()

      This function finds multiple canvases and draws pie charts onto them.
      The number of errors for each canvas are given as separate arguments.
      The piecharts are split with the largest contributer always having the same color.
      The radius of the piechart is a fraction of the canvas size,
      determined by the following equation:

      .. math::

        \frac{r}{r_{canvas}} = \frac{n_{errors}}{n_{errors} + 10}
    */
    var iChart;
    var canvases = document.getElementsByClassName("piechart");
    var ncanvases = Math.min(canvases.length, arguments.length);
    for (iChart = 0; iChart < ncanvases; iChart++) {
        var data = arguments[iChart];
        // data.sort(function(a, b){return b-a});
        var total = 0;
        for (var point in data)
            total += data[point];

        var canvas = canvases[iChart];
        var context = canvas.getContext("2d");
        var centerX = canvas.width/2;
        var centerY = canvas.height/2;
        var radius = Math.min(centerX, centerY) * total/(10 + total);
        var currangle = 0;

        var ndivisions = Math.min(colors.length, data.length);
        var iDivision;
        for (iDivision = 0; iDivision < ndivisions; iDivision++) {
            var nextangle = currangle + 2 * Math.PI * data[iDivision]/total;
            context.beginPath();
            context.arc(centerX, centerY, radius, currangle, nextangle);
            context.lineTo(centerX, centerY);
            context.fillStyle = colors[iDivision];
            context.fill();
            currangle = nextangle;
        }
    }
}


function drawPies () {
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
    head.appendChild(document.createElement('th'));

    uniq_cols.forEach(function(col) {
            var collabel = head.appendChild(document.createElement('th'));
            collabel.className = 'rotate';
            if (ready[col])
                collabel.className += ' ' + ready[col];
            var innerspan = collabel.appendChild(document.createElement('div')).appendChild(document.createElement('span'));
            innerspan.innerHTML = col;
        });

    for (var i_row in table.children) {
        var row = table.children[i_row];
        if (row.id) {
            var row_obj = JSON.parse(row.lastElementChild.lastElementChild.innerHTML);
            uniq_cols.forEach(function(col) {
                    var anchor = document.createElement('a');
                    // var canvas = document.createElement('canvas')
                    // canvas.width = '20';
                    // canvas.height = '20';

                    anchor.innerHTML = function (obj) {
                        output = 0;
                        for (var pie in obj)
                            output += obj[pie];
                        return output;
                    } (row_obj.errors[col]);

                    if (anchor.innerHTML != 0) {
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
                        anchor.target = 'blank';
                    }
                    else
                        anchor.innerHTML = '';

                    var td = row.appendChild(document.createElement('td'));
                    td.align = 'center';
                    td.appendChild(anchor); //.appendChild(canvas);

                });
        }
    }
}
