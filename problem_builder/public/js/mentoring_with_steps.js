function MentoringWithStepsBlock(runtime, element) {

    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }

    var children = runtime.children(element);
    var steps = [];
    var reviewStep;
    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var blockType = $(child.element).data('block-type');
        if (blockType === 'sb-step') {
            steps.push(child);
        } else if (blockType === 'sb-review-step') {
            reviewStep = child;
        }
    }

    var activeStep = $('.mentoring', element).data('active-step');
    var reviewTipsTemplate = _.template($('#xblock-review-tips-template').html()); // Tips about specific questions the user got wrong
    var attemptsTemplate = _.template($('#xblock-attempts-template').html());
    var checkmark, submitDOM, nextDOM, reviewDOM, tryAgainDOM,
        gradeDOM, attemptsDOM, reviewTipsDOM, reviewLinkDOM, submitXHR;

    function isLastStep() {
        return (activeStep === steps.length-1);
    }

    function atReviewStep() {
        return (activeStep === -1);
    }

    function someAttemptsLeft() {
        var data = attemptsDOM.data();
        if (data.max_attempts === 0) { // Unlimited number of attempts available
            return true;
        }
        return (data.num_attempts < data.max_attempts);
    }

    function extendedFeedbackEnabled() {
        var data = gradeDOM.data();
        return data.extended_feedback === "True";
    }

    function showFeedback(response) {
        if (response.step_status === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
        } else if (response.step_status === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
        }
    }

    function postUpdateStep(response) {
        activeStep = response.active_step;
        if (activeStep === -1) {
            updateNumAttempts();
        } else {
            updateControls();
        }
    }

    function handleResults(response) {
        showFeedback(response);

        // Update active step:
        // If we end up at the review step, proceed with updating the number of attempts used.
        // Otherwise, get UI ready for showing next step.
        var handlerUrl = runtime.handlerUrl(element, 'update_active_step');
        $.post(handlerUrl, JSON.stringify(activeStep+1))
            .success(postUpdateStep);
    }

    function updateNumAttempts() {
        var handlerUrl = runtime.handlerUrl(element, 'update_num_attempts');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                attemptsDOM.data('num_attempts', response.num_attempts);
                publishAttempt();
            });
    }

    function publishAttempt() {
        var handlerUrl = runtime.handlerUrl(element, 'publish_attempt');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                // Now that relevant info is up-to-date and attempt has been published, get the latest grade
                updateGrade();
            });
    }

    function updateGrade() {
        var handlerUrl = runtime.handlerUrl(element, 'get_grade');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                gradeDOM.data('score', response.score);
                gradeDOM.data('correct_answer', response.correct_answers);
                gradeDOM.data('incorrect_answer', response.incorrect_answers);
                gradeDOM.data('partially_correct_answer', response.partially_correct_answers);
                gradeDOM.data('correct', response.correct);
                gradeDOM.data('incorrect', response.incorrect);
                gradeDOM.data('partial', response.partial);
                gradeDOM.data('assessment_review_tips', response.assessment_review_tips);
                updateReviewStep(response);
            });
    }

    function updateReviewStep(response) {
        reviewStep.updateAssessmentMessage(response, updateControls);
    }

    function updateControls() {
        submitDOM.attr('disabled', 'disabled');

        nextDOM.removeAttr("disabled");
        if (nextDOM.is(':visible')) { nextDOM.focus(); }

        if (atReviewStep()) {
            if (reviewStep) {
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

    function markRead() {
        var handlerUrl = runtime.handlerUrl(element, 'update_active_step');
        $.post(handlerUrl, JSON.stringify(activeStep+1)).success(function (response) {
            postUpdateStep(response);
            updateDisplay();
        });
    }

    function getResults() {
        var step = steps[activeStep];
        step.getResults(handleReviewResults);
    }

    function handleReviewResults(response) {
        // Show step-level feedback
        showFeedback(response);
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

    function clearSelections() {
        $('input[type=radio], input[type=checkbox]', element).prop('checked', false);
    }

    function cleanAll() {
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');
        hideAllSteps();
        hideReviewStep();
        attemptsDOM.html('');
        reviewTipsDOM.empty().hide();
    }

    function updateNextLabel() {
        var step = steps[activeStep];
        nextDOM.attr('value', step.getStepLabel());
    }

    function updateDisplay() {
        cleanAll();

        if (atReviewStep()) {
            // Tell supporting runtimes to enable navigation between units;
            // user is currently not in the middle of an attempt
            // so it makes sense for them to be able to leave the current unit by clicking arrow buttons
            notify('navigation', {state: 'unlock'});

            showReviewStep();
            showAttempts();
        } else {
            showActiveStep();
            validateXBlock();
            updateNextLabel();
            var step = steps[activeStep];
            if (step.hasQuestion()) {
                nextDOM.attr('disabled', 'disabled');
            } else {
                nextDOM.removeAttr('disabled');
            }
            if (isLastStep() && reviewStep) {
                if (step.hasQuestion()) {
                    reviewDOM.attr('disabled', 'disabled');
                } else {
                    reviewDOM.removeAttr('disabled')
                }
                reviewDOM.show();
            }
        }
    }

    function showReviewStep() {
        // Forward to review step to show assessment message
        reviewStep.showAssessmentMessage();

        // Forward to review step to render grade data
        var showExtendedFeedback = (!someAttemptsLeft() && extendedFeedbackEnabled());
        reviewStep.renderGrade(gradeDOM, showExtendedFeedback);

        // Add click handler that takes care of showing associated step to step links
        $('a.step-link', element).on('click', getStepToReview);

        if (someAttemptsLeft()) {

            tryAgainDOM.removeAttr('disabled');

            // Review tips
            var data = gradeDOM.data();
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
        tryAgainDOM.show();
    }

    function hideReviewStep() {
        reviewStep.hideAssessmentMessage();
        gradeDOM.html('');
    }

    function getStepToReview(event) {
        event.preventDefault();
        var stepIndex = parseInt($(event.target).data('step')) - 1;
        jumpToReview(stepIndex);
    }

    function jumpToReview(stepIndex) {
        activeStep = stepIndex;
        cleanAll();
        showActiveStep();
        updateNextLabel();

        if (isLastStep()) {
            reviewDOM.show();
            reviewDOM.removeAttr('disabled');
            nextDOM.hide();
            nextDOM.attr('disabled', 'disabled');
        } else {
            nextDOM.show();
            nextDOM.removeAttr('disabled');
        }
        var step = steps[activeStep];

        tryAgainDOM.hide();
        if (step.hasQuestion()) {
            submitDOM.show();
        } else {
            submitDOM.hide();
        }
        submitDOM.attr('disabled', 'disabled');
        reviewLinkDOM.show();

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
        step.updatePlots();
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
        if (isLastStep() && step.hasQuestion()) {
            nextDOM.hide();
        } else if (isLastStep()) {
            reviewDOM.one('click', markRead);
            reviewDOM.removeAttr('disabled');
            nextDOM.hide()
        } else if (!step.hasQuestion()) {
            nextDOM.one('click', markRead);
        }
        if (step.hasQuestion()) {
            submitDOM.show();
        } else {
            submitDOM.hide();
        }
    }

    function initSteps(options) {
        for (var i=0; i < steps.length; i++) {
            var step = steps[i];
            var mentoring = {
                setContent: setContent,
                publish_event: publishEvent
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

    function publishEvent(data) {
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'publish_event'),
            data: JSON.stringify(data)
        });
    }

    function showGrade() {
        // Tell supporting runtimes to enable navigation between units;
        // user is currently not in the middle of an attempt
        // so it makes sense for them to be able to leave the current unit by clicking arrow buttons
        notify('navigation', {state: 'unlock'});

        cleanAll();
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
        // Tell supporting runtimes to disable navigation between units;
        // this keeps users from accidentally clicking arrow buttons
        // and interrupting their experience with the current unit
        notify('navigation', {state: 'lock'});

        activeStep = result.active_step;
        clearSelections();
        updateDisplay();
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

    function notify(name, data){
        // Notification interface does not exist in the workbench.
        if (runtime.notify) {
            runtime.notify(name, data);
        }
    }

    function initClickHandlers() {
        $(document).on("click", function(event, ui) {
            var target = $(event.target);
            var itemFeedbackParentSelector = '.choice';
            var itemFeedbackSelector = ".choice .choice-tips";

            function clickedInside(selector, parent_selector){
                return target.is(selector) || target.parents(parent_selector).length>0;
            }

            if (!clickedInside(itemFeedbackSelector, itemFeedbackParentSelector)) {
                $(itemFeedbackSelector).not(':hidden').hide();
                $('.choice-tips-container').removeClass('with-tips');
            }
        });
    }

    function initXBlockView() {
        // Tell supporting runtimes to disable navigation between units;
        // this keeps users from accidentally clicking arrow buttons
        // and interrupting their experience with the current unit
        notify('navigation', {state: 'lock'});

        // Hide steps until we're ready
        hideAllSteps();

        // Initialize references to relevant DOM elements and set up event handlers
        checkmark = $('.assessment-checkmark', element);

        submitDOM = $(element).find('.submit .input-main');
        submitDOM.on('click', submit);

        nextDOM = $(element).find('.submit .input-next');
        if (atReviewStep()) {
            nextDOM.on('click', reviewNextStep);
        } else {
            nextDOM.on('click', updateDisplay);
        }

        reviewDOM = $(element).find('.submit .input-review');
        reviewDOM.on('click', showGrade);

        tryAgainDOM = $(element).find('.submit .input-try-again');
        tryAgainDOM.on('click', tryAgain);

        gradeDOM = $('.grade', element);
        attemptsDOM = $('.attempts', element);
        reviewTipsDOM = $('.assessment-review-tips', element);

        reviewLinkDOM = $(element).find('.review-link');
        reviewLinkDOM.on('click', showGrade);

        // Initialize individual steps
        // (sets up click handlers for questions and makes sure answer data is up-to-date)
        var options = {
            onChange: onChange
        };
        initSteps(options);

        // Refresh info about number of attempts used:
        // In the LMS, the HTML of multiple units can be loaded at once,
        // and the user can flip among them. If that happens, information about
        // number of attempts student has used up may be out of date.
        var handlerUrl = runtime.handlerUrl(element, 'get_num_attempts');
        $.post(handlerUrl, JSON.stringify({}))
            .success(function(response) {
                attemptsDOM.data('num_attempts', response.num_attempts);

                // Finally, show controls and content
                submitDOM.show();
                nextDOM.show();

                updateDisplay();
            });

    }

    initClickHandlers();
    initXBlockView();

}
