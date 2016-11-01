function MentoringEditComponents(runtime, element) {
    "use strict";
    // Disable "add" buttons when a message of that type already exists:
    var $buttons = $('.add-xblock-component-button[data-category=pb-message]', element);
    var updateButtons = function() {
        $buttons.each(function() {
            var msg_type = $(this).data('boilerplate');
            $(this).toggleClass('disabled', $('.xblock .submission-message.'+msg_type).length > 0);
        });
    };
    updateButtons();
    $buttons.click(function(ev) {
        if ($(this).is('.disabled')) {
            ev.preventDefault();
            ev.stopPropagation();
        } else {
            $(this).addClass('disabled');
        }
    });

    ProblemBuilderUtil.transformClarifications(element);

    runtime.listenTo('deleted-child', updateButtons);
}
