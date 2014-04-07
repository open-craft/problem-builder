// TODO: Split in two files
function MessageView(element) {
  return {
    messageDOM: $('.feedback', element),
    allPopupsDOM: $('.choice-tips, .feedback', element),
    clearPopupEvents: function() {
      this.allPopupsDOM.hide();
      $('.close', this.allPopupsDOM).off('click');
    },
    showPopup: function(popupDOM) {
      var self = this;
      this.clearPopupEvents();
      popupDOM.show();
      popupDOM.on('click', function() {
        self.clearPopupEvents();
      });
    },
    showMessage: function(message) {
      if (_.isString(message)) {
        this.messageDOM.html(message);
        this.showPopup(this.messageDOM);
      }
      else {
        this.showPopup(message); // already a DOM
      }
    }
  }
}

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
            var messageView = MessageView(element);
            var choiceInputs = $('.choice input', element);
            $.each(choiceInputs, function(index, choiceInput) {
                var choiceInputDOM = $(choiceInput),
                    choiceDOM = choiceInputDOM.closest('.choice'),
                    choiceResultDOM = $('.choice-result', choiceDOM),
                    choiceTipsDOM = $('.choice-tips', choiceDOM),
                    choiceTipsCloseDOM;

                choiceResultDOM.removeClass(
                  'checkmark-incorrect icon-exclamation fa-exclamation checkmark-correct icon-ok fa-check'
                );
                if (result.completed && choiceInputDOM.val() === result.submission) {
                    choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                }
                else if (choiceInputDOM.val() === result.submission || _.isNull(result.submission)) {
                    choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                }

              var tips = _.find(result.tips, function(obj) {
                           return obj.choice === choiceInputDOM.val();
                         });
              if (tips) {
                  choiceTipsDOM.html(tips.tips);
              }

              choiceTipsCloseDOM = $('.close', choiceTipsDOM);
                choiceResultDOM.off('click').on('click', function() {
                    if (choiceTipsDOM.html() != '') {
                      messageView.showMessage(choiceTipsDOM);
                    }
                });
            });

            if (_.isNull(result.submission)) {
                messageView.showMessage('<div class="message-content"><div class="close"></div>' +
                                        'You have not provided an answer.' + '</div>');
            }
            else if (result.tips) {
                var tips = _.find(result.tips, function(obj) {
                               return obj.choice === result.submission;
                           });
                if (tips) {
                    messageView.showMessage(tips.tips);
                } else {
                    messageView.clearPopupEvents();
                }
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

        handleSubmit: function(result, options) {
            var messageView = MessageView(element);

            if (result.message) {
                messageView.showMessage('<div class="message-content"><div class="close"></div>' +
                                        result.message + '</div>');
            }

            $.each(result.choices, function(index, choice) {
                var choiceInputDOM = $('.choice input[value='+choice.value+']', element),
                    choiceDOM = choiceInputDOM.closest('.choice'),
                    choiceResultDOM = $('.choice-result', choiceDOM),
                    choiceTipsDOM = $('.choice-tips', choiceDOM),
                    choiceTipsCloseDOM;

                choiceResultDOM.removeClass(
                  'checkmark-incorrect icon-exclamation checkmark-correct icon-ok fa-check'
                );

                /* show hint if checked or max_attempts is disabled */
                if (result.completed || choiceInputDOM.prop('checked') || options.max_attempts <= 0) {
                  if (choice.completed) {
                    choiceResultDOM.addClass('checkmark-correct icon-ok fa-check');
                  } else if (!choice.completed) {
                    choiceResultDOM.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
                  }
                }

                choiceTipsDOM.html(choice.tips);

                choiceTipsCloseDOM = $('.close', choiceTipsDOM);
                choiceResultDOM.off('click').on('click', function() {
                    messageView.showMessage(choiceTipsDOM);
                });

            });
        }

    };
}
