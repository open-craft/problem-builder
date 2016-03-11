// Client side code for the Problem Builder Dashboard XBlock
// So far, this code is only used to generate a downloadable report.
function PBDashboardBlock(runtime, element, initData) {
    "use strict";

    var reportTemplate = initData.reportTemplate;

    var generateDataUriFromImageURL = function(imgURL) {
        // Given the URL to an image, IF the image has already been cached by the browser,
        // returns a data: URI with the contents of the image (image will be converted to PNG)

        // Expand relative urls and urls without an explicit protocol into absolute urls
        var a = document.createElement('a');
        a.href = imgURL;
        imgURL = a.href;

        // If the image is from another domain, just return its URL. We can't
        // create a data URL from cross-domain images:
        // https://html.spec.whatwg.org/multipage/scripting.html#dom-canvas-todataurl
        if (a.origin !== window.location.origin)
            return imgURL;

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
            var $report = $('.dashboard-report', element).clone();
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
