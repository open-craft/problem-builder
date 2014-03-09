function QuestionnaireBlock(runtime, element) {
    return {
        handleSubmit: function(result) {
            var tipsDom = $(element).parent().find('.messages'),
                tipHtml = (result || {}).tips || '';

            if(tipHtml) {
                tipsDom.append(tipHtml);
            }
        }
    }
}

function MCQBlock(runtime, element) {
    var init = QuestionnaireBlock(runtime, element);

    init.submit = function() {
        var checkedRadio = $('input[type=radio]:checked', element);

        if(checkedRadio.length) {
            return checkedRadio.val();
        } else {
            return null;
        }
    };

    return init;
}
