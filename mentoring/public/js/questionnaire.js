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
            var messageDOM = $('.choice-message', element),
                allPopupsDOM = $('.choice-tips, .choice-message', element),
                clearPopupEvents = function() {
                    allPopupsDOM.hide();
                    $('.close', allPopupsDOM).off('click');
                },
                showPopup = function(popupDOM) {
                    clearPopupEvents();
                    popupDOM.show();

                    popupDOM.on('click', function() {
                        clearPopupEvents();
                        choiceTipsDOM.hide();
                    });
                };

            if (result.message) {
                messageDOM.html('<div class="message-content"><div class="close"></div>' + 
                                result.message + '</div>');
                showPopup(messageDOM);
            }

            $.each(result.choices, function(index, choice) {
                var choiceInputDOM = $('.choice input[value='+choice.value+']', element),
                    choiceDOM = choiceInputDOM.closest('.choice'),
                    choiceResultDOM = $('.choice-result', choiceDOM),
                    choiceTipsDOM = $('.choice-tips', choiceDOM),
                    choiceTipsCloseDOM;

                if (choice.completed) {
                    choiceResultDOM.removeClass('incorrect').addClass('correct');
                } else {
                    choiceResultDOM.removeClass('correct').addClass('incorrect');
                }

                choiceTipsDOM.html(choice.tips);

                choiceTipsCloseDOM = $('.close', choiceTipsDOM);
                choiceResultDOM.off('click').on('click', function() {
                    showPopup(choiceTipsDOM);
                });
            });
        }
    };
}
