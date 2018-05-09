function MentoringBlock(runtime, element) {
    // Set up gettext in case it isn't available in the client runtime:
    if (typeof gettext == "undefined") {
        window.gettext = function gettext_stub(string) { return string; };
        window.ngettext = function ngettext_stub(strA, strB, n) { return n == 1 ? strA : strB; };
    }

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
        step: step,
        publish_event: publish_event,
        data: data
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
                publish_event({event_type: 'xblock.problem_builder.feedback.closed', content: $(el).text()});
            });
        }

        if (!clickedInside(item_feedback_selector, item_feedback_parent_selector)) {
            $(item_feedback_selector).not(':hidden').hide();
            $('.choice-tips-container').removeClass('with-tips');
        }
    });

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return null;
        }
    }

    function setContent(dom, content) {
        dom.html('');
        dom.append(content);
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
        for (var i=0; i < children.length; i++) {
            var child = children[i];
            callIfExists(child, 'init', options);
        }
    }

    function getChildByName(name) {
        for (var i = 0; i < children.length; i++) {
            var child = children[i];
            if (child && typeof child.name !== 'undefined' && child.name.toString() === name) {
                return child;
            }
        }
    }

    ProblemBuilderUtil.transformClarifications(element);

    MentoringStandardView(runtime, element, mentoring);

    publish_event({event_type:"xblock.problem_builder.loaded"});
}
