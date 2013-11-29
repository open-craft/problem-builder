function MentoringBlock(runtime, element) {
    var progressTemplate = _.template($('#xblock-progress-template').html());

    function renderProgress() {
        var data = $('.progress', element).data();
        $('.indicator', element).html(progressTemplate(data));
    }

    function callIfExists(obj, fn) {
        if (typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return undefined;
        }
    }

    function handleSubmitResults(results) {
        $('.messages', element).empty();

        $.each(results.submitResults || [], function(index, submitResult) {
            var input = submitResult[0],
                result = submitResult[1];
            callIfExists(runtime.childMap(element, input), 'handleSubmit', result);
        });

        $('.progress', element).data('completed', results.completed ? 'True' : 'False')
        renderProgress();

        // Messages should only be displayed upon hitting 'submit', not on page reload
        $('.messages', element).append(results.message);
    }

    $(element).find('.submit').bind('click', function() {
        var data = {};
        var children = runtime.children(element);
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
