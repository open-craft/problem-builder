// TODO: Split in two files

function display_message(message, messageView, checkmark){
    if (message) {
        var msg = '<div class="message-content">' + message + '</div>' +
                  '<button class="close icon-remove-sign fa-times-circle"></button>';
        messageView.showMessage(msg);
        if (checkmark) {
            checkmark.addClass('checkmark-clickable');
            checkmark.on('click', function(ev) {
                ev.stopPropagation();
                messageView.showMessage(msg);
            });
        }
    }
}

function MessageView(element, mentoring) {
    return {
        messageDOM: $('.feedback', element),
        allChoicesDOM: $('.choice', element),
        allPopupsDOM: $('.choice-tips, .feedback', element),
        allPopupContainersDOM: $('.choice-tips-container', element),
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
            var innerDOM = popupDOM.find('.tip-choice-group');
            if (data && data.width) {
                popupDOM.css('width', data.width);
                innerDOM.css('width', data.width);
            } else {
                popupDOM.css('width', '');
                innerDOM.css('width', '');
            }

            if (data && data.height) {
                popupDOM.css('height', data.height);
                popupDOM.css('maxHeight', data.height);
                innerDOM.css('maxHeight', data.height);
            } else {
                popupDOM.css('height', '');
                popupDOM.css('maxHeight', '');
                innerDOM.css('maxHeight', '');
            }

            var container = popupDOM.parent('.choice-tips-container');
            if (container.length) {
                this.allPopupContainersDOM.addClass('with-tips').removeClass('active');
                container.addClass('active');
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
            this.allPopupContainersDOM.removeClass('with-tips active');
            this.allChoicesDOM.removeClass('correct incorrect');
            this.allPopupsDOM.html('').hide();
            this.allResultsDOM.removeClass(
                'checkmark-incorrect icon-exclamation fa-exclamation checkmark-correct icon-ok fa-check'
            );
            this.allResultsDOM.attr('aria-label', '');
        }
    };
}

function MCQBlock(runtime, element) {
    var gettext = window.ProblemBuilderXBlockI18N.gettext;
    return {
        mentoring: null,
        init: function(options) {
            this.mentoring = options.mentoring;
            $('input[type=radio]', element).on('change', options.onChange);
        },

        submit: function() {
            var checkedRadio = $('input[type=radio]:checked', element);

            if(checkedRadio.length) {
                return {"value": checkedRadio.val()};
            } else {
                return null;
            }
        },

        handleReview: function(result){
            $('.choice input[value="' + result.submission + '"]', element).prop('checked', true);
            $('.choice input', element).prop('disabled', true);
        },

        handleSubmit: function(result, options) {

            var mentoring = this.mentoring;

            var messageView = MessageView(element, mentoring);

            messageView.clearResult();

            var choiceInputDOM = $('.choice-selector input[value="'+ result.submission +'"]', element);
            var choiceDOM = choiceInputDOM.closest('.choice');
            var choiceResultDOM = $('.choice-result', choiceDOM);
            var choiceTipsDOM = $('.choice-tips', choiceDOM);

            // We're showing previous answers, so go ahead and display results as well
            if (choiceInputDOM.prop('checked')) {
                choiceResultDOM.find('span.sr-only').remove();
                display_message(result.message, messageView, options.checkmark);
                if (result.status === "correct") {
                    choiceDOM.addClass('correct');
                    choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                    choiceResultDOM.attr('aria-label', choiceResultDOM.data('label_correct'));
                    choiceResultDOM.append('<span class="sr-only">'+gettext("Correct")+'</span>');
                } else {
                    choiceDOM.addClass('incorrect');
                    choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                    choiceResultDOM.attr('aria-label', choiceResultDOM.data('label_incorrect'));
                    choiceResultDOM.append('<span class="sr-only">'+gettext("Incorrect")+'</span>');
                }
                choiceResultDOM.off('click').on('click', function() {
                    if (choiceTipsDOM.html() !== '') {
                        messageView.showMessage(choiceTipsDOM);
                    }
                });
                if (result.tips) {
                    mentoring.setContent(choiceTipsDOM, result.tips);
                    messageView.showMessage(choiceTipsDOM);
                }
            }


            if (_.isNull(result.submission)) {
                messageView.showMessage('<div class="message-content">You have not provided an answer.</div>' +
                                        '<button class="close icon-remove-sign fa-times-circle"></button>');
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

function RatingBlock(runtime, element) {
    return MCQBlock(runtime, element);
}

function SwipeBlock(runtime, element) {
    return MCQBlock(runtime, element);
}

function MRQBlock(runtime, element) {
    var gettext = window.ProblemBuilderXBlockI18N.gettext;
    var ngettext = window.ProblemBuilderXBlockI18N.ngettext;
    return {
        mentoring: null,
        init: function(options) {
            this.mentoring = options.mentoring;
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

        handleReview: function(result) {
            $.each(result.submissions, function (index, value) {
                $('input[type="checkbox"][value="' + value + '"]').prop('checked', true);
            });
            $('input', element).prop('disabled', true);
        },

        handleSubmit: function(result, options) {

            var mentoring = this.mentoring;

            var messageView = MessageView(element, mentoring);

            var questionnaireDOM = $('fieldset.questionnaire', element);
            var data = questionnaireDOM.data();
            var hide_results = (data.hide_results === 'True' ||
                                (data.hide_prev_answer === 'True' && !mentoring.is_step_builder));
            // hide_prev_answer should only take effect when we initially render (previous) results,
            // so set hide_prev_answer to False after initial render.
            questionnaireDOM.data('hide_prev_answer', 'False');

            if (!hide_results) {
                display_message(result.message, messageView, options.checkmark);
            }

            // If user has never submitted an answer for this MRQ, `result` will be empty.
            // So we need to fall back on an empty list for `result.choices` to avoid errors in the next step:
            $.each(result.choices || [], function(index, choice) {
                var choiceInputDOM = $('.choice input[value='+choice.value+']', element);
                var choiceDOM = choiceInputDOM.closest('.choice');
                var choiceResultDOM = $('.choice-result', choiceDOM);
                var choiceTipsDOM = $('.choice-tips', choiceDOM);
                choiceResultDOM.find('span.sr-only').remove();
                /* show hint if checked or max_attempts is disabled */
                if (!hide_results &&
                    (result.completed || choiceInputDOM.prop('checked') || options.max_attempts <= 0)) {
                    if (choice.completed) {
                        choiceDOM.addClass('correct');
                        choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                        choiceResultDOM.attr('aria-label', choiceResultDOM.data('label_correct'));
                        choiceResultDOM.append('<span class="sr-only">'+gettext("Correct")+'</span>');
                    } else if (!choice.completed) {
                        choiceDOM.addClass('incorrect');
                        choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                        choiceResultDOM.attr('aria-label', choiceResultDOM.data('label_incorrect'));
                        choiceResultDOM.append('<span class="sr-only">'+gettext("Incorrect")+'</span>');
                    }

                    mentoring.setContent(choiceTipsDOM, choice.tips);

                    choiceResultDOM.off('click').on('click', function() {
                        if (choiceTipsDOM.html() !== '') {
                            messageView.showMessage(choiceTipsDOM);
                        }
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
