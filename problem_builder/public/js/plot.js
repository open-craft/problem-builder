function PlotBlock(runtime, element) {

    // Define margins
    var margins = {top: 20, right: 20, bottom: 20, left: 20};

    // Define width and height of SVG viewport
    var width = 440;
    var height = 440;

    // Define dimensions of plot area
    var plotWidth = width - margins.left - margins.right;
    var plotHeight = height - margins.top - margins.bottom;

    // Preselect target DOM element for plot.
    // This is necessary because when using a CSS selector,
    // d3.select will select the *first* element that matches the selector (in document traversal order),
    // which leads to unintended consequences when multiple plot blocks are present.
    var plotTarget = $(element).find('.sb-plot').get(0);

    // Create SVG viewport with nested group for plot area
    var svgContainer = d3.select(plotTarget)
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .append("g")
        .attr("transform", "translate(" + margins.left + ", " + margins.right + ")");

    // Create scales to use for axes and data
    var xScale = d3.scale.linear()
        .domain([0, 100])
        .range([0, plotWidth]);

    var yScale = d3.scale.linear()
        .domain([100, 0])
        .range([0, plotHeight]);

    // Create axes
    var xAxis = d3.svg.axis()
        .scale(xScale)
        .orient("bottom");

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left");

    // Create SVG group elements for axes and call the xAxis and yAxis functions
    var xAxisGroup = svgContainer.append("g")
        .attr("transform", "translate(0, " + plotHeight / 2 + ")")
        .call(xAxis);

    var yAxisGroup = svgContainer.append("g")
        .attr("transform", "translate(" + plotWidth / 2 + ", 0)")
        .call(yAxis);

    // Claims

    var defaultClaims = $('.plot-default', element).data('claims');
    var averageClaims = $('.plot-average', element).data('claims');


    // Colors

    var defaultColor = $('.plot-default', element).data('point-color');
    var averageColor = $('.plot-average', element).data('point-color');

    // Quadrant labels

    var q1Label = $('.plot-quadrants', element).data('q1-label');
    var q2Label = $('.plot-quadrants', element).data('q2-label');
    var q3Label = $('.plot-quadrants', element).data('q3-label');
    var q4Label = $('.plot-quadrants', element).data('q4-label');

    // Event handlers

    var defaultButton = $('.plot-default', element);
    var averageButton = $('.plot-average', element);

    function toggleOverlay(claims, color, klass) {
        var selector = "." + klass;
        var selection = svgContainer.selectAll(selector);
        if (selection.empty()) {
            svgContainer.selectAll(selector)
                .data(claims)
                .enter()
                .append("circle")
                .attr("class", klass)
                .attr("title", function(d) {
                    return d[0] + ": " + d[1] + ", " + d[2];
                })
                .attr("cx", function(d) {
                    return xScale(d[1]);
                })
                .attr("cy", function(d) {
                    return yScale(d[2]);
                })
                .attr("r", 5)
                .style("fill", color);
        } else {
            selection.remove();
        }
    }

    function toggleBorderColor(button, color) {
        var $button = $(button);
        var overlayOn = $button.data("overlay-on");
        if (overlayOn) {
            $button.css("border-color", "rgb(237, 237, 237)");  // Default color: grey
        } else {
            $button.css("border-color", color);
        }
        $button.data("overlay-on", !overlayOn);
    }

    defaultButton.on('click', function() {
        toggleOverlay(defaultClaims, defaultColor, 'claim-default');
        toggleBorderColor(this, defaultColor);
    });

    averageButton.on('click', function() {
        toggleOverlay(averageClaims, averageColor, 'claim-average');
        toggleBorderColor(this, averageColor);
    });

    var quadrantsButton = $('.plot-quadrants', element);

    function toggleQuadrantLabels() {
        var selection = svgContainer.selectAll(".quadrant-label");
        var quadrantLabelsOn = quadrantsButton.val() === 'On';
        if (quadrantLabelsOn) {
            selection.remove();
            quadrantsButton.val("Off");
            quadrantsButton.css("border-color", "red");
        } else {
            var labels = [
                [0.75 * plotWidth, 0, q1Label],
                [0.25 * plotWidth, 0, q2Label],
                [0.25 * plotWidth, plotHeight, q3Label],
                [0.75 * plotWidth, plotHeight, q4Label]
            ];
            selection.data(labels)
                .enter()
                .append("text")
                .attr("class", 'quadrant-label')
                .attr("x", function(d) {
                    return d[0];
                })
                .attr("y", function(d) {
                    return d[1];
                })
                .text(function(d) {
                    return d[2];
                })
                .attr("text-anchor", "middle")
                .attr("font-family", "sans-serif")
                .attr("font-size", "16px")
                .attr("fill", "black");
            quadrantsButton.val("On");
            quadrantsButton.css("border-color", "green");
        }
    }

    quadrantsButton.on('click', function() {
        toggleQuadrantLabels();
    });

    // Show default overlay initially

    defaultButton.trigger('click');

    // Quadrant labels are off initially; color of button for toggling them should reflect this

    quadrantsButton.css("border-color", "red");

}
