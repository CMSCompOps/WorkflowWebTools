function printSiteLists (method) {
    console.log(method);
};

function makeTable (option, params) {

    var methodsDiv = document.getElementById("sitemethods");
    methodsDiv.innerHTML = "";

    var paramsDiv = document.getElementById("actionparams");

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
                printSiteLists(event.target.value);
            };
            methodsDiv.appendChild(document.createTextNode(methods[method]));
        }
    }
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
    var simple_texts =  ["memory", "cores"];
    var xrd_opts =  {
        xrootd: ["enabled", "disabled"],
        secondary: ["enabled", "disabled"],
        splitting: split_list
    };
    var split_list = ["2x", "3x", "10x", "20x", "50x", "100x", "200x", "max"];

    [
        {
            action: "clone",
            description: "Kill and Clone",
            texts: simple_texts,
            opts: {
                "splitting": split_list
            }
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
            opts: {
                "action": ["by-pass", "force-complete", "on-hold"]
            },
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

            var params = [
                {
                    workflow: workflow
                }
            ];

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
