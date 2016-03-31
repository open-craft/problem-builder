function MentoringWithStepsBlock(runtime, element) {

    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }

    var children = runtime.children(element);

    var steps = [];

    for (var i = 0; i < children.length; i++) {
        var child = children[i];
        var blockType = $(child.element).data('block-type');
        if (blockType === 'sb-step') {
            registerStep(child);
        }
    }

    var activeStepIndex = $('.mentoring', element).data('active-step');
    var attemptsTemplate = _.template($('#xblock-attempts-template').html());
    var message = $('.sb-step-message', element);
    var checkmark, submitDOM, nextDOM, reviewButtonDOM, tryAgainDOM,
        gradeDOM, attemptsDOM, reviewLinkDOM, submitXHR;
    var reviewStepDOM = $("div.xblock[data-block-type=sb-review-step], div.xblock-v1[data-block-type=sb-review-step]", element);
    var hasAReviewStep = reviewStepDOM.length == 1;
    
    /**
     * Registers step with this StepBuilder instance: Creates and stores a wrapper that contains the XBlock instance
     * and associated DOM element, as well as some additional metadata used to safely
     * remove and re-attach xblock to the DOM. See showStep and hideStep to see why we need to do it.
     * @param step xblock instance to register
     */
    function registerStep(step) {
        var $element = $(step.element);
        var $anchor = $('<span class="xblock-sb-anchor"/>');
        $anchor.insertBefore($element);
        var step_wrapper = {
            $element: $element,
            xblock: step,
            $anchor: $anchor
        };
        steps.push(step_wrapper);
    }

    /**
     * Returns wrapper for the active step
     * @returns {*}, an object containing the XBlock instance and associated DOM element for the active step, as well
     * as additional metadata (see registerStep where this object is created for properties)
     */
    function getWrapperForActiveStep() {
        return steps[activeStepIndex];
    }

    /**
     * Returns the active step
     * @returns {*}
     */
    function getActiveStep() {
        return getWrapperForActiveStep().xblock;
    }

    /**
     * Calls a function for each registered step. The object passed to this function is a step wrapper object
     * (see registerStep where this object is created for a list of properties)
     *
     * @param func single arg function.
     */
    function forEachStep(func){
        for (var idx=0; idx < steps.length; idx++) {
            func(steps[idx]);
        }
    }

    /**
     * Displays a step
     * @param step_wrapper 
     */
    function showStep(step_wrapper) {
        step_wrapper.$element.insertAfter(step_wrapper.$anchor);
        step_wrapper.$element.show();
        step_wrapper.xblock.updateChildren();
    }

    /**
     * Hides a step
     * @param step_wrapper
     */
    function hideStep(step_wrapper) {
        step_wrapper.$element.detach();
    }

    /**
     * Displays the active step
     */
    function showActiveStep() {
        var step = getWrapperForActiveStep();
        showStep(step);
    }

    /**
     * Hides all steps
     */
    function hideAllSteps() {
        forEachStep(function(step){
            hideStep(step);
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
        if (response.step_status === 'correct') {
            checkmark.addClass('checkmark-correct icon-ok fa-check');
        } else if (response.step_status === 'partial') {
            checkmark.addClass('checkmark-partially-correct icon-ok fa-check');
        } else {
            checkmark.addClass('checkmark-incorrect icon-exclamation fa-exclamation');
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
        forEachStep(function (step_wrapper) {
            $('input[type=radio], input[type=checkbox]', step_wrapper.$element).prop('checked', false);
        });
    }

    function cleanAll() {
        checkmark.removeClass('checkmark-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-partially-correct icon-ok fa-check');
        checkmark.removeClass('checkmark-incorrect icon-exclamation fa-exclamation');
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

        reviewStepDOM.show();
    }

    function hideReviewStep() {
        reviewStepDOM.hide();
    }

    function getStepToReview(event) {
        event.preventDefault();
        var stepIndex = parseInt($(event.target).data('step')) - 1;
        jumpToReview(stepIndex);
    }

    function jumpToReview(stepIndex) {
        activeStepIndex = stepIndex;
        cleanAll();
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
        if (data.max_attempts > 0) {
            attemptsDOM.html(attemptsTemplate(data));
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
                publish_event: publishEvent
            };
            step.xblock.initChildren(options);
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

        // Scroll to top of this block
        scrollIntoView();
    }

    function reviewNextStep() {
        jumpToReview(activeStepIndex+1);
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

    function notify(name, data){
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
        reviewButtonDOM.on('click', showGrade);

        tryAgainDOM = $(element).find('.submit .input-try-again');
        tryAgainDOM.on('click', tryAgain);

        gradeDOM = $('.grade', element);
        attemptsDOM = $('.attempts', element);

        reviewLinkDOM = $(element).find('.review-link');
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
