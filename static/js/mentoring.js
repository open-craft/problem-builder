function MentoringBlock(runtime, element) {
    var progress_template = _.template($('#xblock-progress-template').html());

    function render_progress() {
        var data = $('.progress', element).data();
        $('.indicator', element).html(progress_template(data));
    }

    function callIfExists(obj, fn) {
        if (typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return undefined;
        }
    }

    function handleSubmitResults(results) {
        $.each(results.submitResults || {}, function(input, result) {
            callIfExists(runtime.childMap(element, input), 'handleSubmit', result);
        });

        $('.progress', element).data('completed', results.completed ? 'True' : 'False')
        render_progress();
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
        var handlerUrl = runtime.handlerUrl(element, 'submit')
        $.post(handlerUrl, JSON.stringify(data)).success(handleSubmitResults);
    });

    render_progress();
}
