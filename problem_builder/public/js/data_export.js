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
                    'Data export failed. Reason: ' + status.last_export_result.error
                ));
            } else {
                startTime = new Date(status.last_export_result.start_timestamp * 1000);
                $statusArea.append($('<p>').text(
                    'A report is available for download.'
                ));
                $statusArea.append($('<p>').text(
                    'It was created at ' + startTime.toString() +
                    ' and took ' + status.last_export_result.generation_time_s.toFixed(1) +
                    ' seconds to finish.'
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
