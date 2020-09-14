(function () {

    /**
     *  Manager for HTML XBlocks. These blocks are hidden by detaching and shown
     *  by re-attaching them to the DOM. This is only way to generically
     *  handle things like video players (they should stop playing when removed from DOM).
     *
     *  @param html an html xblock
     */
    function HtmlManager(html) {
        var $element = $(html.element);
        var $anchor = $("<span>").addClass("sb-video-anchor").insertBefore($element);
        this.show = function () {
            $element.insertAfter($anchor);
        };
        this.hide = function () {
            $element.detach()
        };
    }

    /**
     *
     * Manager for HTML Video child. Videos are re-sized when showing them.
     * @param video an video xblock
     *
     */
    function VideoManager(video) {
        this.show = function () {
            if (typeof video.resizer === 'undefined') {
                // This one is tricky: but it looks like resizer is undefined only if the video is on the
                // step that is initially visible (and then no resizing is necessary)
                return;
            }
            video.resizer.align();
        };
        /**
         * Videos should be paused when user leaves a step containing a video. There is was a proposed implementation
         * but since it didn't work on every system we decided to drop it (it was out of scope for current task
         * nevertheless). See OC-1441 for details.
         */
        this.hide = function () {};
    }

    /**
     * Manager for Plot Xblocks. Handles updating a plot before displaying it.
     * @param plot
     */
    function PlotManager(plot) {
        this.show = function () {
            plot.update();
        };
        this.hide = function () {};
    }


    function ChildManager(xblock_element, runtime) {

        var Managers = {
            'video': VideoManager,
            'sb-plot': PlotManager
        };

        var children = runtime.children(xblock_element);

        /**
         * A list of managers for children that need special care when showing or hiding.
         *
         * @type {show, hide}[]
         */
        var managedChildren = [];

        /***
         * This is a workaround for issue where jquery.xblock.Runtime doesn't return HTML blocks when querying
         * for children.
         *
         * This can be removed when:
         *
         * * We allow inclusion of Ooyala blocks inside StepBuilder and our clients migrate to Ooyala, in this case
         *   we may drop special handling of HTML blocks. See discussions in OC-1441.
         * * We include HTML blocks in runtime.children for runtime of jquery.xblock, then just add
         *   `html: HtmlManager` to `Managers`, and remove this block.
         */
        $("div.xblock.xblock-student_view.xmodule_HtmlModule", xblock_element).each(function(idx, element) {
            managedChildren.push(new HtmlManager({ element: element }));
        });

        for (var idx = 0; idx < children.length; idx++) {
            var child = children[idx];
            // NOTE: While the following assertion is true for e.g Video blocks:
            // child.type == $(child.element).data('block-type') it is invalid for all sb-* blocks
            var type =  $(child.element).data('block-type');
            var constructor = Managers[type];
            if (typeof constructor === 'undefined') {
                // This block does not requires special care, moving on
                continue;
            }
            managedChildren.push(new constructor(child));
        }

        this.show = function () {
            for (var idx = 0; idx < managedChildren.length; idx++) {
                managedChildren[idx].show();
            }
        };

        this.hide = function () {
            for (var idx = 0; idx < managedChildren.length; idx++) {
                managedChildren[idx].hide();
            }
        };

    }

    window.ProblemBuilderStepUtil = {

        ChildManager: ChildManager

    };
})();
