function AnswerBlock(runtime, element) {
    return {
        submit: function() {
            var input = $(':input', element),
                answer_length = input.val().length,
                data = input.data();

            if (_.isNumber(data.min_characters) &&
                (data.min_characters > 0) &&
                (answer_length < data.min_characters)) {
              throw "The answer has a minimum of " + data.min_characters + " characters.";
            }
            return input.serializeArray();
        },
        handleSubmit: function(result) {
            $(element).find('.message').text((result || {}).error || '');
        }
    }
}
