// Client side code for the Problem Builder Dashboard XBlock
// So far, this code is only used to generate a downloadable report.
function ExportBase(runtime, element, initData) {
    "use strict";

    var reportTemplate = initData.reportTemplate;

    var generateDataUriFromImageURL = function(imgURL) {
        // Given the URL to an image, IF the image has already been cached by the browser,
        // returns a data: URI with the contents of the image (image will be converted to PNG)
        var img = new Image();
        img.src = imgURL;
        if (!img.complete)
            return imgURL;

        // Create an in-memory canvas from which we can extract a data URL:
        var canvas = document.createElement("canvas");
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        // Draw the image onto our temporary canvas:
        canvas.getContext('2d').drawImage(img, 0, 0);
        return canvas.toDataURL("image/png");
    };

    var unicodeStringToBase64 = function(str) {
        // Convert string to base64. A bit weird in order to support unicode, per
        // https://developer.mozilla.org/en-US/docs/Web/API/WindowBase64/btoa
        return window.btoa(unescape(encodeURIComponent(str)));
    };

    var downloadReport = function(ev) {
        // Download Report:
        // Change the URL to a data: URI before continuing with the click event.
        if ($(this).attr('href').charAt(0) == '#') {
            var $report = $(initData.reportContentSelector, element).clone();
            // Convert all images in $report to data URIs:
            $report.find('image').each(function() {
                var origURL = $(this).attr('xlink:href');
                $(this).attr('xlink:href', generateDataUriFromImageURL(origURL));
            });
            // Take the resulting HTML and put it into the template we have:
            var wrapperHTML = reportTemplate.replace('REPORT_GOES_HERE', $report.html());
            //console.log(wrapperHTML);
            var dataURI = "data:text/html;base64," + unicodeStringToBase64(wrapperHTML);
            $(this).attr('href', dataURI);
        }
    };

    var $downloadLink = $('.report-download-link', element);
    $downloadLink.on('click', downloadReport);
}

function PBDashboardBlock(runtime, element, initData) {
    new ExportBase(runtime, element, initData);
}

function MentoringTableBlock(runtime, element, initData) {
    // Display an excerpt for long answers, with a "more" link to display the full text
    $('.answer-table', element).shorten({
        moreText: 'more',
        lessText: 'less',
        showChars: '500'
    });
    new ExportBase(runtime, element, initData)
}
