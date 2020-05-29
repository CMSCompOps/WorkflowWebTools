var allHeader = "All Steps (use this or fill all others)";

function normalize (s) {
    return s.replace(/__\d*$/, ""). // Remove the counter for separating radios
        replace(/^_+/, "");         // Remove leading "_". Don't remember what those are from.
}

function printSiteLists (method, params) {
    $(".sitelist").html("");

    if (method != "Auto")
        $(".paramtable").filter(
            function () {
                var length = $(this).find("h3 a").length;
                return (method == "Ban" ? length === 0 : length != 0);
            }
        ).each(
            function () {
                var step = $(this).find("h3 a").html();
                var torun = params.sitestorun[step] || [];

                var siteList = $(this).find(".sitelist")[0];
                params.allsites.forEach(function (site) {
                    var run = (torun.indexOf(site.site) >= 0);
                    var bad = (site.drain != "enabled");

                    var siteListDiv = siteList.appendChild(document.createElement("div"));
                    siteListDiv.className = "sitecheck";
                    if (bad)
                        siteListDiv.style.color = "red";
                    if (run)
                        siteListDiv.style.fontWeight = "900";

                    $(siteListDiv.appendChild(document.createElement("input"))).
                        attr("type", "checkbox").attr("name", "sites").
                        attr("value", site.site).
                        attr("checked", (method == "Ban" && bad) || (method != "Ban" && run && !bad));
                    siteListDiv.appendChild(document.createTextNode(site.site));
                });
                siteList.appendChild(document.createElement("div")).className = "clear";
            }
        );
};

function makeTable (option, params) {

    var methodsDiv = document.getElementById("sitemethods");
    methodsDiv.innerHTML = "";

    var paramsDiv = document.getElementById("actionparams");
    paramsDiv.innerHTML = "";

    function addParamTable (input) {
        var div = input || paramsDiv.appendChild(document.createElement("div"));
        $(div).addClass("paramtable");
        div.appendChild(document.createElement("div")).className = "sitelist";
        return div;
    };

    if (["acdc", "recovery"].indexOf(option.action) >= 0) {
        // ACDC is the most complex action, and needs parameters for each task and sites.
        var methods = ["Auto", "Manual", "Ban"];
        methodsDiv.appendChild(document.createElement("h4")).
            appendChild(document.createTextNode("Site Selection Method:"));

        methodsDiv.appendChild(document.createElement("p")).
            appendChild(document.createTextNode(
                "To see which sites are selected for this workflow under Auto, "
                    + "check what is automatically checked under Manual. "
                    + "Ban defaults to sites in drain. Same ban list applies to all tasks, "
                    + "which otherwise pick sites from Auto."
            ));

        for (method in methods) {
            var input = methodsDiv.appendChild(document.createElement("input"));
            input.type = "radio";
            input.name = "method";
            input.value = methods[method];
            input.checked = (method == 0)
            input.onclick = function (event) {
                printSiteLists(event.target.value, params);
            };
            methodsDiv.appendChild(document.createTextNode(methods[method]));
        }

        function addTaskHeader (inner) {
            var div = paramsDiv.appendChild(document.createElement("div"));
            var taskParamHeader = div.appendChild(document.createElement("h3"));
            taskParamHeader.innerHTML = inner;
            taskParamHeader.className = "taskparamhead";

            if (inner != allHeader) {
                $(div.appendChild(document.createElement("input"))).
                    attr("type", "checkbox").attr("class", "dothis");
                div.appendChild(document.createElement("span")).innerHTML = "Only this task";
                div.className = "stepdiv";
            }

            addParamTable(div);
        };

        addTaskHeader(allHeader);
        params.steps.forEach(function (step) {
            addTaskHeader('<a href="#' + step + '">' + step + '</a>');
        });

    }
    else
        addParamTable().style.margin = "15px 0px 15px 0px";

    counter = 0;

    $(".paramtable").each(function () {
        var paramtable = this;
        option.opts.forEach(function (opt) {
            var optDiv = paramtable.appendChild(document.createElement("div"));
            optDiv.appendChild(document.createElement("b")).innerHTML = normalize(opt.name) + ": ";

            opt.options.forEach(function (value) {
                optDiv.appendChild(document.createTextNode("    " + value + "  "));
                var radio = optDiv.appendChild(document.createElement("input"));
                radio.type = "radio";
                radio.name = opt.name + "__" + counter;
                radio.value = value;
                radio.ondblclick = function() {
                    this.checked = false;
                };
            });
        });

        option.texts.forEach(function (text) {
            var optDiv = paramtable.appendChild(document.createElement("div"));
            optDiv.appendChild(document.createElement("b")).innerHTML = normalize(text) + ": ";

            var input = optDiv.appendChild(document.createElement("input"));
            input.type = "text";
            input.name = text;
        });

        // Increment counter so that radio buttons are split
        counter++;
    });
};

