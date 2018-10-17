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
                        attr("checked", (method == "Ban" && bad) || (method != "Ban" && run));
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
        div.className = "paramtable";
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

            addParamTable(div);
        };

        addTaskHeader("All Steps (use this or fill all others)");
        params.steps.forEach(function (step) {
            addTaskHeader('<a href="#' + step + '">' + step + '</a>');
        });

    }
    else
        addParamTable().style.margin = "15px 0px 15px 0px";

    $(".paramtable").each(function () {
        var paramtable = this;
        option.opts.forEach(function (opt) {
            var optDiv = paramtable.appendChild(document.createElement("div"));
            optDiv.appendChild(document.createElement("b")).innerHTML = opt.name + ": ";

            opt.options.forEach(function (value) {
                optDiv.appendChild(document.createTextNode("    " + value + "  "));
                var radio = optDiv.appendChild(document.createElement("input"));
                radio.type = "radio";
                radio.name = opt.name;
                radio.value = value;
                radio.ondblclick = function() {
                    this.checked = false;
                };
            });
        });

        option.texts.forEach(function (text) {
            var optDiv = paramtable.appendChild(document.createElement("div"));
            optDiv.appendChild(document.createElement("b")).innerHTML = text + ": ";

            var input = optDiv.appendChild(document.createElement("input"));
            input.type = "text";
            input.name = text;
        });
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
                {name: "action", options: ["by-pass", "force-complete", "on-hold"]},
            ],
            texts: [
                "other",
            ]
        }
    ].forEach(function (option) {

        $(form.appendChild(document.createElement("input"))).
            attr("type", "radio").attr("name", "action").attr("value", option.action).
            click(function () {
                makeTable(option, params)
            });

        form.appendChild(document.createTextNode(option.description));

    });

    form.appendChild(document.createElement("br"));
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
                alert("Submitted");
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
                attr("type", "submit").attr("value", "Submit").click(function () {
                    var output = [
                        {
                            workflow: workflow
                        }
                    ];
                    // Create a JavaScript Object of all the parameters and send them
                });

            formDiv.appendChild(form);
        }
    });

}

function prepareSubmit (workflow) {
    makeForm(workflow);
    setReasons();
};
