function MentoringStepBlock(runtime, element) {

    var children = runtime.children(element);

    var submitXHR, resultsXHR,
        message = $(element).find('.sb-step-message');
    
    var childManager = new ProblemBuilderStepUtil.ChildManager(element, runtime);

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return null;
        }
    }


    return {

        initChildren: function(options) {
            for (var i=0; i < children.length; i++) {
                var child = children[i];
                callIfExists(child, 'init', options);
            }
        },

        validate: function() {
            var is_valid = true;
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) {
                    var child_validation = callIfExists(child, 'validate');
                    if (_.isBoolean(child_validation)) {
                        is_valid = is_valid && child_validation;
                    }
                }
            }
            return is_valid;
        },

        getSubmitData: function() {
            var data = {};
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) {
                    data[child.name.toString()] = callIfExists(child, "submit");
                }
            }
            return data;
        },

        showFeedback: function(response) {
            // Called when user has just submitted an answer or is reviewing their answer during extended feedback.
            if (message.length) {
                message.fadeIn();
                $(document).click(function() {
                    message.fadeOut();
                });
            }
        },

        getResults: function(resultHandler) {
            var handler_name = 'get_results';
            var data = [];
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) { // Check if we are dealing with a question
                    data[i] = child.name;
                }
            }
            var handlerUrl = runtime.handlerUrl(element, handler_name);
            if (resultsXHR) {
                resultsXHR.abort();
            }
            resultsXHR = $.post(handlerUrl, JSON.stringify(data))
                .success(function(response) {
                    resultHandler(response);
                });
        },

        handleReview: function(results, options) {
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) { // Check if we are dealing with a question
                    var result = results[child.name];
                    // Call handleReview first to ensure that choice-level feedback for MCQs is displayed:
                    // Before displaying feedback for a given choice, handleSubmit checks if it is selected.
                    // (If it isn't, we don't want to display feedback for it.)
                    // handleReview is responsible for setting the "checked" property to true
                    // for each choice that the student selected as part of their most recent submission.
                    // If it is called after handleSubmit, the check mentioned above will fail,
                    // and no feedback will be displayed.
                    callIfExists(child, 'handleReview', result);
                    callIfExists(child, 'handleSubmit', result, options);
                }
            }
        },

        getStepLabel: function() {
            return $('.sb-step', element).data('next-button-label');
        },

        hasQuestion: function() {
            return $('.sb-step', element).data('has-question');
        },

        /**
         * Shows a step, updating all children. 
         */
        showStep: function () {
            $(element).show();
            childManager.show();
        },

        /**
         * Hides a step, updating all children.
         */
        hideStep: function () {
            $(element).hide();
            childManager.hide();
        }
    };

}
