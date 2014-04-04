function MentoringBlock(runtime, element) {
    var progressTemplate = _.template($('#xblock-progress-template').html());

    function renderProgress() {
        var data = $('.progress', element).data();
        $('.indicator', element).html(progressTemplate(data));
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
        var messages_dom = $('.messages', element);
        messages_dom.empty().hide();

        $.each(results.submitResults || [], function(index, submitResult) {
            var input = submitResult[0],
                result = submitResult[1],
                child = getChildByName(element, input);
            callIfExists(child, 'handleSubmit', result);
        });

        $('.progress', element).data('completed', results.completed ? 'True' : 'False');
        $('.progress', element).data('attempted', results.attempted ? 'True' : 'False');
        renderProgress();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        messages_dom.append(results.message);
        if (messages_dom.html().trim()) {
            messages_dom.prepend('<div class="title1">Feedback</div>');
            messages_dom.show();
        }
    }

    function getChildren(element) {
        var children_dom = $('.xblock-light-child', element),
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

    function initXBlock() {
        var submit_dom = $(element).find('.submit .input-main');

        submit_dom.bind('click', function() {
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
            $.post(handlerUrl, JSON.stringify(data)).success(handleSubmitResults);
        });

        // init children (especially mrq blocks)
        var children = getChildren(element);
        var options = {
            blockValidator: validateXBlock
        };
        _.each(children, function(child) {
          callIfExists(child, 'init', options);
        });

        validateXBlock();

        if (submit_dom.length) {
            renderProgress();
        }

        renderDependency();
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
        var submit_dom = $(element).find('.submit .input-main');
        var children_are_valid = true;
        var data = {};
        var children = getChildren(element);

        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child.name !== undefined) {
                var child_validation = callIfExists(child, 'validate');
                if (_.isBoolean(child_validation)) {
                    children_are_valid = children_are_valid && child_validation
                }
            }
        }

        if (!children_are_valid) {
            submit_dom.attr('disabled','disabled');
        }
        else {
            submit_dom.removeAttr("disabled");
        }
    }

    // We need to manually refresh, XBlocks are currently loaded together with the section
    refreshXBlock(element);
}
