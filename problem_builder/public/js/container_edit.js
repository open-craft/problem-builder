function ProblemBuilderContainerEdit(runtime, element) {
    "use strict";

    // Standard initialization for any Problem Builder / Step Builder container XBlocks
    // that are instances of StudioContainerXBlockWithNestedXBlocksMixin

    StudioContainerXBlockWithNestedXBlocksMixin(runtime, element);

    if (window.ProblemBuilderUtil) {
        ProblemBuilderUtil.transformClarifications(element);
    }
}
