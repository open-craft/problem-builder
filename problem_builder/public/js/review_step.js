function ReviewStepBlock(runtime, element) {

    var gradeTemplate = _.template($('#xblock-feedback-template').html());
    var reviewStepsTemplate = _.template($('#xblock-step-links-template').html());

    var assessmentMessageDOM = $('.assessment-message', element);

    return {

        'showAssessmentMessage': function() {
            var assessmentMessage = assessmentMessageDOM.data('assessment_message');
            assessmentMessageDOM.html(assessmentMessage);
            assessmentMessageDOM.show();
        },

        'hideAssessmentMessage': function() {
            assessmentMessageDOM.html('');
            assessmentMessageDOM.hide();
        },

        'updateAssessmentMessage': function(grade, callback) {
            var handlerUrl = runtime.handlerUrl(element, 'get_assessment_message');
            $.post(handlerUrl, JSON.stringify(grade)).success(function(response) {
                assessmentMessageDOM.data('assessment_message', response.assessment_message);
                callback();
            });
        },

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
