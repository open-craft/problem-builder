function MentoringWithStepsBlock(runtime, element) {

    var steps = runtime.children(element).filter(
        function(c) { return c.element.className.indexOf('pb-mentoring-step') > -1; }
    );
    var step = $('.mentoring', element).data('step');
    var active_child, checkmark, submitDOM, nextDOM, tryAgainDOM, submitXHR;

    function isLastChild() {
        return (active_child === steps.length-1);
    }

    function updateStep() {
        var handlerUrl = runtime.handlerUrl(element, 'update_step');
        $.post(handlerUrl, JSON.stringify(step+1))
            .success(function(response) {
                step = response.step;
            });
    }

    function handleResults(response) {
        // Update step so next step is shown on page reload (even if user does not click "Next Step")
        updateStep();

        // Update UI
        if (response.completed === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
        } else if (response.completed === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
        }

        submitDOM.attr('disabled', 'disabled');

        nextDOM.removeAttr("disabled");
        if (nextDOM.is(':visible')) { nextDOM.focus(); }

        if (isLastChild()) {
            tryAgainDOM.removeAttr('disabled');
            tryAgainDOM.show();
        }
    }

    function submit() {
        // We do not handle submissions at this level, so just forward to "submit" method of current step
        var child = steps[active_child];
        child['submit'](handleResults);
    }

    function hideAllSteps() {
        for (var i=0; i < steps.length; i++) {
            $(steps[i].element).hide();
        }
    }

    function cleanAll() {
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');
        hideAllSteps();
    }

    function displayNextChild() {
        cleanAll();
        findNextChild();
        nextDOM.attr('disabled', 'disabled');
        validateXBlock();
    }

    function findNextChild() {
        // find the next real child block to display. HTMLBlock are always displayed
        ++active_child;
        var child = steps[active_child];
        $(child.element).show();
    }

    function onChange() {
        // We do not allow users to modify answers belonging to a step after submitting them:
        // Once an answer has been submitted (next button is enabled),
        // start ignoring changes to the answer.
        if (nextDOM.attr('disabled')) {
            validateXBlock();
        }
    }

    function validateXBlock() {
        var is_valid = true;
        var child = steps[active_child];
        if (child) {
            is_valid = child['validate']();
        }
        if (!is_valid) {
            submitDOM.attr('disabled', 'disabled');
        } else {
            submitDOM.removeAttr('disabled');
        }
        if (isLastChild()) {
            nextDOM.hide();
        }
    }

    function initSteps(options) {
        for (var i=0; i < steps.length; i++) {
            var step = steps[i];
            step['initChildren'](options);
        }
    }

    function handleTryAgain(result) {
        if (result.result !== 'success')
            return;

        active_child = -1;
        displayNextChild();
        tryAgainDOM.hide();
        submitDOM.show();
        if (! isLastChild()) {
            nextDOM.show();
        }
    }

    function tryAgain() {
        var handlerUrl = runtime.handlerUrl(element, 'try_again');
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify({})).success(handleTryAgain);
    }

    function initXBlockView() {
        checkmark = $('.assessment-checkmark', element);

        submitDOM = $(element).find('.submit .input-main');
        submitDOM.bind('click', submit);
        submitDOM.show();

        nextDOM = $(element).find('.submit .input-next');
        nextDOM.bind('click', displayNextChild);
        nextDOM.show();

        tryAgainDOM = $(element).find('.submit .input-try-again');
        tryAgainDOM.bind('click', tryAgain);

        var options = {
            onChange: onChange
        };
        initSteps(options);

        active_child = step;
        active_child -= 1;
        displayNextChild();
    }

    initXBlockView();

}
