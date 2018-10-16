
// This is the number of workflows that get automatically loaded for the global error page
var eachLoad = 40;

// Colors dictionary
var status_colors = {
    "none": "red",
    "acted": "green",
    "pending": "blue"
}

function listWorkflows (workflows) {
    // Returns a function to do on a click
    return function () {
        var span = document.getElementById("workflows");
        span.innerHTML = "Workflows:"
        var list = span.appendChild(document.createElement("ul"));

        workflows.forEach(function (wkflow) {
            var line = list.appendChild(document.createElement("li"));
            var dot = line.appendChild(document.createElement("span"));
            dot.className = "dot";
            dot.style.backgroundColor = status_colors[wkflow.status];
            line.appendChild(document.createTextNode(" " + wkflow.errors + " "));
            var aref = line.appendChild(document.createElement("a"));
            aref.href = '/seeworkflow2/?workflow=' + wkflow.workflow;
            aref.innerHTML = wkflow.workflow;
            aref.leftMargin = '10px';
        });
    }
}

function fillWorkflows(rowObj) {
    $.ajax({
        url: "/getworkflows",
        data: {"prepid": rowObj.id},
        success: function (workflows) {

            // Sum the errors and throw them into the row
            rowObj.appendChild(document.createElement("td")).appendChild(
                document.createTextNode(workflows.reduce(function (a, b) {
                    return {errors: a.errors + b.errors};
                }).errors || 0));

            var report = rowObj.appendChild(document.createElement("td"));
            var drawn = 0;

            workflows.forEach(function (wkfl) {
                if (drawn && !(drawn % 10))
                    report.appendChild(document.createElement("br"));

                var dot = report.appendChild(document.createElement("span"));
                dot.className = "dot";
                dot.style.backgroundColor = status_colors[wkfl.status];
                drawn += 1;
            });
            rowObj.onclick = listWorkflows(workflows);
        }
    });
}

function fillSomePrepIDs(prepids, start, howmany) {
    var table = document.getElementById("errortable");

    var iPrep = start;
    var last = howmany ? Math.min(prepids.length, start + howmany) : prepids.length;


    while (iPrep < last) {
        var prepid = prepids[iPrep];
        var rowObj = table.insertRow();
        rowObj.id = prepid;

        var remover = rowObj.appendChild(document.createElement("td"));
        remover.innerHTML = "&#x2716";
        remover.className = "remover";
        remover.onclick = function (event) {
            var myRow = event.target.parentNode
            table.deleteRow(myRow.rowIndex);
            $.ajax({
                url: '/markreset',
                data: {'prepid': myRow.id}
            });
            event.stopPropagation();
        };

        rowObj.appendChild(document.createElement("td")).
            innerHTML = prepid;
        fillWorkflows(rowObj);
        iPrep += 1;
    }

    // We can still load more
    if (iPrep < prepids.length) {
        $("#loadmore").html("Load " + eachLoad + " More").off("click").click(function () {
                fillSomePrepIDs(prepids, iPrep, eachLoad);
            });
        $("#loadall").off("click").click(function () {
                fillSomePrepIDs(prepids, iPrep, 0);
            });
    }
    // Otherwise, remove our buttons
    else {
        document.getElementById("loadmore").remove();
        document.getElementById("loadall").remove();
    }
}

function fillPrepIDs() {
    // Create the table of PrepIDs
    $.ajax({
        url: "/getprepids",
        success: function (prepids) {
            fillSomePrepIDs(prepids, 0, eachLoad);
            document.getElementById("loading").remove();

            $(document.getElementById("top").appendChild(document.createElement("button"))).
                click(function () {
                    $("#errortable tr").remove();
                    var search = new RegExp($("#searchbar").val());
                    fillSomePrepIDs(
                        prepids.filter(function (element) {
                            return search.test(element);
                        }),
                        0, eachLoad);
                }).html("Submit");
        }
    });

}
