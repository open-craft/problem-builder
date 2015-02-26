function MentoringAssessmentView(runtime, element, mentoring) {
    var gradeTemplate = _.template($('#xblock-grade-template').html());
    var submitDOM, nextDOM, reviewDOM, tryAgainDOM;
    var submitXHR;
    var checkmark;
    var active_child;

    var callIfExists = mentoring.callIfExists;

    function cleanAll() {
        // clean checkmark state
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');

        // Clear all selections
        $('input[type=radio], input[type=checkbox]', element).prop('checked', false);

        // hide all questions
        mentoring.hideAllSteps();

        $('.grade').html('');
        $('.attempts').html('');
    }

    function renderGrade() {
        var data = $('.grade', element).data();
        cleanAll();
        $('.grade', element).html(gradeTemplate(data));
        reviewDOM.hide();
        submitDOM.hide();
        nextDOM.hide();
        tryAgainDOM.show();

        var attempts_data = $('.attempts', element).data();
        if (attempts_data.num_attempts >= attempts_data.max_attempts) {
            tryAgainDOM.attr("disabled", "disabled");
        }
        else {
            tryAgainDOM.removeAttr("disabled");
        }

        mentoring.renderAttempts();
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
        var success = true;
        var handlerUrl = runtime.handlerUrl(element, 'try_again');
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify({})).success(handleTryAgain);
    }

    function initXBlockView() {
        submitDOM = $(element).find('.submit .input-main');
        nextDOM = $(element).find('.submit .input-next');
        reviewDOM = $(element).find('.submit .input-review');
        tryAgainDOM = $(element).find('.submit .input-try-again');
        checkmark = $('.assessment-checkmark', element);

        submitDOM.show();
        submitDOM.bind('click', submit);
        nextDOM.bind('click', displayNextChild);
        nextDOM.show();
        reviewDOM.bind('click', renderGrade);
        tryAgainDOM.bind('click', tryAgain);

        active_child = mentoring.step;

        var options = {
            onChange: onChange
        };
        mentoring.initChildren(options);
        if (isDone()) {
            renderGrade();
        } else {
            active_child = active_child - 1;
            displayNextChild();
        }

        mentoring.renderDependency();
    }

    function isLastChild() {
        return (active_child == mentoring.steps.length-1);
    }

    function isDone() {
        return (active_child == mentoring.steps.length);
    }

    function displayNextChild() {
        cleanAll();

        // find the next real child block to display. HTMLBlock are always displayed
        active_child++;
        var child = mentoring.steps[active_child];
        $(child.element).show();
        mentoring.publish_event({
            event_type: 'xblock.mentoring.assessment.shown',
            exercise_id: child.name
        });

        if (isDone())
            renderGrade();
        nextDOM.attr('disabled', 'disabled');
        reviewDOM.attr('disabled', 'disabled');
        validateXBlock();
    }

    function onChange() {
        // Assessment mode does not allow to modify answers.
        // Once an answer has been submitted (next button is enabled),
        // start ignoring changes to the answer.
        if (nextDOM.attr('disabled')) {
            validateXBlock();
        }
    }

    function handleSubmitResults(result) {
        $('.grade', element).data('score', result.score);
        $('.grade', element).data('correct_answer', result.correct_answer);
        $('.grade', element).data('incorrect_answer', result.incorrect_answer);
        $('.grade', element).data('partially_correct_answer', result.partially_correct_answer);
        $('.grade', element).data('max_attempts', result.max_attempts);
        $('.grade', element).data('num_attempts', result.num_attempts);
        $('.attempts', element).data('max_attempts', result.max_attempts);
        $('.attempts', element).data('num_attempts', result.num_attempts);

        if (result.completed === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
        } else if (result.completed === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
        }

        submitDOM.attr('disabled', 'disabled');

        /* Something went wrong with student submission, denied next question */
        if (result.step != active_child+1) {
            active_child = result.step-1;
            displayNextChild();
        } else {
            nextDOM.removeAttr("disabled");
            reviewDOM.removeAttr("disabled");
        }
    }

    function submit() {
        var success = true;
        var data = {};
        var child = mentoring.steps[active_child];
        if (child && child.name !== undefined) {
            data[child.name] = callIfExists(child, 'submit');
        }
        var handlerUrl = runtime.handlerUrl(element, 'submit');
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify(data)).success(handleSubmitResults);
    }

    function validateXBlock() {
        var is_valid = true;
        var data = $('.attempts', element).data();
        var steps = mentoring.steps;

        // if ((data.max_attempts > 0) && (data.num_attempts >= data.max_attempts)) {
        //     is_valid = false;
        // }
        var child = mentoring.steps[active_child];
        if (child && child.name !== undefined) {
            var child_validation = callIfExists(child, 'validate');
            if (_.isBoolean(child_validation)) {
                is_valid = is_valid && child_validation;
            }
        }


        if (!is_valid) {
            submitDOM.attr('disabled','disabled');
        }
        else {
            submitDOM.removeAttr("disabled");
        }

        if (isLastChild()) {
            nextDOM.hide();
            reviewDOM.show();
        }

    }

    initXBlockView();
}
