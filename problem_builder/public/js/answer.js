function AnswerBlock(runtime, element) {
    return {
        init: function(options) {
            // Clear results and validate block when answer changes
            $(':input', element).on('keyup', options.onChange);

            this.validateXBlock = options.validateXBlock;

            // In the LMS, the HTML of multiple units can be loaded at once,
            // and the user can flip among them. If that happens, the answer in
            // our HTML may be out of date.
            this.refreshAnswer();
        },

        submit: function() {
            var freeform_answer = $(':input', element);

            if(freeform_answer.length) {
                return {"value": freeform_answer.val()};
            } else {
                return null;
            }
        },

        handleReview: function(result) {
            $('textarea', element).prop('disabled', true);
        },

        handleSubmit: function(result, options) {

            var checkmark = $('.answer-checkmark', element);

            this.clearResult();

            if (options.hide_results) {
                return;
            }
            if (result.status) {
                if (result.status === "correct") {
                    checkmark.addClass('checkmark-correct icon-ok fa-check');
                    checkmark.attr('aria-label', checkmark.data('label_correct'));
                }
                else {
                    checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                    checkmark.attr('aria-label', checkmark.data('label_incorrect'));
                }
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

            // An answer cannot be empty even if min_characters is 0
            if (_.isNumber(data.min_characters)) {
                var min_characters = _.max([data.min_characters, 1]);
                if (answer_length < min_characters) {
                    return false;
                }
            }
            return true;
        },

        refreshAnswer: function() {
            var self = this;
            $.ajax({
                type: 'POST',
                url: runtime.handlerUrl(element, 'answer_value'),
                data: '{}',
                dataType: 'json',
                success: function(data) {
                    // Update the answer to the latest, unless the user has made an edit
                    var newAnswer = data.value;
                    var $textarea = $(':input', element);
                    var currentAnswer = $textarea.val();
                    var origAnswer = $('.orig-student-answer', element).text();
                    if (currentAnswer == origAnswer && currentAnswer != newAnswer) {
                        $textarea.val(newAnswer);
                    }
                    if (self.validateXBlock) {
                      self.validateXBlock();
                    }
                },
            });
        }
    };
}
