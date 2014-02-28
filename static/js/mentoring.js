function MentoringBlock(runtime, element) {
    var progressTemplate = _.template($('#xblock-progress-template').html());

    function renderProgress() {
        var data = $('.progress', element).data();
        $('.indicator', element).html(progressTemplate(data));
    }

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return undefined;
        }
    }

    function handleSubmitResults(results) {
        $('.messages', element).empty();

        $.each(results.submitResults || [], function(index, submitResult) {
            var input = submitResult[0],
                result = submitResult[1],
                child = getChildByName(element, input);
            callIfExists(child, 'handleSubmit', result);
        });

        $('.progress', element).data('completed', results.completed ? 'True' : 'False')
        renderProgress();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        $('.messages', element).append(results.message);
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

    $(element).find('.submit').bind('click', function() {
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

    renderProgress();
}
