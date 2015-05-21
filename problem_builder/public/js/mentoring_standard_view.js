function MentoringStandardView(runtime, element, mentoring) {
    var submitXHR;
    var submitDOM, messagesDOM;

    var callIfExists = mentoring.callIfExists;

    function handleSubmitResults(response, disable_submit) {
        messagesDOM.empty().hide();

        $.each(response.results || [], function(index, result_spec) {
            var input = result_spec[0];
            var result = result_spec[1];
            var child = mentoring.getChildByName(input);
            var options = {
                max_attempts: response.max_attempts,
                num_attempts: response.num_attempts
            };
            callIfExists(child, 'handleSubmit', result, options);
        });

        $('.attempts', element).data('max_attempts', response.max_attempts);
        $('.attempts', element).data('num_attempts', response.num_attempts);
        mentoring.renderAttempts();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        mentoring.setContent(messagesDOM, response.message);
        if (messagesDOM.html().trim()) {
            messagesDOM.prepend('<div class="title1">' + mentoring.data.feedback_label + '</div>');
            messagesDOM.show();
        }

        // this method is called on successful submission and on page load
        // results will be empty only for initial load if no submissions was made
        // in such case we must allow submission to support submitting empty read-only long answer recaps
        if (disable_submit || response.results.length > 0) {
            submitDOM.attr('disabled', 'disabled');
        }
    }

    function handleSubmitError(jqXHR, textStatus, errorThrown, disable_submit) {
        if (textStatus == "error") {
            var errMsg = errorThrown;
            // Check if there's a more specific JSON error message:
            if (jqXHR.responseText) {
                // Is there a more specific error message we can show?
                try {
                    errMsg = JSON.parse(jqXHR.responseText).error;
                } catch (error) { errMsg = jqXHR.responseText.substr(0, 300); }
            }

            mentoring.setContent(messagesDOM, errMsg);
            messagesDOM.show();
        }

        if (disable_submit) {
            submitDOM.attr('disabled', 'disabled');
        }
    }

    function calculate_results(handler_name, disable_submit) {
        var data = {};
        var children = mentoring.children;
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child && child.name !== undefined && typeof(child[handler_name]) !== "undefined") {
                data[child.name.toString()] = child[handler_name]();
            }
        }
        var handlerUrl = runtime.handlerUrl(element, handler_name);
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify(data))
            .success(function(response) { handleSubmitResults(response, disable_submit); })
            .error(function(jqXHR, textStatus, errorThrown) { handleSubmitError(jqXHR, textStatus, errorThrown, disable_submit); });
    }

    function get_results(){
        calculate_results('get_results', false);
    }

    function submit() {
        calculate_results('submit', true);
    }

    function clearResults() {
        messagesDOM.empty().hide();

        var children = mentoring.children;
        for (var i = 0; i < children.length; i++) {
            callIfExists(children[i], 'clearResult');
        }
    }

    function onChange() {
        clearResults();
        validateXBlock();
    }

    function initXBlockView() {
        messagesDOM = $(element).find('.messages');
        submitDOM = $(element).find('.submit .input-main');
        submitDOM.bind('click', submit);
        submitDOM.show();

        var options = {
            onChange: onChange
        };

        mentoring.initChildren(options);
        mentoring.renderDependency();

        get_results();

        var submitPossible = submitDOM.length > 0;
        if (submitPossible) {
            mentoring.renderAttempts();
            validateXBlock();
        } // else display_submit is false and this is read-only
    }

    // validate all children
    function validateXBlock() {
        var is_valid = true;
        var data = $('.attempts', element).data();
        var children = mentoring.children;

        if ((data.max_attempts > 0) && (data.num_attempts >= data.max_attempts)) {
            is_valid = false;
        } else {
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) {
                    var child_validation = callIfExists(child, 'validate');
                    if (_.isBoolean(child_validation)) {
                        is_valid = is_valid && child_validation;
                    }
                }
            }
        }
        if (!is_valid) {
            submitDOM.attr('disabled','disabled');
        } else {
            submitDOM.removeAttr("disabled");
        }
    }

    initXBlockView();
}
