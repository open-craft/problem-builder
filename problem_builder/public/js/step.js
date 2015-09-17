function MentoringStepBlock(runtime, element) {

    var children = runtime.children(element);

    function callIfExists(obj, fn) {
        if (typeof obj !== 'undefined' && typeof obj[fn] == 'function') {
            return obj[fn].apply(obj, Array.prototype.slice.call(arguments, 2));
        } else {
            return null;
        }
    }

    return {

        initChildren: function(options) {
            for (var i=0; i < children.length; i++) {
                var child = children[i];
                callIfExists(child, 'init', options);
            }
        },

        validate: function() {
            var is_valid = true;
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                if (child && child.name !== undefined) {
                    var child_validation = callIfExists(child, 'validate');
                    if (_.isBoolean(child_validation)) {
                        is_valid = is_valid && child_validation;
                    }
                }
            }
            return is_valid;
        }

    };

}
