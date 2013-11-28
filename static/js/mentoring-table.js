function MentoringTableBlock(runtime, element) {
    // Display an exceprt for long answers, with a "more" link to display the full text
    $('.answer-table', element).shorten({
        moreText: 'more',
        lessText: 'less',
        showChars: '500'
    });
}
