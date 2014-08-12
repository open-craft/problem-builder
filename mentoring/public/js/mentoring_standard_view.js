function MentoringStandardView(runtime, element, mentoring) {
    var submitXHR;

    var callIfExists = mentoring.callIfExists;

    function handleSubmitResults(results) {
        messagesDOM.empty().hide();

        $.each(results.submitResults || [], function(index, submitResult) {
            var input = submitResult[0],
                result = submitResult[1],
                child = mentoring.getChildByName(element, input);
            var options = {
                max_attempts: results.max_attempts,
                num_attempts: results.num_attempts
            }
            callIfExists(child, 'handleSubmit', result, options);
        });

        $('.attempts', element).data('max_attempts', results.max_attempts);
        $('.attempts', element).data('num_attempts', results.num_attempts);
        mentoring.renderAttempts();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        mentoring.setContent(messagesDOM, results.message);
        if (messagesDOM.html().trim()) {
            messagesDOM.prepend('<div class="title1">Feedback</div>');
            messagesDOM.show();
        }

        submitDOM.attr('disabled', 'disabled');
    }

    function submit() {
        var success = true;
        var data = {};
        var children = mentoring.children;
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child && child.name !== undefined) {
                data[child.name] = callIfExists(child, 'submit');
            }
        }
        var handlerUrl = runtime.handlerUrl(element, 'submit');
        if (submitXHR) {
            submitXHR.abort();
        }
        submitXHR = $.post(handlerUrl, JSON.stringify(data)).success(handleSubmitResults);
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

        mentoring.displayChildren(options);

        mentoring.renderAttempts();
        mentoring.renderDependency();

        validateXBlock();
    }

    function handleRefreshResults(results) {
        $(element).html(results.html);
        mentoring.readChildren();
        initXBlockView();
    }

    function refreshXBlock() {
        var handlerUrl = runtime.handlerUrl(element, 'view');
        $.post(handlerUrl, '{}').success(handleRefreshResults);
    }

    // validate all children
    function validateXBlock() {
        var is_valid = true;
        var data = $('.attempts', element).data();
        var children = mentoring.children;

        if ((data.max_attempts > 0) && (data.num_attempts >= data.max_attempts)) {
            is_valid = false;
        }
        else {
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
        }
        else {
            submitDOM.removeAttr("disabled");
        }
    }

    // We need to manually refresh, XBlocks are currently loaded together with the section
    refreshXBlock(element);
}
