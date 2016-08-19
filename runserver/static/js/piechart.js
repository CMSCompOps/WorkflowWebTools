// List the colors for the pie chart.
// Will eventually want to link severity of errors to different colors

var colors = ["#ff0000","#00ff00","#0000ff","#00ffff","#ff00ff","#ffff00","#808080","#ffffff"];

// This function finds multiple canvases and draws pie charts onto them

function drawpiecharts() {
    var iChart;
    var canvases = document.getElementsByClassName("piechart");
    var ncanvases = Math.min(canvases.length, arguments.length);
    for (iChart = 0; iChart < ncanvases; iChart++) {
        var data = arguments[iChart];
        data.sort(function(a, b){return b-a});
        var total = 0;
        for (var point in data)
            total += data[point];

        var canvas = canvases[iChart];
        var context = canvas.getContext("2d");
        var centerX = canvas.width/2;
        var centerY = canvas.height/2;
        var radius = Math.min(centerX, centerY) * total/(10 + total);
        var currangle = 0;

        var ndivisions = Math.min(colors.length, data.length);
        var iDivision;
        for (iDivision = 0; iDivision < ndivisions; iDivision++) {
            var nextangle = currangle + 2 * Math.PI * data[iDivision]/total;
            context.beginPath();
            context.arc(centerX, centerY, radius, currangle, nextangle);
            context.lineTo(centerX, centerY);
            context.fillStyle = colors[iDivision];
            context.fill();
            currangle = nextangle;
        }
    }
}
