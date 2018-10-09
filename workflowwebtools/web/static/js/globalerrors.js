
function fillWorkflows(prepID) {

}

function fillPrepIDs() {
    // Create the table of PrepIDs
    var table = document.getElementById("errortable");

    $.ajax({
        url: '/prepids',
        success: function (prepids) {
            prepids.forEach(function (prepid) {
                var rowObj = table.insertRow();
                rowObj.id = prepid;
                rowObj.appendChild(document.createElement('td')).
                    innerHTML = prepid;
            })
        }
    });

}
