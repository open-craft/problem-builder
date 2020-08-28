function MentoringWithStepsBlock(runtime, element) {

    // Use problem_builder translations
    var gettext = window.ProblemBuilderXBlockI18N.gettext;
    var ngettext = window.ProblemBuilderXBlockI18N.ngettext;

    var children = runtime.children(element);

    var steps = [];

    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var blockType = $(child.element).data('block-type');
        if (blockType === 'sb-step') {
            steps.push(child);
        }
    }

    var activeStepIndex = $('.mentoring', element).data('active-step');
    var message = $('.sb-step-message', element);
    var checkmark, submitDOM, nextDOM, reviewButtonDOM, tryAgainDOM,
        gradeDOM, attemptsDOM, reviewLinkDOM, submitXHR;
    var reviewStepDOM = $("div.xblock[data-block-type=sb-review-step], div.xblock-v1[data-block-type=sb-review-step]", element);
    var reviewStepAnchor = $("<span>").addClass("review-anchor").insertBefore(reviewStepDOM);
    var hasAReviewStep = reviewStepDOM.length == 1;

    /**
     * Returns the active step
     * @returns MentoringStepBlock
     */
    function getActiveStep() {
        return  steps[activeStepIndex];
    }

    /**
     * Calls a function for each registered step. The object passed to this function is a MentoringStepBlock.
     *
     * @param func single arg function.
     */
    function forEachStep(func) {
        for (var idx=0; idx < steps.length; idx++) {
            func(steps[idx]);
        }
    }

    /**
     * Displays the active step
     */
    function showActiveStep() {
        var step = getActiveStep();
        step.showStep();
    }

    /**
     * Hides all steps
     */
    function hideAllSteps() {
        forEachStep(function(step) {
            step.hideStep();
        });
    }

    function isLastStep() {
        return (activeStepIndex === steps.length-1);
    }

    function atReviewStep() {
        return (activeStepIndex === -1);
    }

    function someAttemptsLeft() {
        var data = attemptsDOM.data();
        if (data.max_attempts === 0) { // Unlimited number of attempts available
            return true;
        }
        return (data.num_attempts < data.max_attempts);
    }

    function showFeedback(response) {
        checkmark.find('span.sr-only').remove();
        if (response.step_status === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
            checkmark.attr('aria-label', checkmark.data('label_correct'));
            checkmark.append('<span class="sr-only">'+gettext("Correct")+'</span>')
        } else if (response.step_status === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
            checkmark.attr('aria-label', checkmark.data('label_partial'));
            checkmark.append('<span class="sr-only">'+gettext("Partially correct")+'</span>')
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
            checkmark.attr('aria-label', checkmark.data('label_incorrect'));
            checkmark.append('<span class="sr-only">'+gettext("Incorrect")+'</span>');
        }
        var step = getActiveStep();
        if (typeof step.showFeedback == 'function') {
            step.showFeedback(response);
        }
    }

    function updateControls() {
        submitDOM.attr('disabled', 'disabled');

        nextDOM.removeAttr("disabled");
        if (nextDOM.is(':visible')) { nextDOM.focus(); }

        if (atReviewStep()) {
            if (hasAReviewStep) {
                reviewButtonDOM.removeAttr('disabled');
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
        submitDOM.attr('disabled', 'disabled'); // Disable the button until the results load.
        var submitUrl = runtime.handlerUrl(element, 'submit');
        var activeStep = getActiveStep();
        var hasQuestion = activeStep.hasQuestion();
        var data = activeStep.getSubmitData();
        data["active_step"] = activeStepIndex;
        $.post(submitUrl, JSON.stringify(data)).success(function(response) {
            showFeedback(response);
            activeStepIndex = response.active_step;
            if (activeStepIndex === -1) {
                // We are now showing the review step / end
                // Update the number of attempts.
                attemptsDOM.data('num_attempts', response.num_attempts);
                reviewStepDOM.html($(response.review_html).html());
                updateControls();
            } else if (!hasQuestion) {
                // This was a step with no questions, so proceed to the next step / review:
                updateDisplay();
            } else {
                // Enable the Next button so users can proceed.
                updateControls();
            }
        });
    }

    function getResults() {
        getActiveStep().getResults(handleReviewResults);
    }

    function handleReviewResults(response) {
        // Show step-level feedback
        showFeedback(response);
        // Forward to active step to show answer level feedback
        var step = getActiveStep();
        var results = response.results;
        var options = {
            checkmark: checkmark
        };
        step.handleReview(results, options);
    }


    function clearSelections() {
        forEachStep(function (step) {
            $('input[type=radio], input[type=checkbox]', step.element).prop('checked', false).change();
        });
    }

    function stopVideos() {
        $(element).find('video').trigger('pause');
    }

    function cleanAll() {
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');
        checkmark.attr('aria-label', '');
        hideAllSteps();
        hideReviewStep();
        attemptsDOM.html('');
        message.hide();
    }

    function updateNextLabel() {
        var step = getActiveStep();
        nextDOM.attr('value', step.getStepLabel());
    }

    function updateDisplay() {
        cleanAll();
        stopVideos();

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

            // Reinstate default event handlers
            nextDOM.off('click');
            nextDOM.on('click', updateDisplay);
            reviewButtonDOM.off('click');
            reviewButtonDOM.on('click', showGrade);

            var step = getActiveStep();
            if (step.hasQuestion()) {  // Step includes one or more questions
                nextDOM.attr('disabled', 'disabled');
                submitDOM.show();
                if (isLastStep()) {  // Step is last step
                    nextDOM.hide();
                    if (hasAReviewStep) {  // Step Builder includes review step
                        reviewButtonDOM.attr('disabled', 'disabled');
                        reviewButtonDOM.show();
                    }
                }
            } else {  // Step does not include any questions
                nextDOM.removeAttr('disabled');
                submitDOM.hide();
                if (isLastStep()) {  // Step is last step
                    // Remove default event handler from button that displays review.
                    // This is necessary to make sure updateDisplay is not called twice
                    // when user clicks this button next;
                    // "submit" already does the right thing with respect to updating the display,
                    // and calling updateDisplay twice causes issues with scrolling behavior:
                    reviewButtonDOM.off();
                    reviewButtonDOM.one('click', submit);
                    reviewButtonDOM.removeAttr('disabled');
                    nextDOM.hide();
                    if (hasAReviewStep) {  // Step Builder includes review step
                        reviewButtonDOM.show();
                    }
                } else {  // Step is not last step
                    // Remove default event handler from button that displays next step.
                    // This is necessary to make sure updateDisplay is not called twice
                    // when user clicks this button next;
                    // "submit" already does the right thing with respect to updating the display,
                    // and calling updateDisplay twice causes issues with scrolling behavior:
                    nextDOM.off();
                    nextDOM.one('click', submit);
                }
            }
        }

        // Scroll to top of this block
        scrollIntoView();
    }

    function showReviewStep() {
        if (someAttemptsLeft()) {
            tryAgainDOM.removeAttr('disabled');
        }

        submitDOM.hide();
        nextDOM.hide();
        reviewButtonDOM.hide();
        tryAgainDOM.show();

        // reviewStepDOM is detached in hideReviewStep
        reviewStepDOM.insertBefore(reviewStepAnchor);
        reviewStepDOM.show();
    }

    /**
     * We detach review step from DOM, this is required to handle HTML
     * blocks with embedded videos, that can be added to that step.
     *
     * NOTE: Review steps are handled differently than "normal" steps:
     * the HTML contents of a review step are replaced with fresh
     * contents in submit function.
     */
    function hideReviewStep() {
        reviewStepDOM.hide();
        reviewStepDOM.detach();
    }

    function getStepToReview(event) {
        event.preventDefault();
        var stepIndex = parseInt($(event.target).data('step')) - 1;
        jumpToReview(stepIndex);
    }

    function jumpToReview(stepIndex) {
        activeStepIndex = stepIndex;
        cleanAll();
        clearSelections();
        showActiveStep();
        updateNextLabel();

        if (isLastStep()) {
            reviewButtonDOM.show();
            reviewButtonDOM.removeAttr('disabled');
            nextDOM.hide();
            nextDOM.attr('disabled', 'disabled');
        } else {
            nextDOM.show();
            nextDOM.removeAttr('disabled');
        }
        var step = getActiveStep();

        tryAgainDOM.hide();
        if (step.hasQuestion()) {
            submitDOM.show();
        } else {
            submitDOM.hide();
        }
        submitDOM.attr('disabled', 'disabled');
        reviewLinkDOM.show();

        getResults();

        // Scroll to top of this block
        scrollIntoView();
    }

    function showAttempts() {
        var data = attemptsDOM.data();
        if (_.isNumber(data.max_attempts) && data.max_attempts > 0) {
           var message = _.template(
              ngettext("You have used {num_used} of 1 submission.", "You have used {num_used} of {max_attempts} submissions.", data.max_attempts),
              {num_used: _.min([data.num_attempts, data.max_attempts]), max_attempts: data.max_attempts}, {interpolate: /\{(.+?)\}/g}
            );
           attemptsDOM.html("<span>" + message + "</span>");
        } // Don't show attempts if unlimited attempts available (max_attempts === 0)
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
        var step = getActiveStep();
        if (step) {
            isValid = step.validate();
        }
        if (!isValid) {
            submitDOM.attr('disabled', 'disabled');
        } else {
            submitDOM.removeAttr('disabled');
        }
    }

    function initSteps(options) {
        forEachStep(function (step) {
            options.mentoring = {
                setContent: setContent,
                publish_event: publishEvent,
                is_step_builder: true
            };
            step.initChildren(options);
        });
    }

    function setContent(dom, content) {
        dom.html('');
        dom.append(content);
    }

    function publishEvent(data) {
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'publish_event'),
            data: JSON.stringify(data)
        });
    }

    function buildInteractionData() {
        var attemptsData = attemptsDOM.data();

        return {
            "attempts_count": attemptsData.num_attempts,
            "attempts_max": attemptsData.max_attempts || "unlimited",
            "score": reviewStepDOM.find(".grade-result").data('score')
        }
    }

    function notifyInteraction() {
        // Tell XBlock runtime that an interaction with this XBlock happened, submitting
        // current and max attempts and current score. Runtime is free to react to this event as necessary.
        // This event is not used in this XBlock, but removing it might break some integrations with third party
        // software
        var interactionData = buildInteractionData();
        notify("xblock.interaction", interactionData);

        var xblockBackendEventData = $.extend({}, interactionData, {event_type: 'xblock.interaction'});
        publishEvent(xblockBackendEventData);
    }

    function showGrade() {
        // Tell supporting runtimes to enable navigation between units;
        // user is currently not in the middle of an attempt
        // so it makes sense for them to be able to leave the current unit by clicking arrow buttons
        notify('navigation', {state: 'unlock'});
        notifyInteraction();

        cleanAll();
        stopVideos();
        showReviewStep();
        showAttempts();

        // Disable "Try again" button if no attempts left
        if (!someAttemptsLeft()) {
            tryAgainDOM.attr("disabled", "disabled");
        }

        nextDOM.off();
        nextDOM.on('click', reviewNextStep);
        reviewLinkDOM.hide();

        // Scroll to top of this block
        scrollIntoView();
    }

    function reviewNextStep() {
        jumpToReview(activeStepIndex+1);
        stopVideos();
    }

    function handleTryAgain(result) {
        // Tell supporting runtimes to disable navigation between units;
        // this keeps users from accidentally clicking arrow buttons
        // and interrupting their experience with the current unit
        notify('navigation', {state: 'lock'});

        activeStepIndex = result.active_step;
        clearSelections();
        updateDisplay();
        tryAgainDOM.hide();
        submitDOM.show();
        if (! isLastStep()) {
            nextDOM.off();
            nextDOM.on('click', updateDisplay);
            nextDOM.show();
            reviewButtonDOM.hide();
        }
    }

    function tryAgain() {
        var handlerUrl = runtime.handlerUrl(element, 'try_again');
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify({})).success(handleTryAgain);
    }

    function notify(name, data) {
        // Notification interface does not exist in the workbench.
        if (runtime.notify) {
            runtime.notify(name, data);
        }
    }

    function scrollIntoView() {
        // This function can be called multiple times per step initialization.
        // We must make sure that only one animation is queued or running at any given time,
        // that's why we use a special animation queue and make sure to .stop() any running/queued
        // animations before enqueueing a new one.
        var rootBlock = $(element),
            rootBlockOffset = rootBlock.offset().top,
            queue = 'sb-scroll',
            props = {scrollTop: rootBlockOffset},
            opts = {duration: 500, queue: queue};
        $('html, body').stop(queue, true).animate(props, opts).dequeue(queue);
    }

    function initClickHandlers() {
        $(document).on("click", function(event, ui) {
            var target = $(event.target);
            var itemFeedbackParentSelector = '.choice';
            var itemFeedbackSelector = ".choice .choice-tips";

            function clickedInside(selector, parent_selector) {
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
        checkmark = $('.step-overall-checkmark', element);

        submitDOM = $(element).find('.submit .input-main');
        submitDOM.on('click', submit);

        nextDOM = $(element).find('.submit .input-next');
        if (atReviewStep()) {
            nextDOM.on('click', reviewNextStep);
        } else {
            nextDOM.on('click', updateDisplay);
        }

        reviewButtonDOM = $(element).find('.submit .input-review');
        reviewButtonDOM.off('click');
        reviewButtonDOM.on('click', showGrade);

        tryAgainDOM = $(element).find('.submit .input-try-again');
        tryAgainDOM.on('click', tryAgain);

        gradeDOM = $('.grade', element);
        attemptsDOM = $('.attempts', element);

        reviewLinkDOM = $(element).find('.review-link');
        reviewLinkDOM.off('click');
        reviewLinkDOM.on('click', showGrade);

        // Add click handler that takes care of links to steps on the extended review:
        $(element).on('click', 'a.step-link', getStepToReview);

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
