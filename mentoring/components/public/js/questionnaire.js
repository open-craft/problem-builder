// TODO: Split in two files

function MessageView(element, mentoring) {
    return {
        messageDOM: $('.feedback', element),
        allPopupsDOM: $('.choice-tips, .feedback', element),
        allResultsDOM: $('.choice-result', element),
        clearPopupEvents: function() {
            this.allPopupsDOM.hide();
            $('.close', this.allPopupsDOM).off('click');
        },
        showPopup: function(popupDOM) {
            var self = this;
            this.clearPopupEvents();

            // Set the width/height
            var tip = $('.tip', popupDOM)[0];
            var data = $(tip).data();
            if (data && data.width) {
                popupDOM.css('width', data.width);
            } else {
                popupDOM.css('width', '');
            }

            if (data && data.height) {
                popupDOM.css('height', data.height);
            } else {
                popupDOM.css('height', '');
            }

            popupDOM.show();

            mentoring.publish_event({
                event_type:'xblock.mentoring.feedback.opened',
                content: $(popupDOM).text()
            });

            $('.close', popupDOM).on('click', function() {
                self.clearPopupEvents();
                mentoring.publish_event({
                    event_type:'xblock.mentoring.feedback.closed',
                    content: $(popupDOM).text()
                });
            });
        },
        showMessage: function(message) {
            if (_.isString(message)) {
                mentoring.setContent(this.messageDOM, message);
                this.showPopup(this.messageDOM);
            }
            else {
                this.showPopup(message); // already a DOM
            }
        },
        clearResult: function() {
            this.allPopupsDOM.html('').hide();
            this.allResultsDOM.removeClass(
                'checkmark-incorrect icon-exclamation fa-exclamation checkmark-correct icon-ok fa-check'
            );
        }
    };
}

function MCQBlock(runtime, element) {
    return {
        mode: null,
        mentoring: null,
        init: function(options) {
            this.mentoring = options.mentoring;
            this.mode = options.mode;
            $('input[type=radio]', element).on('change', options.onChange);
        },

        submit: function() {
            var checkedRadio = $('input[type=radio]:checked', element);

            if(checkedRadio.length) {
                return checkedRadio.val();
            } else {
                return null;
            }
        },

        handleSubmit: function(result) {
            if (this.mode === 'assessment')
                return;

            mentoring = this.mentoring;

            var messageView = MessageView(element, mentoring);
            messageView.clearResult();

            var choiceInputs = $('.choice input', element);
            $.each(choiceInputs, function(index, choiceInput) {
                var choiceInputDOM = $(choiceInput);
                var choiceDOM = choiceInputDOM.closest('.choice');
                var choiceResultDOM = $('.choice-result', choiceDOM);
                var choiceTipsDOM = $('.choice-tips', choiceDOM);
                var choiceTipsCloseDOM;

                if (result.status === "correct" && choiceInputDOM.val() === result.submission) {
                    choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                }
                else if (choiceInputDOM.val() === result.submission || _.isNull(result.submission)) {
                    choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                }

                if (result.tips && choiceInputDOM.val() === result.submission) {
                    mentoring.setContent(choiceTipsDOM, result.tips);
                }

                choiceTipsCloseDOM = $('.close', choiceTipsDOM);
                choiceResultDOM.off('click').on('click', function() {
                    if (choiceTipsDOM.html() !== '') {
                        messageView.showMessage(choiceTipsDOM);
                    }
                });
            });

            if (_.isNull(result.submission)) {
                messageView.showMessage('<div class="message-content">You have not provided an answer.</div>' +
                                        '<div class="close icon-remove-sign fa-times-circle"></div>');
            }
            else if (result.tips) {
                messageView.showMessage(result.tips);
            }
        },

        clearResult: function() {
            MessageView(element, this.mentoring).clearResult();
        },

        validate: function(){
            var checked = $('input[type=radio]:checked', element);
            return Boolean(checked.length);
        }
    };
}

function MRQBlock(runtime, element, mentoring) {
    return {
        mode: null,
        mentoring: null,
        init: function(options) {
            this.mentoring = options.mentoring;
            this.mode = options.mode;
            $('input[type=checkbox]', element).on('change', options.onChange);
        },

        submit: function() {
            var checkedCheckboxes = $('input[type=checkbox]:checked', element);
            var checkedValues = [];

            $.each(checkedCheckboxes, function(index, checkedCheckbox) {
                checkedValues.push($(checkedCheckbox).val());
            });
            return checkedValues;
        },

        handleSubmit: function(result, options) {
            if (this.mode === 'assessment')
                return;

            mentoring = this.mentoring;

            var messageView = MessageView(element, mentoring);

            if (result.message) {
                messageView.showMessage('<div class="message-content">' + result.message + '</div>'+
                                        '<div class="close icon-remove-sign fa-times-circle"></div>');
            }

            var questionnaireDOM = $('fieldset.questionnaire', element);
            var data = questionnaireDOM.data();
            var hide_results = (data.hide_results === 'True') ? true : false;

            $.each(result.choices, function(index, choice) {
                var choiceInputDOM = $('.choice input[value='+choice.value+']', element);
                var choiceDOM = choiceInputDOM.closest('.choice');
                var choiceResultDOM = $('.choice-result', choiceDOM);
                var choiceTipsDOM = $('.choice-tips', choiceDOM);
                var choiceTipsCloseDOM;

                /* show hint if checked or max_attempts is disabled */
                if (!hide_results &&
                    (result.completed || choiceInputDOM.prop('checked') || options.max_attempts <= 0)) {
                    if (choice.completed) {
                        choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                    } else if (!choice.completed) {
                        choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                    }

                    mentoring.setContent(choiceTipsDOM, choice.tips);

                    choiceTipsCloseDOM = $('.close', choiceTipsDOM);
                    choiceResultDOM.off('click').on('click', function() {
                        messageView.showMessage(choiceTipsDOM);
                    });
                }
            });
        },

        clearResult: function() {
            MessageView(element, this.mentoring).clearResult();
        },

        validate: function(){
            var checked = $('input[type=checkbox]:checked', element);
            if (checked.length) {
                return true;
            }
            return false;
        }

    };
}
