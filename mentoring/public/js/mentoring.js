function MentoringBlock(runtime, element) {
    var attemptsTemplate = _.template($('#xblock-attempts-template').html());
    var children; // Keep track of children. A Child need a single object scope for its data.
    var submitXHR;

    function renderAttempts() {
        var data = $('.attempts', element).data();
        $('.attempts', element).html(attemptsTemplate(data));
    }

    function renderDependency() {
        var warning_dom = $('.missing-dependency', element),
            data = warning_dom.data();

        if (data.missing === 'True') {
            warning_dom.show();
        }
    }

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return undefined;
        }
    }

    function handleSubmitResults(results) {
        messagesDOM.empty().hide();

        $.each(results.submitResults || [], function(index, submitResult) {
            var input = submitResult[0],
                result = submitResult[1],
                child = getChildByName(element, input);
            var options = {
                max_attempts: results.max_attempts,
                num_attempts: results.num_attempts
            }
            callIfExists(child, 'handleSubmit', result, options);
        });

        $('.attempts', element).data('max_attempts', results.max_attempts);
        $('.attempts', element).data('num_attempts', results.num_attempts);
        renderAttempts();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        messagesDOM.append(results.message);
        if (messagesDOM.html().trim()) {
            messagesDOM.prepend('<div class="title1">Feedback</div>');
            messagesDOM.show();
        }

        submitDOM.attr('disabled', 'disabled');
    }

    function getChildren(element) {
        if (!_.isUndefined(children))
            return children;

        var children_dom = $('.xblock-light-child', element);
        children = [];

        $.each(children_dom, function(index, child_dom) {
            var child_type = $(child_dom).attr('data-type'),
                child = window[child_type];
            if (typeof child !== 'undefined') {
                child = child(runtime, child_dom);
                child.name = $(child_dom).attr('name');
                children.push(child);
            }
        });
        return children;
    }

    function getChildByName(element, name) {
        var children = getChildren(element);

        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child.name === name) {
                return child;
            }
        }
    }

    function submit() {
        var success = true;
        var data = {};
        var children = getChildren(element);
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child.name !== undefined) {
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

        var children = getChildren(element);
        for (var i = 0; i < children.length; i++) {
            callIfExists(children[i], 'clearResult');
        }
    }

    function onChange() {
        clearResults();
        validateXBlock();
    }

    function initXBlock() {
        messagesDOM = $(element).find('.messages');
        submitDOM = $(element).find('.submit .input-main');
        submitDOM.bind('click', submit);

        // init children (especially mrq blocks)
        var children = getChildren(element);
        var options = {
            onChange: onChange
        };
        _.each(children, function(child) {
            callIfExists(child, 'init', options);
        });


        renderAttempts();
        renderDependency();

        validateXBlock();
    }

    function handleRefreshResults(results) {
        $(element).html(results.html);
        initXBlock();
    }

    function refreshXBlock() {
        var handlerUrl = runtime.handlerUrl(element, 'view');
        $.post(handlerUrl, '{}').success(handleRefreshResults);
    }

    // validate all children
    function validateXBlock() {
        var is_valid = true;
        var data = $('.attempts', element).data();
        var children = getChildren(element);

        if ((data.max_attempts > 0) && (data.num_attempts >= data.max_attempts)) {
            is_valid = false;
        }
        else {
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child.name !== undefined) {
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
