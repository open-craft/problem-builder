function AnswerBlock(runtime, element) {
    return {
        submit: function() {
            var input = $(':input', element),
                input_value = input.val().replace(/^\s+|\s+$/gm,''),
                answer_length = input_value.length,
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
