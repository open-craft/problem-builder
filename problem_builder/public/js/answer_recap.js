function AnswerRecapBlock(runtime, element) {
    return {
        init: function(options) {
            // In the LMS, the HTML of multiple units can be loaded at once,
            // and the user can flip among them. If that happens, the answer in
            // our HTML may be out of date.
            this.refreshAnswer();
        },

        refreshAnswer: function() {
            $.ajax({
                type: 'POST',
                url: runtime.handlerUrl(element, 'refresh_html'),
                data: '{}',
                dataType: 'json',
                success: function(data) {
                    $(element).html(data.html);
                }
            });
        }
    };
}
