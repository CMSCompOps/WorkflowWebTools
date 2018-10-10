var wfwebtool = function () {
    // This function deterimines which page is open
    // and what function to run
    // to fill it properly

    var functions = {
        '/seeworkflow' : this.workflowTable
    };

    functions[this.url.pathname] ();
}

wfwebtool.url = new URL(location.toString());


wfwebtool.writeParams = function () {
    var wf = this.url.searchParams.get('workflow');

    $.ajax({
        url: '/wkfparams',
        data: {workflow: wf},
        success: function (params) {

            var toWrite = document.getElementById('wkfparams');

            if (params.RequestType) {

                toWrite.innerHTML =
                    'Request Type: ' + params.RequestType + '<br>' +
                    'Sub-Request Type: ' + params.SubRequestType + '<br>' +
                    'Memory: ' + params.Memory + '<br>' +
                    'Estimated Number of Jobs: ' + (params.TotalEstimatedJobs || '?');

                if (params.RequestType == 'Resubmission')
                    $('#optclone').remove();

                $('a').each(function () {

                    var newUrl = $(this).attr('href').replace("PREPID", params.PrepID);
                    $(this).attr('href', newUrl);

                });

            } else {

                toWrite.style.color = 'red';
                toWrite.innerHTML = 'Problem retrieving info (likely an expired certificate, use link above)';

            }
        }
    });
};


wfwebtool.describeError = function () {

    var wf = this.url.searchParams.get('workflow');

    $.ajax({
        url: '/classifyerror',
        data: {workflow: wf},
        timeout: 0,  // This one can be long
        success: function (error) {

            // Maximum error and link to report
            document.getElementById('maxerror').innerHTML =
                '<a href="/explainerror?errorcode=' + error.maxerror +
                '&workflowstep=/' + wf +
                '">' + error.maxerror + '</a>';

            // Display types
            document.getElementById('errortypes').innerHTML =
                error.types || 'Not Reported';

            // Display recommendation
            document.getElementById('errorrecommend').innerHTML =
                error.recommended;

            if (error.params) {

                // Get the whole div and append some stuff to the end
                var info = document.getElementById('errorinfo');

                info.appendChild(document.createElement('br'));
                var head = info.appendChild(document.createElement('span'));
                head.style['font-weight'] = 'bold';
                head.innerHTML = 'AdditionalParameters:';
                info.appendChild(document.createElement('br'));
                info.appendChild(document.createElement('span')).innerHTML = error.params;

            }
        }
    });
};


wfwebtool.fillSimilar = function () {

    if (this.url.searchParams.get('issuggested'))
        return;

    var wf = this.url.searchParams.get('workflow');
    var wftoggle = $("#multiwfs");

    $.ajax({
        // First we need to get the acted workflows
        url: '/similarwfs',
        data: {workflow: wf},            // Then we fill the list of multiple workflows
        success: function (data) {
            var button = document.getElementById("showmulti");
            button.style.display = '';
            var wfdiv = document.getElementById("wflist");

            data.similar.forEach(function (simwf) {
                // Create an input box
                var input = wfdiv.appendChild(document.createElement('input'));
                input.type = 'checkbox';
                input.name = 'workflows';
                input.value = simwf;

                // Add a link after it
                var wflink = wfdiv.appendChild(document.createElement('a'));
                wflink.innerHTML = simwf;
                wflink.target = 'blank';
                wflink.href = '?workflow=' + simwf + '&issuggested=1';
                wflink.className = data.acted.indexOf(simwf) >= 0 ? 'acted' : 'notacted';

                // New line
                wfdiv.appendChild(document.createElement('br'));
            });

            button.onclick = function () {
                wftoggle.toggle();
            };
        }
    });
};


function reset(wkfl) {
    theSpan = document.getElementById('reset');
    theSpan.innerHTML = 'Refreshing page, please wait...';
    $.ajax({
        url: '/resetcache?workflow=' + wkfl,
        success: function () {
            theSpan.style.color = 'red';
            theSpan.innerHTML = 'Refreshing page...';
            location.reload();
        }
    })
};


wfwebtool.workflowTable = function () {
    // These are a bunch of separate functions to fill in the page
    this.describeError();
    this.writeParams();
    this.fillSimilar();
};
