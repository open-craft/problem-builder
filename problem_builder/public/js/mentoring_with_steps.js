function MentoringWithStepsBlock(runtime, element) {

    var steps = runtime.children(element).filter(
        function(c) { return c.element.className.indexOf('pb-mentoring-step') > -1; }
    );
    var active_child = -1;
    var checkmark, submitDOM, nextDOM;

    function isLastChild() {
        return (active_child === steps.length-1);
    }

    function handleResults(response) {
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

    function initXBlockView() {
        checkmark = $('.assessment-checkmark', element);

        submitDOM = $(element).find('.submit .input-main');
        submitDOM.bind('click', submit);
        submitDOM.show();

        nextDOM = $(element).find('.submit .input-next');
        nextDOM.bind('click', displayNextChild);
        nextDOM.show();

        var options = {
            onChange: onChange
        };
        initSteps(options);

        displayNextChild();
    }

    initXBlockView();

}
