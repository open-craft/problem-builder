function MentoringEditBlock(runtime, element) {
    var xmlEditorTextarea = $('.block-xml-editor', element),
        xmlEditor = CodeMirror.fromTextArea(xmlEditorTextarea[0], { mode: 'xml' });

    $('.save-button', element).bind('click', function() {
        var handlerUrl = runtime.handlerUrl(element, 'studio_submit'),
            data = {
                'xml_content': xmlEditor.getValue(),
            };

        $('.error-message', element).html();
        $.post(handlerUrl, JSON.stringify(data)).done(function(response) {
            if (response.result === 'success') {
                window.location.reload(false);
            } else {
                $('.error-message', element).html('Error: '+response.message);
            }
        });
    });

    $('.cancel-button', element).bind('click', function() {
        runtime.notify('cancel', {});
    });
}
