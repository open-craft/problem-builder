function MentoringWithStepsBlock(runtime, element) {

    var steps = runtime.children(element).filter(
        function(c) { return c.element.className.indexOf('sb-step') > -1; }
    );
    var activeStep = $('.mentoring', element).data('active-step');
    var gradeTemplate = _.template($('#xblock-review-template').html());
    var reviewStepsTemplate = _.template($('#xblock-review-steps-template').html());
    var reviewTipsTemplate = _.template($('#xblock-review-tips-template').html()); // Tips about specific questions the user got wrong
    var attemptsTemplate = _.template($('#xblock-attempts-template').html());
    var reviewStep, checkmark, submitDOM, nextDOM, reviewDOM, tryAgainDOM,
        assessmentMessageDOM, gradeDOM, attemptsDOM, reviewTipsDOM, reviewLinkDOM, submitXHR;

    function isLastStep() {
        return (activeStep === steps.length-1);
    }

    function atReviewStep() {
        return (activeStep === -1);
    }

    function reviewStepPresent() {
        return reviewStep.length > 0;
    }

    function someAttemptsLeft() {
        var data = attemptsDOM.data();
        if (data.max_attempts === 0) { // Unlimited number of attempts available
            return true;
        }
        return (data.num_attempts < data.max_attempts);
    }

    function updateActiveStep(newValue) {
        var handlerUrl = runtime.handlerUrl(element, 'update_active_step');
        $.post(handlerUrl, JSON.stringify(newValue))
            .success(function(response) {
                activeStep = response.active_step;
            });
    }

    function updateNumAttempts() {
        var handlerUrl = runtime.handlerUrl(element, 'update_num_attempts');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                attemptsDOM.data('num_attempts', response.num_attempts);
            });
    }

    function updateGrade() {
        var handlerUrl = runtime.handlerUrl(element, 'get_score');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                gradeDOM.data('score', response.score);
                gradeDOM.data('correct_answer', response.correct_answers);
                gradeDOM.data('incorrect_answer', response.incorrect_answers);
                gradeDOM.data('partially_correct_answer', response.partially_correct_answers);
            });
    }

    function updateReviewTips() {
        var handlerUrl = runtime.handlerUrl(element, 'get_review_tips');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                gradeDOM.data('assessment_review_tips', response.review_tips);
            });
    }

    function handleResults(response) {
        // Update active step so next step is shown on page reload (even if user does not click "Next Step")
        updateActiveStep(activeStep+1);

        // If step submitted was last step of this mentoring block, update grade and number of attempts used
        if (response.attempt_complete) {
            updateNumAttempts();
            updateGrade();
            updateReviewTips();
        }

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

        if (isLastStep()) {
            if (reviewStepPresent()) {
                reviewDOM.removeAttr('disabled');
            } else {
                if (someAttemptsLeft()) {
                    tryAgainDOM.removeAttr('disabled');
                    tryAgainDOM.show();
                } else {
                    showAttempts();
                }
            }
        }
    }

    function submit() {
        // We do not handle submissions at this level, so just forward to "submit" method of active step
        var step = steps[activeStep];
        step.submit(handleResults);
    }

    function getResults() {
        var step = steps[activeStep];
        step.getResults(handleReviewResults);
    }

    function handleReviewResults(response) {
        // Show step-level feedback
        if (response.completed === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
        } else if (response.completed === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
        }
        // Forward to active step to show answer level feedback
        var step = steps[activeStep];
        var results = response.results;
        var options = {
            checkmark: checkmark
        };
        step.handleReview(results, options);
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
        assessmentMessageDOM.html('');
        gradeDOM.html('');
        attemptsDOM.html('');
        reviewTipsDOM.empty().hide();
    }

    function updateDisplay() {
        cleanAll();
        if (atReviewStep()) {
            showAssessmentMessage();
            showReviewStep();
            showAttempts();
        } else {
            showActiveStep();
            validateXBlock();
            nextDOM.attr('disabled', 'disabled');
            if (isLastStep() && reviewStepPresent()) {
                reviewDOM.attr('disabled', 'disabled');
                reviewDOM.show();
            }
        }
    }

    function showAssessmentMessage() {
        var data = gradeDOM.data();
        assessmentMessageDOM.html(data.assessment_message);
    }

    function showReviewStep() {
        reviewStep.show();

        var data = gradeDOM.data();

        // Links for reviewing individual questions (WIP)
        var enableExtendedFeedback = (!someAttemptsLeft() && data.extended_feedback);

        _.extend(data, {
            'runDetails': function(correctness) {
                if (!enableExtendedFeedback) {
                    return '';
                }
                var self = this;
                return reviewStepsTemplate({'questions': self[correctness], 'correctness': correctness});
            }
        });
        gradeDOM.html(gradeTemplate(data));
        $('a.step-link', element).on('click', getStepToReview);

        // Review tips
        if (someAttemptsLeft()) {
            if (data.assessment_review_tips.length > 0) {
                // on-assessment-review-question messages specific to questions the student got wrong:
                reviewTipsDOM.html(reviewTipsTemplate({
                    tips: data.assessment_review_tips
                }));
                reviewTipsDOM.show();
            }
        }

        submitDOM.hide();
        nextDOM.hide();
        reviewDOM.hide();
        tryAgainDOM.removeAttr('disabled');
        tryAgainDOM.show();
    }

    function getStepToReview(event) {
        event.preventDefault();
        var stepIndex = parseInt($(event.target).data('step')) - 1;
        jumpToReview(stepIndex);
    }

    function jumpToReview(stepIndex) {
        activeStep = stepIndex;
        cleanAll();
        reviewStep.hide();
        showActiveStep();

        if (isLastStep()) {
            reviewDOM.show();
            reviewDOM.removeAttr('disabled');
            nextDOM.hide();
            nextDOM.attr('disabled', 'disabled');
        } else {
            nextDOM.show();
            nextDOM.removeAttr('disabled');
        }

        // ...
        tryAgainDOM.hide();
        submitDOM.show();
        submitDOM.attr('disabled', 'disabled');
        reviewLinkDOM.show();
        // ...

        getResults();
    }

    function showAttempts() {
        var data = attemptsDOM.data();
        if (data.max_attempts > 0) {
            attemptsDOM.html(attemptsTemplate(data));
        } // Don't show attempts if unlimited attempts available (max_attempts === 0)
    }

    function showActiveStep() {
        var step = steps[activeStep];
        $(step.element).show();
    }

    function onChange() {
        // We do not allow users to modify answers belonging to a step after submitting them:
        // Once an answer has been submitted ("Next Step" button is enabled),
        // start ignoring changes to the answer.
        if (nextDOM.attr('disabled')) {
            validateXBlock();
        }
    }

    function validateXBlock() {
        var isValid = true;
        var step = steps[activeStep];
        if (step) {
            isValid = step.validate();
        }
        if (!isValid) {
            submitDOM.attr('disabled', 'disabled');
        } else {
            submitDOM.removeAttr('disabled');
        }
        if (isLastStep()) {
            nextDOM.hide();
        }
    }

    function initSteps(options) {
        for (var i=0; i < steps.length; i++) {
            var step = steps[i];
            var mentoring = {
                setContent: setContent
            };
            options.mentoring = mentoring;
            step.initChildren(options);
        }
    }

    function setContent(dom, content) {
        dom.html('');
        dom.append(content);
        var template = $('#light-child-template', dom).html();
        if (template) {
            dom.append(template);
        }
    }

    function showGrade() {
        cleanAll();
        showAssessmentMessage();
        showReviewStep();
        showAttempts();
        // Disable "Try again" button if no attempts left
        if (!someAttemptsLeft()) {
            tryAgainDOM.attr("disabled", "disabled");
        }
        nextDOM.off();
        nextDOM.on('click', reviewNextStep);
        reviewLinkDOM.hide();
    }

    function reviewNextStep() {
        jumpToReview(activeStep+1);
    }

    function handleTryAgain(result) {
        activeStep = result.active_step;
        updateDisplay();
        reviewStep.hide();
        tryAgainDOM.hide();
        submitDOM.show();
        if (! isLastStep()) {
            nextDOM.off();
            nextDOM.on('click', updateDisplay);
            nextDOM.show();
            reviewDOM.hide();
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
        reviewStep = $('.sb-review-step', element);
        reviewStep.hide();

        checkmark = $('.assessment-checkmark', element);

        submitDOM = $(element).find('.submit .input-main');
        submitDOM.on('click', submit);
        submitDOM.show();

        nextDOM = $(element).find('.submit .input-next');
        if (atReviewStep()) {
            nextDOM.on('click', reviewNextStep);
        } else {
            nextDOM.on('click', updateDisplay);
        }
        nextDOM.show();

        reviewDOM = $(element).find('.submit .input-review');
        reviewDOM.on('click', showGrade);

        tryAgainDOM = $(element).find('.submit .input-try-again');
        tryAgainDOM.on('click', tryAgain);

        assessmentMessageDOM = $('.assessment-message', element);
        gradeDOM = $('.grade', element);
        attemptsDOM = $('.attempts', element);
        reviewTipsDOM = $('.assessment-review-tips', element);

        reviewLinkDOM = $(element).find('.review-link');
        reviewLinkDOM.on('click', showGrade);

        var options = {
            onChange: onChange
        };
        initSteps(options);

        updateDisplay();
    }

    initXBlockView();

}
