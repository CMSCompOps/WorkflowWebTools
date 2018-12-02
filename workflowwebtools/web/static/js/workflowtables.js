
function setSiteStatuses () {
    $.ajax({
        url: '/sitestatuses',
        success: function(statuses) {
            statuses.forEach(function (site) {
                $("." + site.site).addClass(site.status);
            });
        }
    });
}

function drawTable(step, table) {
    table.border = "3";
    table.style.borderCollapse = "collapse";
    var headRow = table.insertRow();
    headRow.appendChild(document.createElement("td"));
    step.allsites.forEach(function (site) {
        var siteHead = headRow.appendChild(document.createElement("th"));
        siteHead.className = "rotate " + site;
        siteHead.appendChild(document.createElement("div")).innerHTML = site;
    });

    step.codes.forEach(function (code) {
        var rowObj = table.insertRow();
        var label = rowObj.appendChild(document.createElement("td"));
        label.innerHTML = code.code;
        step.allsites.forEach(function (site) {
            var num = rowObj.appendChild(document.createElement("td"));
            var entry = code.sites[site] || "0";
            num.innerHTML = entry;
            if (entry != "0")
                num.style.backgroundColor = "#ef4f4f";
        });
    });

    $(table).find("td").attr("align", "center");
}

function fillTables(wkflow) {

    $.ajax({
        url: "/workflowerrors",
        data: {workflow: wkflow},
        success: function (errors) {
            var tasks = document.getElementById("tasks");
            tasks.innerHTML = '';
            var tables = document.getElementById("tables");

            errors.forEach(function (step) {
                var ref = tasks.appendChild(document.createElement("a"));
                ref.href = "#" + step.step;
                ref.innerHTML = step.step;
                tasks.appendChild(document.createElement("br"))

                var tabHead = tables.appendChild(document.createElement("h2"));
                tabHead.id = step.step;
                tabHead.innerHTML = step.step;
                tables.appendChild(document.createElement("p")).
                    innerHTML = '<a href="#top">To top</a>';

                drawTable(step, tables.appendChild(document.createElement("table")));
            });

            setSiteStatuses();
        }
    });

}

function initPage(workflow) {
    fillTables(workflow);
    wfwebtool.workflowTable();
    prepareSubmit(workflow);
}
