function DataExportBlock(runtime, element) {
    'use strict';
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
            dataType: 'json',
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
    function updateView() {
        var $statusArea = $('.data-export-status', element);
        $statusArea.empty();
        $startButton.toggle(!status.export_pending);
        $cancelButton.toggle(status.export_pending);
        $downloadButton.toggle(Boolean(status.download_url));
        $deleteButton.toggle(Boolean(status.last_export_result));
        if (status.last_export_result) {
            if (status.last_export_result.error) {
                $statusArea.append($('<p>').text(
                    'Data export failed. Reason: ' + status.last_export_result.error
                ));
            } else {
                $statusArea.append($('<p>').text(
                    'Date completed: ' + status.last_export_result.report_date
                ));
                $statusArea.append($('<p>').text(
                    'The report took ' + status.last_export_result.generation_time_s +
                    ' seconds to generate.'
                ));
            }
        } else {
            if (status.export_pending) {
                $statusArea.append($('<p>').text(
                    'The report is currently being generated…'
                ));
            } else {
                $statusArea.append($('<p>').text(
                    'No report data available.'
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
                dataType: 'json',
            });
        });
    }
    addHandler($startButton, 'start_export');
    addHandler($cancelButton, 'cancel_export');
    addHandler($deleteButton, 'delete_export');
    $downloadButton.on('click', function() {
        window.location.href = status.download_url;
    });
    getStatus();
}
