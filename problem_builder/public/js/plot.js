function PlotBlock(runtime, element) {

    // jQuery helpers

    jQuery.fn.isEmpty = function() {
        return !$.trim($(this).html());
    };

    jQuery.fn.isHidden = function() {
        // Don't use jQuery :hidden selector here;
        // this is necessary to ensure that result is independent of parent visibility
        return $(this).css('display') === 'none';
    };

    jQuery.fn.isVisible = function() {
        // Don't use jQuery :visible selector here;
        // this is necessary to ensure that result is independent of parent visibility
        return $(this).css('display') !== 'none';
    };

    // Plot

    // Define margins
    var margins = {top: 20, right: 20, bottom: 20, left: 20};

    // Define width and height of SVG viewport
    var width = 440,
        height = 440;

    // Define dimensions of plot area
    var plotWidth = width - margins.left - margins.right,
        plotHeight = height - margins.top - margins.bottom;

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
        .orient("bottom")
        .tickValues([]);

    var yAxis = d3.svg.axis()
        .scale(yScale)
        .orient("left")
        .tickValues([]);

    // Create SVG group elements for axes and call the xAxis and yAxis functions
    var xAxisGroup = svgContainer.append("g")
        .attr("transform", "translate(0, " + plotHeight / 2 + ")")
        .call(xAxis);

    var yAxisGroup = svgContainer.append("g")
        .attr("transform", "translate(" + plotWidth / 2 + ", 0)")
        .call(yAxis);

    // Buttons

    var defaultButton = $('.plot-default', element),
        averageButton = $('.plot-average', element),
        quadrantsButton = $('.plot-quadrants', element),
        overlayButtons = $('input.plot-overlay', element);

    // Claims

    var defaultClaims = defaultButton.data('claims'),
        averageClaims = averageButton.data('claims');

    // Colors

    var defaultColor = defaultButton.data('point-color'),
        averageColor = averageButton.data('point-color');

    // Quadrant labels

    var q1Label = quadrantsButton.data('q1-label'),
        q2Label = quadrantsButton.data('q2-label'),
        q3Label = quadrantsButton.data('q3-label'),
        q4Label = quadrantsButton.data('q4-label');

    // Event handlers

    function toggleOverlay(claims, color, klass, refresh) {
        var selector = buildSelector(klass),
            selection = svgContainer.selectAll(selector);
        if (selection.empty()) {
            showOverlay(selection, claims, color, klass);
        } else {
            hideOverlay(selection);
            if (refresh) {
                toggleOverlay(claims, color, klass);
            }
        }
    }

    function buildSelector(klass) {
        var classes = klass.split(' ');
        if (classes.length === 1) {
            return "." + klass;
        }
        return '.' + classes.join('.');
    }

    function showOverlay(selection, claims, color, klass) {
        selection
            .data(claims)
            .enter()
            .append("circle")
            .attr("class", klass)
            .attr("data-tooltip", function(d) {
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
    }

    function hideOverlay(selection) {
        selection.remove();
    }

    function toggleBorderColor(button, color, refresh) {
        var $button = $(button),
            overlayOn = $button.data("overlay-on");
        if (overlayOn && !refresh) {
            $button.css("border-color", "rgb(237, 237, 237)");  // Default color: grey
            $button.data("overlay-on", false);
        } else {
            $button.css("border-color", color);
            $button.data("overlay-on", true);
        }
    }

    function toggleOverlayInfo(klass, hide) {
        var plotInfo = $('.plot-info', element),
            selector = buildSelector(klass),
            overlayInfo = plotInfo.children(selector);
        if (hide || overlayInfo.isVisible()) {
            overlayInfo.hide();
            var overlayInfos = plotInfo.children('.plot-overlay'),
                hidePlotInfo = true;
            overlayInfos.each(function() {
                var overlayInfo = $(this);
                hidePlotInfo = hidePlotInfo && (overlayInfo.isHidden() || overlayInfo.isEmpty());
            });
            if (hidePlotInfo) {
                plotInfo.hide();
            }
        } else {
            overlayInfo.show();
            if (!overlayInfo.isEmpty() && !plotInfo.isVisible()) {
                plotInfo.show();
            }
        }
    }

    function toggleQuadrantLabels() {
        var selection = svgContainer.selectAll(".quadrant-label"),
            quadrantLabelsOn = quadrantsButton.val() === 'On';
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

    defaultButton.on('click', function(event, refresh) {
        toggleOverlay(defaultClaims, defaultColor, 'claim-default', refresh);
        toggleBorderColor(this, defaultColor, refresh);
    });

    averageButton.on('click', function() {
        toggleOverlay(averageClaims, averageColor, 'claim-average');
        toggleBorderColor(this, averageColor);
    });

    quadrantsButton.on('click', function() {
        toggleQuadrantLabels();
    });

    overlayButtons.each(function(index) {

        var overlayButton = $(this),
            claims = overlayButton.data('claims'),
            color = overlayButton.data('point-color'),
            klass = overlayButton.attr('class');

        overlayButton.on('click', function() {
            toggleOverlay(claims, color, klass);
            toggleBorderColor(this, color);
            toggleOverlayInfo(klass);
        });

        // Hide overlay info initially
        toggleOverlayInfo(klass, 'hide');

    });

    // Quadrant labels are off initially; color of button for toggling them should reflect this
    quadrantsButton.css("border-color", "red");

    // Hide plot info initially
    $('.plot-info', element).hide();

    // API

    var dataXHR;

    return {

        update: function() {
            var handlerUrl = runtime.handlerUrl(element, 'get_data');
            if (dataXHR) {
                dataXHR.abort();
            }
            dataXHR = $.post(handlerUrl, JSON.stringify({}))
                .success(function(response) {
                    defaultClaims = response.default_claims;
                    averageClaims = response.average_claims;

                    // Default overlay should be visible initially.
                    // Might still be visible from a previous attempt;
                    // in that case, we refresh it:
                    defaultButton.trigger('click', 'refresh');

                    // Average overlay should be hidden initially.
                    // This is the default when (re-)loading the page from scratch.
                    // However, the overlay might still be visible from a previous attempt;
                    // in that case, we hide it:
                    var selection = svgContainer.selectAll('.claim-average');
                    if (!selection.empty()) {
                        hideOverlay(selection);
                        toggleBorderColor(averageButton, averageColor);
                    }
                });
        }

    };

}
