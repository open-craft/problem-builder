window.ProblemBuilderUtil = {

    transformClarifications: function(element) {
        var $element = $(element);

        var transformExisting = function(node) {
            $('.pb-clarification', node).each(function() {
                var item = $(this);
                var content = item.html();
                var clarification = $(
                    '<span class="clarification" tabindex="0" role="note" aria-label="Clarification">' +
                        '<i data-tooltip-show-on-click="true" class="fa fa-info-circle" aria-hidden="true"></i>' +
                        '<span class="sr"></span>' +
                    '</span>'
                );
                clarification.find('i').attr('data-tooltip', content);
                clarification.find('span.sr').html(content);
                item.empty().append(clarification);
            });
        };

        // Transform all span.pb-clarifications already existing inside the element.
        transformExisting($element);

        // Transform all future span.pb-clarifications using mutation observer.
        // It's only needed in the Studio when editing xblock children because the
        // block's JS init function isn't called after edits in the Studio.
        if (window.MutationObserver) {
            var observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    Array.prototype.forEach.call(mutation.addedNodes, function(node) {
                        transformExisting(node);
                    });
                })
            });
            observer.observe($element[0], {childList: true, subtree: true});
        }
    }
};

var gettext;
var ngettext;
if ('ProblemBuilderXBlockI18N' in window) {
    // Use problem builder's local translations
    gettext = window.ProblemBuilderXBlockI18N.gettext;
    ngettext = window.ProblemBuilderXBlockI18N.ngettext;
} else if ('gettext' in window) {
    // Use edxapp's global translations
    gettext = window.gettext;
    ngettext = window.ngettext;
}
if (typeof gettext == "undefined") {
    // No translations -- used by test environment
    gettext = function(string) { return string; };
    ngettext = function(strA, strB, n) { return n == 1 ? strA : strB; };
}