var reasons = {
    reasons: {},
    fillReason: function (caller) {
        $(caller.parentNode).find(".shortreason").
            attr("value", caller.value);
        $(caller.parentNode).find(".longreason").
            html(reasons.reasons[caller.value] || "");
    },
    addReason: function () {
        var reasonDiv = document.getElementById("reasons");

        var reason = reasonDiv.appendChild(document.createElement("div"));
        reason.style.float = "left";

        var remover = reason.appendChild(document.createElement("button"));
        remover.type = "button";
        remover.innerHTML = "&#10006;";
        remover.onclick = function (event) {
            event.target.parentNode.remove();
            event.stopPropagation();
        };

        var content = reason.appendChild(document.createElement("div"));
        content.innerHTML = reasons.content;
        content.className = "reasoncontent";
    },
    content: '<img src="/static/img/loading.gif" alt="Loading...">',
}

function setReasons() {
    $.ajax({
        url: "/getreasons",
        success: function (response) {
            var liststring = "";

            response.forEach(function (reason) {
                reasons.reasons[reason.short] = reason.long;
                liststring = liststring + '<option value="' + reason.short + '">'
                    + reason.short + '</option>';
            });

            reasons.content = "Select reason: "
                + '<select name= "selectedreason" onchange="reasons.fillReason(this)">'
                + '<option  value="">New Reason</option>'
                + liststring
                + '</select> <br>'
                + 'Short Reason: <br>'
                + '<input name="shortreason" class="shortreason" type="text"> <br>'
                + 'Long Reason: <br>'
                + '<textarea name="longreason" class="longreason" type="text" rows="10"></textarea> <br>'
            ;

            $("reasoncontent").html(reasons.content);
        }
    });
}

function addOptions (form, params) {
    var split_list = ["2x", "3x", "10x", "20x", "50x", "100x", "200x", "max"];
    var simple_texts =  ["memory", "cores"];
    var xrd_opts =  [
        {name: "xrootd", options: ["enabled", "disabled"]},
        {name: "secondary", options: ["enabled", "disabled"]},
        {name: "splitting", options: split_list}
    ];

    [
        {
            action: "clone",
            description: "Kill and Clone",
            texts: simple_texts,
            opts: [
                {name: "splitting", options: split_list}
            ]
        },
        {
            action: "acdc",
            description: "ACDC",
            texts: simple_texts,
            opts: xrd_opts
        },
        {
            action: "recovery",
            description: "Recovery (not ACDC)",
            texts: [
                "memory",
                "group",
                "cores"
            ],
            opts: xrd_opts
        },
        {
            action: "special",
            description: "Other action",
            opts: [
                {name: "_action", options: ["by-pass", "force-complete", "on-hold"]},
            ],
            texts: [
                "other",
            ]
        }
    ].forEach(function (option) {

        var optspan = form.appendChild(document.createElement("span"));
        $(optspan).attr("id", "opt" + option.action);

        $(optspan.appendChild(document.createElement("input"))).
            attr("type", "radio").attr("name", "action").attr("value", option.action).
            click(function () {
                makeTable(option, params)
            });

        optspan.appendChild(document.createTextNode(option.description));

    });

    form.appendChild(document.createElement("br"));
}

