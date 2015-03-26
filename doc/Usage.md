Mentoring Block Usage
=====================

When you add the `Mentoring` component to a course in the studio, the
built-in editing tools guide you through the process of configuring the
block and adding individual questions.

### Mentoring modes

There are 2 mentoring modes available:

* *standard*: Traditional mentoring. All questions are displayed on the
  page and submitted at the same time. The students get some tips and
  feedback about their answers. This is the default mode.

* *assessment*: Questions are displayed and submitted one by one. The
  students don't get tips or feedback, but only know if their answer was
  correct. Assessment mode comes with a default `max_attempts` of `2`.

Below are some LMS screenshots of a mentoring block in assessment mode.

Question before submitting an answer:

![Assessment Step 1](img/assessment-1.png)

Question after submitting the correct answer:

![Assessment Step 2](img/assessment-2.png)

Question after submitting a wrong answer:

![Assessment Step 3](img/assessment-3.png)

Score review and the "Try Again" button:

![Assessment Step 4](img/assessment-4.png)

### Free-form Question

Free-form questions are represented by a "Long Answer" component. 

Example screenshot before answering the question:

![Answer Initial](img/answer-1.png)

Screenshot after answering the question:

![Answer Complete](img/answer-2.png)

You can add "Long Answer Recap" components to mentoring blocks later on
in the course to provide a read-only view of any answer that the student
entered earlier.

The read-only answer is rendered as a quote in the LMS:

![Answer Read-Only](img/answer-3.png)

### Multiple Choice Questions (MCQ)

Multiple Choice Questions can be added to a mentoring component and
have the following configurable options:

* Question - The question to ask the student
* Message - A feedback message to display to the student after they
  have made their choice.
* Weight - The weight is used when computing total grade/score of
  the mentoring block. The larger the weight, the more influence this
  question will have on the grade. Value of zero means this question
  has no influence on the grade (float, defaults to `1`).
* Correct Choice - Specify which choice[s] is considered correct. If
  a student selects a choice that is not indicated as correct here,
  the student will get the question wrong.

Using the Studio editor, you can add "Custom Choice" blocks to the MCQ.
Each Custom Choice represents one of the options from which students
will choose their answer.

You can also add "Tip" entries. Each "Tip" must be configured to link
it to one or more of the choices. If the student chooses a choice, the


Screenshot: Before attempting to answer the questions:

![MCQ Initial](img/mcq-1.png)

While attempting to complete the questions:

![MCQ Attempting](img/mcq-2.png)

After successfully completing the questions:

![MCQ Success](img/mcq-3.png)

#### Rating MCQ

When constructing questions where the student rates some topic on the
scale from `1` to `5` (e.g. a Likert Scale), you can use the Rating
question type, which includes built-in numbered choices from 1 to 5
The `Low` and `High` settings specify the text shown next to the
lowest and highest valued choice.

Rating questions are a specialized type of MCQ, and the same
instructions apply. You can also still add "Custom Choice" components
if you want additional choices to be available such as "I don't know".


### Self-assessment Multiple Response Questions (MRQ)

Multiple Response Questions are set up similarly to MCQs. The answers
are rendered as checkboxes. Unlike MCQs where only a single answer can
be selected, MRQs allow multiple answers to be selected at the same
time.

MRQ questions have these configurable settings:

* Question - The question to ask the student
* Required Choices - For any choices selected here, if the student
  does *not* select that choice, they will lose marks.
* Ignored Choices - For any choices selected here, the student will
  always be considered correct whether they choose this choice or not.
* Message - A feedback message to display to the student after they
  have made their choice.
* Weight - The weight is used when computing total grade/score of
  the mentoring block. The larger the weight, the more influence this
  question will have on the grade. Value of zero means this question
  has no influence on the grade (float, defaults to `1`).
* Hide Result - If set to True, the feedback icons next to each
  choice will not be displayed (This is false by default).

The "Custom Choice" and "Tip" components work the same way as they
do when used with MCQs (see above).

Screenshot - Before attempting to answer the questions:

![MRQ Initial](img/mrq-1.png)

While attempting to answer the questions:

![MRQ Attempt](img/mrq-2.png)

After clicking on the feedback icon next to the "Its bugs" answer:

![MRQ Attempt](img/mrq-3.png)

After successfully completing the questions:

![MRQ Success](img/mrq-4.png)

### Tables

The mentoring table allows you to present answers to multiple
free-form questions in a concise way. Once you create an "Answer
Recap Table" inside a Mentoring component in Studio, you will be
able to add columns to the table. Each column has an optional
"Header" setting that you can use to add a header to that column.
Each column can contain one or more "Answer Recap" element, as
well as HTML components.

Screenshot:

![Mentoring Table](img/mentoring-table.png)

### Maximum Attempts

You can set the number of maximum attempts for the unit completion by
setting the Max. Attempts option of the Mentoring component.

Before submitting an answer for the first time:

![Max Attempts Before](img/max-attempts-before.png)

After submitting a wrong answer two times:

![Max Attempts Reached](img/max-attempts-reached.png)

### Custom tip popup window size

You can specify With and Height attributes of any Tip component to
customize the popup window size. The value of those attribute should
be valid CSS (e.g. `50px`).

### "Dashboard" Self-Assessment Summary Block

[Instructions for using the "Dashboard" Self-Assessment Summary Block](Dashboard.md)
