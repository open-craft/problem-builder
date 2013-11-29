function MentoringDataExportBlock(runtime, element) {
    var downloadUrl = runtime.handlerUrl(element, 'download_csv');

    $('button.download', element).click(function(ev) {
        ev.preventDefault();
        window.location = downloadUrl;
    });
}