function paramsOfDiv (sel) {
    var output = {};
    $(sel).find("input:radio:checked, input:text").each(function () {
        output[normalize(this.name)] = this.value;
    });
    return output;
}

function buildSubmit (workflow, sitesToRun, allsites) {
    var action = $("form input[name=action]:checked").val();
    var siteMethod = $("#sitemethods input:radio:checked").val();

    if (siteMethod == "Ban")
        var banned = $(".sitecheck input:checked").map(function (i, ele) { return ele.value }).get();

    var params = function () {
        if (["acdc", "recovery"].indexOf(action) >= 0) {
            var allSteps = {};
            var onlySteps = {};
            $(".stepdiv").each(
                function () {
                    var sel = $(this);

                    var stepName = sel.find(".taskparamhead a").html();
                    var stepParams = paramsOfDiv(this);
                    stepParams["sites"] = function () {
                        if (siteMethod == "Auto") {
                            // Filter out drained
                            var siteMap = {};
                            allsites.forEach(function (site) {
                                    siteMap[site.site] = site.drain;
                                });

                            return sitesToRun[stepName].filter(function (site) {return siteMap[site] == 'enabled';});
                        }
                        if (siteMethod == "Manual")
                            return sel.find(".sitecheck input:checked").map(function (i, ele) { return ele.value }).get();
                        // Otherwise, filter out Banned
                        return sitesToRun[stepName].filter(function (site) {return banned.indexOf(site) < 0});
                    } ();

                    var saveName = stepName.replace("/" + workflow + "/", "");
                    allSteps[saveName] = stepParams;
                    if (sel.find(".dothis:checked").length)
                        onlySteps[saveName] = stepParams;
                }
            );
            return $.isEmptyObject(onlySteps) ? allSteps : onlySteps;
        }
        else {
            return paramsOfDiv(".paramtable");
        }
    } ();

    var output = [
        {
            workflow: workflow,
            parameters: {
                Action: action,
                Reasons: $(".longreason").map(function(i, ele) { return ele.value }).get(),
                ACDCs: [],
                Parameters: params
            }
        }
    ];
    return output;
}


function showStatus(workflow) {
    $.ajax({
        url: "/getstatus",
        data: {"workflow": workflow},
        success: function (status) {
            document.getElementById("actionstatus").innerHTML = "Action: " + status.status;
        }
    });
}


function makeForm(workflow) {

    $.ajax({
        url: "/submissionparams",
        data: {"workflow": workflow},
        success: function (params) {
            var formDiv = document.getElementById("submitform");
            $(formDiv).find(".loading").remove()

            var form = formDiv.appendChild(document.createElement("form"));
            form.action = "javascript:;";
            form.onsubmit = function () {
                submission = buildSubmit(workflow, params.sitestorun, params.allsites);
                if (confirm("Will submit " + JSON.stringify(submission))) {
                    $.ajax({
                        url: "/submit2",
                        type: "POST",
                        dataType: "json",
                        contentType : 'application/json',
                        data: JSON.stringify({documents: submission}),
                        success: function () {
                            showStatus(workflow);
                            alert('Action Submitted');
                        }
                    });
                }
            };

            addOptions(form, params);

            form.appendChild(document.createElement("div")).id = "sitemethods";
            form.appendChild(document.createElement("div")).id = "actionparams";

            var button = form.appendChild(document.createElement("button"));
            button.type = "button";
            button.innerHTML = "Add Reason";
            button.onclick = reasons.addReason;

            form.appendChild(document.createElement("div")).id = "reasons";
            form.appendChild(document.createElement("br")).clear = "both";

            $(form.appendChild(document.createElement("input"))).
                attr("type", "submit").attr("value", "Submit");

            formDiv.appendChild(form);
        }
    });

}

function prepareSubmit (workflow) {
    makeForm(workflow);
    setReasons();
    showStatus(workflow);
};
