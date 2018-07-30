var wfwebtool = {

    describeError: function () {
        var url = new URL(location.toString());
        var wf = url.searchParams.get('workflow');

        $.ajax({url: '/classifyerror',
                data: {workflow: wf},
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
    },

    writeSimilar: function (similar) {
	if (!similar.length)
	    return;

        var url = new URL(location.toString());
        var wf = url.searchParams.get('workflow');

        var wftoggle = $("#multiwfs");

        // This should be called from the seeworkflow page, which has this parameter
        $.post({url: '/actedwfs',
		data: JSON.stringify({filtered: similar}),
		dataType: 'json',
		contentType: 'application/json',
		processData: false,
		success: function (acted_wfs) {
		    var button = document.getElementById("showmulti");
		    button.style.display = '';
		    var wfdiv = document.getElementById("wflist");

		    similar.forEach(function (wf) {
			    // Create an input box
			    var input = wfdiv.appendChild(document.createElement('input'));
			    input.type = 'checkbox';
			    input.name = 'workflows';
			    input.value = wf;

			    // Add a link after it
			    var wflink = wfdiv.appendChild(document.createElement('a'));
			    wflink.innerHTML = wf;
			    wflink.target = 'blank';
			    wflink.href = '?workflow=' + wf + '&issuggested=1';
			    wflink.className = acted_wfs.indexOf(wf) >= 0 ? 'acted' : 'notacted';

			    // New line
			    wfdiv.appendChild(document.createElement('br'));
			});

		    button.onclick = wftoggle.toggle;
                }
            });
    },

    fillSimilar: function () {
        var url = new URL(location.toString());

        if (url.searchParams.get('issuggested'))
            return;

        var wf = url.searchParams.get('workflow');

        $.ajax({
            // First we need to get the acted workflows
	    url: '/similarwfs',
            data: {workflow: wf},            // Then we fill the list of multiple workflows
            success: this.writeSimilar
        })
    },

    workflowTable: function () {
        this.describeError();
        this.fillSimilar();  
    }
};
