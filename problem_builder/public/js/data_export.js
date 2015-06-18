function DataExportBlock(runtime, element) {
    'use strict';
    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }
    var $startButton = $('.data-export-start', element);
    var $cancelButton = $('.data-export-cancel', element);
    var $downloadButton = $('.data-export-download', element);
    var $deleteButton = $('.data-export-delete', element);
    var status;
    function getStatus() {
        $.ajax({
            type: 'POST',
            url: runtime.handlerUrl(element, 'get_status'),
            data: '{}',
            success: updateStatus,
            dataType: 'json'
        });
    }
    function updateStatus(newStatus) {
        var statusChanged = newStatus !== status;
        status = newStatus;
        if (status.export_pending) {
            // Keep polling for status updates when an export is running.
            setTimeout(getStatus, 1000);
        }
        if (statusChanged) updateView();
    }
    function showSpinner() {
        $startButton.prop('disabled', true);
        $cancelButton.prop('disabled', true);
        $downloadButton.prop('disabled', true);
        $deleteButton.prop('disabled', true);
        $('.data-export-status', element).empty().append(
            $('<i>').addClass('icon fa fa-spinner fa-spin')
        );
    }
    function updateView() {
        var $statusArea = $('.data-export-status', element), startTime;
        $statusArea.empty();
        $startButton.toggle(!status.export_pending).prop('disabled', false);
        $cancelButton.toggle(status.export_pending).prop('disabled', false);
        $downloadButton.toggle(Boolean(status.download_url)).prop('disabled', false);
        $deleteButton.toggle(Boolean(status.last_export_result)).prop('disabled', false);
        if (status.last_export_result) {
            if (status.last_export_result.error) {
                $statusArea.append($('<p>').text(
                    _.template(
                        gettext('Data export failed. Reason: <%= error %>'),
                        {'error': status.last_export_result.error}
                    )
                ));
            } else {
                startTime = new Date(status.last_export_result.start_timestamp * 1000);
                $statusArea.append($('<p>').text(
                    gettext('A report is available for download.')
                ));
                $statusArea.append($('<p>').text(
                    _.template(
                        ngettext(
                            'It was created at <%= creation_time %> and took <%= seconds %> second to finish.',
                            'It was created at <%= creation_time %> and took <%= seconds %> seconds to finish.',
                            status.last_export_result.generation_time_s.toFixed(1)
                        ),
                        {
                            'creation_time': startTime.toString(),
                            'seconds': status.last_export_result.generation_time_s.toFixed(1)
                        }
                    )
                ));
            }
        } else {
            if (status.export_pending) {
                $statusArea.append($('<p>').text(
                    gettext('The report is currently being generated…')
                ));
            } else {
                $statusArea.append($('<p>').text(
                    gettext('No report data available.')
                ));
            }
        }
    }
    function addHandler($button, handlerName) {
        $button.on('click', function() {
            $.ajax({
                type: 'POST',
                url: runtime.handlerUrl(element, handlerName),
                data: '{}',
                success: updateStatus,
                dataType: 'json'
            });
            showSpinner();
        });
    }
    addHandler($startButton, 'start_export');
    addHandler($cancelButton, 'cancel_export');
    addHandler($deleteButton, 'delete_export');
    $downloadButton.on('click', function() {
        window.location.href = status.download_url;
    });
    showSpinner();
    getStatus();
}
