function MentoringEditBlock(runtime, element) {
    $('.save-button').bind('click', function() {
        var data = {
            'xml_content': $('#mentoring-xml-content').val(),
        };
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        $.post(handlerUrl, JSON.stringify(data)).complete(function() {
            // TODO-MRQ: Error handling
            window.location.reload(false);
        });
    });
}
