function SliderBlock(runtime, element) {
    var $slider = $('.pb-slider-range', element);
    return {
        mode: null,
        mentoring: null,

        value: function() {
            return parseInt($slider.val());
        },

        init: function(options) {
            this.mentoring = options.mentoring;
            this.mode = options.mode;
            $slider.on('change', options.onChange);
        },

        submit: function() {
            return this.value();
        },

        handleReview: function(result){
            $slider.val(result.submission);
            $slider.prop('disabled', true);
        },

        handleSubmit: function(result) {
            // Show a green check if the user has submitted a valid value:
            if (typeof result.submission !== "undefined") {
                $('.submit-result', element).css('visibility', 'visible');
            }
        },

        clearResult: function() {
            $('.submit-result', element).css('visibility', 'hidden');
        },

        validate: function(){
            return Boolean(this.value() >= 0 && this.value() <= 100);
        }
    };
}
