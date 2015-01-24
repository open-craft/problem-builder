function MentoringBlock(runtime, element) {
    var attemptsTemplate = _.template($('#xblock-attempts-template').html());
    var data = $('.mentoring', element).data();
    var children = runtime.children(element);
    var step = data.step;

    var mentoring = {
        callIfExists: callIfExists,
        setContent: setContent,
        renderAttempts: renderAttempts,
        renderDependency: renderDependency,
        children: children,
        initChildren: initChildren,
        getChildByName: getChildByName,
        hideAllChildren: hideAllChildren,
        step: step,
        publish_event: publish_event
    };

    function publish_event(data) {
        $.ajax({
            type: "POST",
            url: runtime.handlerUrl(element, 'publish_event'),
            data: JSON.stringify(data)
        });
    }

    $(document).on("click", function(event, ui) {
        var target = $(event.target);
        var question_feedback_selector = ".mentoring .feedback";
        var item_feedback_parent_selector = '.choice';
        var item_feedback_selector = ".choice .choice-tips";

        function clickedInside(selector, parent_selector){
            return target.is(selector) || target.parents(parent_selector).length>0;
        }

        if (!clickedInside(question_feedback_selector, question_feedback_selector)) {
            $(question_feedback_selector).not(':hidden').each(function (i, el) {
                $(el).hide();
                publish_event({event_type: 'xblock.mentoring.feedback.closed', content: $(el).text()});
            });
        }

        if (!clickedInside(item_feedback_selector, item_feedback_parent_selector)) {
            $(item_feedback_selector).not(':hidden').hide();
        }
    });

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return undefined;
        }
    }

    function setContent(dom, content) {
        dom.html('');
        dom.append(content);
        var template = $('#light-child-template', dom).html();
        if (template) {
            dom.append(template);
        }
    }

    function renderAttempts() {
        var data = $('.attempts', element).data();
        $('.attempts', element).html(attemptsTemplate(data));
    }

    function renderDependency() {
        var warning_dom = $('.missing-dependency', element);
        var data = warning_dom.data();

        if (data.missing === 'True') {
            warning_dom.show();
        }
    }

    function initChildren(options) {
        options = options || {};
        options.mentoring = mentoring;
        options.mode = data.mode;
        for (var i=0; i < children.length; i++) {
            var child = children[i];
            callIfExists(child, 'init', options);
        }
    }

    function hideAllChildren() {
        for (var i=0; i < children.length; i++) {
            $(children[i].element).hide();
        }
    }

    function getChildByName(name) {
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child && child.name === name) {
                return child;
            }
        }
    }

    if (data.mode === 'standard') {
        MentoringStandardView(runtime, element, mentoring);
    }
    else if (data.mode === 'assessment') {
        MentoringAssessmentView(runtime, element, mentoring);
    }

    publish_event({event_type:"xblock.mentoring.loaded"});
}
