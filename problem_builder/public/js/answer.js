function AnswerBlock(runtime, element) {
    return {
        mode: null,
        init: function(options) {
            // register the child validator
            $(':input', element).on('keyup', options.onChange);

            this.mode = options.mode;
            var checkmark = $('.answer-checkmark', element);
            var completed = $('.xblock-answer', element).data('completed');
            if (completed === 'True' && this.mode === 'standard') {
                checkmark.addClass('checkmark-correct icon-ok fa-check');
            }
        },

        submit: function() {
            return $(':input', element).serializeArray();
        },

        handleReview: function(result) {
            $('textarea', element).prop('disabled', true);
        },

        handleSubmit: function(result) {

            var checkmark = $('.answer-checkmark', element);
            $(element).find('.message').text((result || {}).error || '');

            this.clearResult();

            if (this.mode === 'assessment') {
                // Display of checkmark would be redundant.
                return
            }

            if (result.status === "correct") {
                checkmark.addClass('checkmark-correct icon-ok fa-check');
            }
            else {
                checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
            }
        },

        clearResult: function() {
            var checkmark = $('.answer-checkmark', element);
            checkmark.removeClass(
                'checkmark-incorrect icon-exclamation fa-exclamation checkmark-correct icon-ok fa-check'
            );
        },

        // Returns `true` if the child is valid, else `false`
        validate: function() {

            // return true if the answer is read only
            var blockquote_ro = $('blockquote.answer.read_only', element);
            if (blockquote_ro.length > 0)
                return true;

            var input = $(':input', element);
            var input_value = input.val().replace(/^\s+|\s+$/gm,'');
            var answer_length = input_value.length;
            var data = input.data();

            // an answer cannot be empty event if min_characters is 0
            if (_.isNumber(data.min_characters)) {
                var min_characters = _.max([data.min_characters, 1]);
                if (answer_length < min_characters) {
                    return false;
                }
            }
            return true;
        }
    };
}
