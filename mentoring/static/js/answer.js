function AnswerBlock(runtime, element) {
    return {
        submit: function() {
            return $(element).find(':input').serializeArray();
        },
        handleSubmit: function(result) {
            $(element).find('.message').text((result || {}).error || '');
        }
    }
}
