
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
            var aref = line.appendChild(document.createElement("a"));
            aref.href = '/seeworkflow/?workflow=' + wkflow.workflow;
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
            var report = rowObj.appendChild(document.createElement("td"));
            workflows.forEach(function (wkfl) {
                var dot = report.appendChild(document.createElement("span"));
                dot.className = "dot";
                dot.style.backgroundColor = status_colors[wkfl.status];
            });
            rowObj.onclick = listWorkflows(workflows);
        }
    });
}

function fillPrepIDs() {
    // Create the table of PrepIDs
    var table = document.getElementById("errortable");

    $.ajax({
        url: "/getprepids",
        success: function (prepids) {
            prepids.forEach(function (prepid) {
                var rowObj = table.insertRow();
                rowObj.id = prepid;
                rowObj.appendChild(document.createElement("td")).
                    innerHTML = prepid;
                fillWorkflows(rowObj);
            });
            document.getElementById("loading").remove();
        }
    });

}
