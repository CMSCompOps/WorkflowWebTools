var reasons = {
    reasons: {},
    fillReason: function (caller) {
        $(caller.parentNode).find(".shortreason").
            attr("value", caller.value);
        $(caller.parentNode).find(".longreason").
            html(reasons.reasons[caller.value] || '');
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
            var liststring = '';

            response.forEach(function (reason) {
                reasons.reasons[reason.short] = reason.long;
                liststring = liststring + '<option value="' + reason.short + '">'
                    + reason.short + '</option>';
            });

            reasons.content = 'Select reason: '
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
    [
        {
            action: "clone",
            description: "Kill and Clone"
        },
        {
            action: "acdc",
            description: "ACDC"
        },
        {
            action: "recovery",
            description: "Recovery (not ACDC)"
        },
        {
            action: "special",
            description: "Other action"
        }
    ].forEach(function (option) {
        $(form.appendChild(document.createElement("input"))).
            attr("type", "radio").attr("name", "action").attr("value", option.action).
            click(function () {
                makeTable(option.action, params)
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

            $(form.appendChild(document.createElement("input"))).
                attr("type", "hidden").attr("name", "workflows").attr("value", workflow);

            addOptions(form, params);

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
};
