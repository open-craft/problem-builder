function ReviewStepBlock(runtime, element) {

    var gradeTemplate = _.template($('#xblock-feedback-template').html());
    var reviewStepsTemplate = _.template($('#xblock-step-links-template').html());

    return {

        'renderGrade': function(gradeDOM, showExtendedFeedback) {

            var data = gradeDOM.data();

            _.extend(data, {
                'runDetails': function(correctness) {
                    if (!showExtendedFeedback) {
                        return '';
                    }
                    var self = this;
                    return reviewStepsTemplate({'questions': self[correctness], 'correctness': correctness});
                }
            });

            gradeDOM.html(gradeTemplate(data));

        }

    };

}
