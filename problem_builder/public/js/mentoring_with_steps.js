function MentoringWithStepsBlock(runtime, element) {

    var steps = runtime.children(element).filter(
        function(c) { return c.element.className.indexOf('pb-mentoring-step') > -1; }
    );
    var active_child = -1;
    var nextDOM;

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
    }

    function findNextChild() {
        // find the next real child block to display. HTMLBlock are always displayed
        ++active_child;
        var child = steps[active_child];
        $(child.element).show();
    }

    function initXBlockView() {

        displayNextChild();

        nextDOM = $(element).find('.submit .input-next');
        nextDOM.bind('click', displayNextChild);
        nextDOM.removeAttr('disabled');
        nextDOM.show();
    }

    initXBlockView();

}
