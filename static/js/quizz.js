function QuizzBlock(runtime, element) {
    return {
        submit: function() {
            var checked_radio = $('input[type=radio]:checked', element);

            if(checked_radio.length) {
                return checked_radio.val();
            } else {
                return null;
            }
        },
        handleSubmit: function(result) {
            var tips_dom = $(element).parent().find('.quizz-tips'),
                tip_html = (result || {}).tip || '';

            if(tip_html) {
                tips_dom.append(tip_html);
            }
        }
    }
}
