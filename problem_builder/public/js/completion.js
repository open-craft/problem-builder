function CompletionBlock(runtime, element) {

    var $completion = $('.pb-completion-value', element);

    return {
        mentoring: null,

        init: function(options) {
            this.mentoring = options.mentoring;
            $completion.on('change', options.onChange);
        },

        submit: function() {
            return $completion.is(':checked');
        },

        handleSubmit: function(result, options) {
            if (typeof result.submission !== 'undefined') {
                this.updateCompletion(result);
                if (!options.hide_results) {
                    $('.submit-result', element).css('visibility', 'visible');
                }
            }
        },

        handleReview: function(result) {
            this.updateCompletion(result);
            $completion.prop('disabled', true);
        },

        clearResult: function() {
            $('.submit-result', element).css('visibility', 'hidden');
        },

        updateCompletion: function(result) {
            $completion.prop('checked', result.submission);
        }
    };

}
