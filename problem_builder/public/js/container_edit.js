function ProblemBuilderContainerEdit(runtime, element) {
    "use strict";

    // Standard initialization for any Problem Builder / Step Builder container XBlocks
    // that are instances of StudioContainerXBlockWithNestedXBlocksMixin

    StudioContainerXBlockWithNestedXBlocksMixin(runtime, element);

    if (window.ProblemBuilderUtil) {
        ProblemBuilderUtil.transformClarifications(element);
    }

    // Add a "mentoring" class to the root XBlock so we can use it as a
    // selector. We cannot just add a div.mentoring wrapper around our children
    // since it breaks jQuery drag-and-drop re-ordering of children.
    $(".wrapper-xblock.level-page > .xblock-render > .xblock").addClass("mentoring");
}
