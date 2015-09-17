function MentoringWithStepsBlock(runtime, element) {

    var steps = runtime.children(element).filter(
        function(c) { return c.element.className.indexOf('pb-mentoring-step') > -1; }
    );
    var active_child = -1;
    var submitDOM, nextDOM;

    function isLastChild() {
        return (active_child === steps.length-1);
    }

    function hideAllSteps() {
        for (var i=0; i < steps.length; i++) {
            $(steps[i].element).hide();
        }
    }

    function displayNextChild() {
        hideAllSteps();
        findNextChild();
        if (isLastChild()) {
            nextDOM.attr('disabled', 'disabled');
        }
        validateXBlock();
    }

    function findNextChild() {
        // find the next real child block to display. HTMLBlock are always displayed
        ++active_child;
        var child = steps[active_child];
        $(child.element).show();
    }

    function onChange() {
        validateXBlock();
    }

    function validateXBlock() {
        var is_valid = true;
        var child = steps[active_child];
        if (child) {
            is_valid = child['validate']();
        }
        if (!is_valid) {
            submitDOM.attr('disabled', 'disabled');
        } else {
            submitDOM.removeAttr('disabled');
        }
    }

    function initSteps(options) {
        for (var i=0; i < steps.length; i++) {
            var step = steps[i];
            step['initChildren'](options);
        }
    }

    function initXBlockView() {
        submitDOM = $(element).find('.submit .input-main');
        submitDOM.show();

        nextDOM = $(element).find('.submit .input-next');
        nextDOM.bind('click', displayNextChild);
        nextDOM.removeAttr('disabled');
        nextDOM.show();

        var options = {
            onChange: onChange
        };
        initSteps(options);

        displayNextChild();
    }

    initXBlockView();

}
