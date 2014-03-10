// TODO: Split in two files

function MCQBlock(runtime, element) {
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
            var tipsDom = $(element).parent().find('.messages'),
                tipHtml = (result || {}).tips || '';

            if(tipHtml) {
                tipsDom.append(tipHtml);
            }
        }
    };
}

function MRQBlock(runtime, element) {
    return {
        submit: function() {
            var checkedCheckboxes = $('input[type=checkbox]:checked', element),
                checkedValues = [];

            $.each(checkedCheckboxes, function(index, checkedCheckbox) {
                checkedValues.push($(checkedCheckbox).val());
            });
            return checkedValues;
        },

        handleSubmit: function(result) {
            $.each(result.choices, function(index, choice) {
                var choice_input_dom = $('.choice input[value='+choice.value+']', element),
                    choice_dom = choice_input_dom.closest('.choice'),
                    choice_result_dom = $('.choice-result', choice_dom),
                    choice_tips_dom = $('.choice-tips', choice_dom);

                if (choice.completed) {
                    choice_result_dom.removeClass('incorrect').addClass('correct');
                } else {
                    choice_result_dom.removeClass('correct').addClass('incorrect');
                }

                choice_tips_dom.html(choice.tips);
            });
        }
    };
}
