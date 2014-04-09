function AnswerBlock(runtime, element) {
    return {

        init: function(options) {
          // register the child validator
          $(':input', element).on('keyup', options.blockValidator);
        },

        submit: function() {
            return $(':input', element).serializeArray();
        },

        handleSubmit: function(result) {
            var checkmark = $('.answer-checkmark', element);
            $(element).find('.message').text((result || {}).error || '');

            checkmark.removeClass(
              'checkmark-incorrect icon-exclamation fa-exclamation checkmark-correct icon-ok fa-check'
            );
            if (result.completed) {
                checkmark.addClass('checkmark-correct icon-ok fa-check');
            }
            else {
                checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
            }
        },

        // Returns `true` if the child is valid, else `false`
        validate: function() {
            var input = $(':input', element),
                input_value = input.val().replace(/^\s+|\s+$/gm,''),
                answer_length = input_value.length,
                data = input.data();

            // an answer cannot be empty event if min_characters is 0
            if (_.isNumber(data.min_characters)) {
                var min_characters = _.max([data.min_characters, 1]);
                if (answer_length < min_characters) {
                    return false;
                }
            }

            return true;
        }
    }
}
