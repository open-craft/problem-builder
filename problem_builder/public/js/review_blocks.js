// Client side code for the Problem Builder Dashboard XBlock
// So far, this code is only used to generate a downloadable report.
function ExportBase(runtime, element, initData) {
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

    var $element = $(element),
        $shareButton = $element.find('.mentoring-share-button'),
        $doShareButton = $element.find('.do-share-button'),
        $shareMenu = $element.find('.mentoring-share-with'),
        $displayDropdown = $element.find('.mentoring-display-dropdown'),
        $errorHolder = $element.find('.share-errors'),
        $deleteShareButton = $element.find('.remove-share'),
        $newShareContainer = $($element.find('.new-share-container')[0]),
        $addShareField = $($element.find('.add-share-field')[0]),
        $notification = $($element.find('.share-notification')),
        $closeNotification = $($element.find('.notification-close')),
        tableLoadURL = runtime.handlerUrl(element, 'table_render'),
        deleteShareUrl = runtime.handlerUrl(element, 'remove_share'),
        sharedListLoadUrl = runtime.handlerUrl(element, 'get_shared_list'),
        clearNotificationUrl = runtime.handlerUrl(element, 'clear_notification'),
        shareResultsUrl = runtime.handlerUrl(element, 'share_results');

    function loadTable(data) {
        $element.find('.mentoring-table-target').html(data['content']);
        $('.answer-table', element).shorten({
            moreText: 'more',
            lessText: 'less',
            showChars: '500'
        });
    }

    function errorMessage(event) {
        $errorHolder.text(JSON.parse(event.responseText)['error'])
    }

    function sharedRefresh(data) {
        $element.find('.shared-with-container').html(data['content']);
        $deleteShareButton = $($deleteShareButton.selector);
        $deleteShareButton.on('click', deleteShare);
    }

    function postShareRefresh(data) {
        sharedRefresh(data);
        $element.find(".new-share-container").each(function(index, container) {
            if (index === 0) {
                var $container = $(container);
                $container.find('.add-share-username').val('');
                $container.find('.add-share-field').show();
                return;
            }
            $(container).remove()
        });
        $errorHolder.html('');
    }

    function postShare() {
        $.ajax({
            type: "POST",
            url: sharedListLoadUrl,
            data: JSON.stringify({}),
            success: postShareRefresh,
            error: errorMessage
        });
    }

    function updateShare() {
        var usernames = [];
        $element.find('.add-share-username').each(function(index, username) {
            usernames.push($(username).val())
        });
        $.ajax({
            type: "POST",
            url: shareResultsUrl,
            data: JSON.stringify({'usernames': usernames}),
            success: postShare,
            error: errorMessage
        });
    }

    function menuHider(event) {
        if (!$(event.target).closest($shareMenu).length) {
            // We're clicking outside of the menu, so hide it.
            $shareMenu.hide();
            $(document).off('click.mentoring_share_menu_hide');
        }
    }

    $shareButton.on('click', function (event) {
        if (!$shareMenu.is(':visible')){
            event.stopPropagation();
            $(document).on('click.mentoring_share_menu_hide', menuHider);
            $shareMenu.show();
        }
    });
    $doShareButton.on('click', updateShare);

    function postLoad(data) {
        loadTable(data);
        new ExportBase(runtime, element, initData);
    }

    $.ajax({
        type: "POST",
        url: tableLoadURL,
        data: JSON.stringify({'target_username': $displayDropdown.val()}),
        success: postLoad
    });

    $.ajax({
        type: "POST",
        url: sharedListLoadUrl,
        data: JSON.stringify({}),
        success: sharedRefresh
    });

    $displayDropdown.on('change', function () {
        if ($displayDropdown[0].selectedIndex !== 0) {
            $shareButton.prop('disabled', true);
            $element.find('.report-download-container').hide();
        } else {
            $shareButton.prop('disabled', false);
            $element.find('.report-download-container').show();
        }
        $.ajax({
            type: "POST",
            url: tableLoadURL,
            data: JSON.stringify({'target_username': $displayDropdown.val()}),
            success: loadTable
        })
    });

    function addShare() {
        var container = $newShareContainer.clone();
        container.find('.add-share-username').val('');
        container.insertAfter($element.find('.new-share-container').last());
        container.find('.add-share-field').on('click', addShare);
        var buttons = $element.find('.new-share-container .add-share-field');
        buttons.hide();
        buttons.last().show();
    }

    function deleteShare(event) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: deleteShareUrl,
            data: JSON.stringify({'username': $(event.target).parent().prev()[0].innerHTML}),
            success: function () {
                $(event.target).parent().parent().remove();
                $errorHolder.html('');
            },
            error: errorMessage
        });
    }

    $closeNotification.on('click', function () {
        // Don't need server approval to hide it.
        $notification.hide();
        $.ajax({
            type: "POST",
            url: clearNotificationUrl,
            data: JSON.stringify({'usernames': $notification.data('shared')})
        })
    });

    $addShareField.on('click', addShare);
}
