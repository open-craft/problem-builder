function MentoringDataViewerBlock(runtime, element) {
    var handlerUrl = runtime.handlerUrl(element, 'get_data');

    $.get(handlerUrl, function(result) {
        $('.mentoring-dataviewer .mentoring-dataviewer-table', element).handsontable({
            data: result.data,
            colWidths: 300,
            rowHeaders: true,
            colHeaders: true,
            stretchH: 'all'
        });
    }, 'json');
}
