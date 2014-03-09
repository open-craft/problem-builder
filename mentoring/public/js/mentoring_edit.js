function MentoringEditBlock(runtime, element) {
    var xml_editor_textarea = $('.block-xml-editor', element),
        xml_editor = CodeMirror.fromTextArea(xml_editor_textarea[0], { mode: 'xml' });

    $('.save-button').bind('click', function() {
        var data = {
            'xml_content': xml_editor.getValue(),
        };

        var handlerUrl = runtime.handlerUrl(element, 'studio_submit');
        $.post(handlerUrl, JSON.stringify(data)).complete(function() {
            // TODO-MRQ: Error handling
            window.location.reload(false);
        });
    });
}
