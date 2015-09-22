function MentoringWithStepsEdit(runtime, element) {
    "use strict";

    var blockIsPresent = function(klass) {
        return $('.xblock ' + klass).length > 0;
    };

    var updateButton = function(button, condition) {
        button.toggleClass('disabled', condition);
    };

    var disableButton = function(ev) {
        if ($(this).is('.disabled')) {
            ev.preventDefault();
            ev.stopPropagation();
        } else {
            $(this).addClass('disabled');
        }
    };

    var initButtons = function(dataCategory) {
        var $buttons = $('.add-xblock-component-button[data-category='+dataCategory+']', element);
        $buttons.each(function() {
            if (dataCategory === 'pb-message') {
                var msg_type = $(this).data('boilerplate');
                updateButton($(this), blockIsPresent('.submission-message.'+msg_type));
            } else {
                updateButton($(this), blockIsPresent('.xblock-header-sb-review-step'));
            }
        });
        $buttons.on('click', disableButton);
    };

    initButtons('pb-message');
    initButtons('sb-review-step');

    ProblemBuilderUtil.transformClarifications(element);
    StudioEditableXBlockMixin(runtime, element);
}
