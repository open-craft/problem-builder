function QuizzBlock(runtime, element) {
    return {
        submit: function() {
            var checkedRadio = $('input[type=radio]:checked', element);

            if(checkedRadio.length) {
                return checkedRadio.val();
            } else {
                return null;
            }
        },
        handleSubmit: function(result) {
            var tipsDom = $(element).parent().find('.quizz-tips'),
                tipHtml = (result || {}).tip || '';

            if(tipHtml) {
                tipsDom.append(tipHtml);
            }
        }
    }
}
