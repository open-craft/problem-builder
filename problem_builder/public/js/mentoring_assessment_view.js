function MentoringAssessmentView(runtime, element, mentoring) {
    var gradeTemplate = _.template($('#xblock-grade-template').html());
    var reviewQuestionsTemplate = _.template($('#xblock-review-questions-template').html()); // Detailed list of which questions the user got wrong
    var reviewTipsTemplate = _.template($('#xblock-review-tips-template').html()); // Tips about specific questions the user got wrong
    var submitDOM, nextDOM, reviewDOM, tryAgainDOM, assessmentMessageDOM, reviewLinkDOM, reviewTipsDOM;
    var submitXHR;
    var checkmark;
    var active_child;

    var callIfExists = mentoring.callIfExists;

    function cleanAll() {
        // clean checkmark state
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');
        checkmark.removeClass('checkmark-clickable');
        checkmark.attr('aria-label', '');
        checkmark.off('click');

        // Clear all selections
        $('input[type=radio], input[type=checkbox]', element).prop('checked', false);

        // hide all questions
        mentoring.hideAllSteps();

        $('.grade').html('');
        $('.attempts').html('');
        assessmentMessageDOM.html('');
        reviewTipsDOM.empty().hide();
    }

    function no_more_attempts() {
        var attempts_data = $('.attempts', element).data();
        return (attempts_data.max_attempts > 0) && (attempts_data.num_attempts >= attempts_data.max_attempts);
    }

    function renderGrade() {
        notify('navigation', {state: 'unlock'})
        var data = $('.grade', element).data();
        data.enable_extended = (no_more_attempts() && data.extended_feedback);
        _.extend(data, {
            'runDetails': function(label) {
                if (! data.enable_extended) {
                    return ''
                }
                var self = this;
                return reviewQuestionsTemplate({'questions': self[label], 'label': label})
            }
        });
        cleanAll();
        $('.grade', element).html(gradeTemplate(data));
        reviewLinkDOM.hide();
        reviewDOM.hide();
        submitDOM.hide();
        if (data.enable_extended) {
            nextDOM.unbind('click');
            nextDOM.bind('click', reviewNextChild)
        }
        nextDOM.hide();
        tryAgainDOM.show();

        var attempts_data = $('.attempts', element).data();
        if (attempts_data.max_attempts > 0 && attempts_data.num_attempts >= attempts_data.max_attempts) {
            tryAgainDOM.attr("disabled", "disabled");
        } else {
            tryAgainDOM.removeAttr("disabled");
        }

        mentoring.renderAttempts();
        if (data.max_attempts === 0 || data.num_attempts < data.max_attempts) {
            if (data.assessment_message) {
                // Overall on-assessment-review message:
                assessmentMessageDOM.html(data.assessment_message);
            }
            if (data.assessment_review_tips.length > 0) {
                // on-assessment-review-question messages specific to questions the student got wrong:
                reviewTipsDOM.html(reviewTipsTemplate({
                    tips: data.assessment_review_tips
                }));
                reviewTipsDOM.show();
            }
        } else {
            var msg = gettext("Note: you have used all attempts. Continue to the next unit.");
            assessmentMessageDOM.html('').append($('<p></p>').html(msg));
        }
        $('a.question-link', element).click(reviewJump);
    }

    function handleTryAgain(result) {
        if (result.result !== 'success')
            return;

        active_child = -1;
        notify('navigation', {state: 'lock'})
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
        notify('navigation', {state: 'lock'})
        submitDOM = $(element).find('.submit .input-main');
        nextDOM = $(element).find('.submit .input-next');
        reviewDOM = $(element).find('.submit .input-review');
        tryAgainDOM = $(element).find('.submit .input-try-again');
        reviewLinkDOM = $(element).find('.review-link');
        checkmark = $('.assessment-checkmark', element);
        assessmentMessageDOM = $('.assessment-message', element);
        reviewTipsDOM = $('.assessment-review-tips', element);

        submitDOM.show();
        submitDOM.bind('click', submit);
        nextDOM.bind('click', displayNextChild);
        nextDOM.show();
        tryAgainDOM.bind('click', tryAgain);

        active_child = mentoring.step;

        function renderGradeEvent(event) {
            event.preventDefault();
            renderGrade();
        }
        reviewLinkDOM.bind('click', renderGradeEvent);
        reviewDOM.bind('click', renderGradeEvent);

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

    function notify(name, data){
        // Notification interface does not exist in the workbench.
        if (runtime.notify) {
            runtime.notify(name, data)
        }
    }

    function reviewJump(event) {
        // Used only during extended feedback. Assumes completion and attempts exhausted.
        event.preventDefault();

        var target = parseInt($(event.target).data('step')) - 1;
        reviewDisplayChild(target);
    }

    function reviewDisplayChild(child_index) {
        active_child = child_index;
        cleanAll();
        var child = mentoring.steps[active_child];
        $(child.element).show();
        $(child.element).find("input, textarea").first().focus();
        mentoring.publish_event({
            event_type: 'xblock.mentoring.assessment.review',
            exercise_id: $(mentoring.steps[active_child]).attr('name')
        });
        post_display(true);
        get_results();
    }

    function reviewNextChild() {
        nextDOM.attr('disabled', 'disabled');
        nextDOM.hide();
        findNextChild();
        reviewDisplayChild(active_child)
    }

    function displayNextChild() {
        cleanAll();
        findNextChild(true);
        // find the next real child block to display. HTMLBlock are always displayed
        if (isDone()) {
            renderGrade();
        } else {
            post_display();
        }
    }

    function findNextChild(fire_event) {
        // find the next real child block to display. HTMLBlock are always displayed
        ++active_child;
        var child = mentoring.steps[active_child];
        $(child.element).show();
        $(child.element).find("input, textarea").first().focus();
        if (fire_event) {
            mentoring.publish_event({
                event_type: 'xblock.problem_builder.assessment.shown',
                exercise_id: child.name.toString()
            });
        }
    }

    function post_display(show_link) {
        nextDOM.attr('disabled', 'disabled');
        if (no_more_attempts()) {
            if (show_link) {
                reviewLinkDOM.show();
            } else {
                reviewDOM.show();
                reviewDOM.removeAttr('disabled')
            }
        } else {
            reviewDOM.attr('disabled', 'disabled');
        }
        validateXBlock(show_link);
        if (show_link && ! isLastChild()) {
            // User should also be able to browse forward if we're showing the review link.
            nextDOM.show();
            nextDOM.removeAttr('disabled');
        }
        if (show_link) {
            // The user has no more tries, so the try again button is noise. A disabled submit button
            // emphasizes that the user cannot change their answer.
            tryAgainDOM.hide();
            submitDOM.show();
            submitDOM.attr('disabled', 'disabled')
        }
    }

    function onChange() {
        // Assessment mode does not allow to modify answers.
        // Once an answer has been submitted (next button is enabled),
        // start ignoring changes to the answer.
        if (nextDOM.attr('disabled')) {
            validateXBlock();
        }
    }

    function handleResults(response) {
        $('.grade', element).data('score', response.score);
        $('.grade', element).data('correct_answer', response.correct_answer);
        $('.grade', element).data('incorrect_answer', response.incorrect_answer);
        $('.grade', element).data('partially_correct_answer', response.partially_correct_answer);
        $('.grade', element).data('max_attempts', response.max_attempts);
        $('.grade', element).data('num_attempts', response.num_attempts);
        $('.grade', element).data('assessment_message', response.assessment_message);
        $('.attempts', element).data('max_attempts', response.max_attempts);
        $('.attempts', element).data('num_attempts', response.num_attempts);

        if (response.completed === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
            checkmark.attr('aria-label', checkmark.data('label_partial'));
        } else if (response.completed === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
            checkmark.attr('aria-label', checkmark.data('label_correct'));
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
            checkmark.attr('aria-label', checkmark.data('label_incorrect'));
        }

        submitDOM.attr('disabled', 'disabled');

        /* We're not dealing with the current step */
        if (response.step != active_child+1) {
            return
        }
        nextDOM.removeAttr("disabled");
        reviewDOM.removeAttr("disabled");
        if (nextDOM.is(':visible')) { nextDOM.focus(); }
        if (reviewDOM.is(':visible')) { reviewDOM.focus(); }
    }

    function handleReviewResults(response) {
        handleResults(response);
        var options = {
            max_attempts: response.max_attempts,
            num_attempts: response.num_attempts,
            checkmark: checkmark
        };
        var result = response.results[1];
        var child = mentoring.steps[active_child];
        callIfExists(child, 'handleSubmit', result, options);
        callIfExists(child, 'handleReview', result, options);
    }

    function handleSubmitResults(response){
        handleResults(response);
        // Update grade information
        $('.grade').data(response);
    }


    function calculate_results(handler_name, callback) {
        var data = {};
        var child = mentoring.steps[active_child];
        if (child && child.name !== undefined) {
            data[child.name.toString()] = callIfExists(child, handler_name);
        }
        var handlerUrl = runtime.handlerUrl(element, handler_name);
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify(data)).success(callback);
    }

    function submit() {
        calculate_results('submit', handleSubmitResults)
    }

    function get_results() {
        calculate_results('get_results', handleReviewResults)
    }

    function validateXBlock(hide_nav) {
        var is_valid = true;
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

        if (isLastChild() && ! hide_nav) {
            nextDOM.hide();
            reviewDOM.show();
        }

    }

    initXBlockView();
}
