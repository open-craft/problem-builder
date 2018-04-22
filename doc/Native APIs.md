Native API Documentation
========================

This documents the APIs that can be used to implement native wrappers. There are
three types of APIs:

- `student_view_data`: Exposes block settings and content as JSON data. Can be
  retrieved via the edX
  [Course Blocks API](http://edx.readthedocs.io/projects/edx-platform-api/en/latest/courses/blocks.html),
  e.g.,
  ```
  GET https://<lms_server_url>/api/courses/v1/blocks/?course_id=<course_id>&username=<username>&depth=all&requested_fields=student_view_data&student_view_data=<xblock_types>
  ```
  Does not include user-specific data, which is available from `student_view_user_state`.
- `student_view_user_state`: XBlock handler which returns the currently logged
  in user's state data in JSON format (e.g. items derived from `Scope.user_state`
  fields).
  ```
  GET https://<lms_server_url>/courses/<course_id>/xblock/<xblock_id>/handler/student_view_user_state
  ```
- Custom XBlock handlers used for submitting user input and recording user actions.

Problem Builder (`problem-builder`)
-----------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `max_attempts`: (integer) Max number of allowed attempts.
- `extended_feedback`: (boolean) `true` if extended feedback is enabled for this
  block.
- `feedback_label`: (string) Feedback message header.
- `messages`: (object) A dict with three string entries: `completed`,
  `incomplete`, and `max_attempts_reached`. See below for info on each.
- `components`: (array) A list of `student_view_data` output of all immediate
  child components which implement `student_view_data`. Child components which
  don't implement `student_view_data` are omitted from the list.

#### `messages`

These messages are displayed as feedback, depending on the state of the
block. Any of these may be `null`.

- `completed`: (string) Message to be shown if the user successfully completes
  the problem. May contain HTML.
- `incomplete`: (string) Message to be shown if the user did not successfully
  complete the problem, but still has available attempts left. May contain HTML.
- `max_attempts_reached`: (string) Message to be shown if the user did not
  complete the problem and has no available attempts left.

### `student_view_user_state`

- `num_attempts`: (integer) Number of attempts used so far.
- `completed`: (boolean) `true` if the user successfully completed the problem at least once.
- `student_results`: (array) A list of user submitted answers with metadata for
  each child component. See below for more info.
- `components`: (object) Contains the `student_view_user_state` output of all
  immediate child components which implement `student_view_user_state`. Each key
  is a component ID (string), and the value is the component's
  `student_view_user_state` (object). Child components which don't implement
  student_view_user_state are not included in the dict.

#### `student_results`

The `student_results` field is an array of two-element arrays. Each nested array
has the form of `[component_name, data]`. If the user has not made any
submissions to particular component, then the element corresponding to that
component may be omitted from the array. The structure of the `data` object
depends on the type of the child component and is described separately for each
type of child component below.

### Custom Handlers

#### `submit`

The `submit` XBlock JSON handler is used for submitting student input. The
`POST` data should be a dict where keys are child component names. The values
depend on the component type and are described separately for each type of child
component below.

Example URL:

```
POST https://<lms_server_url>/courses/<course_id>/xblock/<xblock_id>/handler/submit
```

Returns a JSON object which contains these fields:

- `results`: (array) Same as `student_results` described under
  `student_view_user_state` above.
- `completed`: (boolean) Same as `completed` described under
  `student_view_user_state` above.
- `message`: (string) One of the `completed`, `incomplete`, or
  `max_attempts_reached` feedback messages described under `messages` above. Can
  be `null` if no messages has been defined. May contain HTML.
- `max_attempts`: (integer) Same as `max_attempts` under `student_view_data`.
- `num_attempts`: (integer) Same as `num_attempts` under
  `student_view_user_state`.

Step Builder (`step-builder`)
-----------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `title`: (string) The display name of the component.
- `show_title`: (boolean) `true` if the title should be displayed.
- `weight`: (float) The weight of the problem.
- `extended_feedback`: (boolean) `true` if extended feedback is enabled for this
  block.
- `max_attempts`: (integer) Max number of allowed attempts.
- `components`: (array) A list of `student_view_data` output of all immediate
  child components which implement `student_view_data`. For `step-builder`,
  immediate children are typically `sb-step` and `sb-review-step` type
  components. Child components which don't implement `student_view_data` are
  omitted from the list.

### `student_view_user_state`

Same as [Problem Builder above](#problem-builder-problem-builder), but also
contains these additional fields:

- `active_step`: (integer) The index of the step which is currently
  active. Starts at zero.
- `score_summary`: (object) Contains the user's score information for their completed attempts.
  If no attempts have been completed yet, then this object will be empty (`{}`).
  If one or more attempts have been made, then this object will contain:
    - `correct`: (array) list of questions that were answered correctly.
    - `correct_answers`: (integer) Number of questions answered correctly.
    - `incorrect`: (array) list of questions that were answered incorrectly.
    - `incorrect_answers`: (integer) Number of questions answered incorrectly.
    - `partial`: (array) list of questions that were answered partially correctly.
    - `partially_correct_answers`: (integer) Number of questions answered partially correctly.
    - `review_tips`: (array) List of review tips for each question answered incorrectly, where provided.
    - `score`: (integer) Total points earned for the problems in the step builder, weighted for each step.
    - `complete`: (boolean) True if all problems were answered correctly.
    - `max_attempts_reached`: (boolean) True if the maximum number of attempts has been reached.
    - `show_extended_review`: (boolean) True if extended feedback is configured, and the maximum
      number of attempts has been reached.


### Custom Handlers

#### `submit`

The `submit` XBlock JSON handler is used for submitting student input. The
`POST` data should be a dict where keys are child component names. The values
depend on the component type and are described separately for each type of child
component below.

In addition to child component names, the `POST` data should also include the
`active_step` field. The value should be the index of the current step.

Example URL:

```
POST https://<lms_server_url>/courses/<course_id>/xblock/<xblock_id>/handler/submit --data '{"bf9c37a":[{"name":"input","value":"Freeform answer"}],"71f85d0d3e7dabfc1a8cfecf72dce4284f18b13a":"3","71c526b60ec97364214ac70860def69914de84e7":["000bc8e","da9691e"],"477847c4f3540f37b8b3815430a74632a352064d":0.59,"b66a6115af051939c5ce92fb5ff739ccf704d1e9":false}'
```

#### `try_again`

The `try_again` XBlock JSON handler can be used when the student reaches the
final step. Sending a `POST` request to `try_again` will reset the problem and
all of its children.

Returns a JSON object containing the new value of `active_step`.

Example URL:

```
POST https://<lms_server_url>/courses/<course_id>/xblock/<xblock_id>/handler/try_again
```

To call this method you must send a valid JSON body, so put `{}` as the body
of the POST request.

Mentoring Step (`sb-step`)
--------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-step"` for Mentoring Step components.
- `title`: (string) Step component's display name.
- `show_title`: (boolean) `true` if the title should be displayed.
- `next_button_label`: (string) Text label of the "Next Step" button.
- `message`: (string) Feedback or instructional message which should be
  displayed after student submits the step. May be `null`.
- `components`: (array) A list of `student_view_data` output of all immediate
  child components which implement `student_view_data`. Child components which
  don't implement `student_view_data` are omitted from the list.

### `student_view_user_state`

- `student_results`: (array) Same as `student_results` described under
  `student_view_user_state` in the Problem Builder section.
- `components`: (object) Same as `components` described under
  `student_view_user_state` in the Problem Builder section.

Review Step (`sb-review-step`)
------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-review-step`" for Review Step components.
- `title`: (string) Display name of the component.
- `components`: (array) A list of `student_view_data` output of all immediate
  child components which implement `student_view_data`. Child components which
  don't implement `student_view_data` are omitted from the list.

Conditional Message (`sb-conditional-message`)
----------------------------------------------

Conditional Message component is always child of a Review Step component.

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-conditional-message"` for Conditional
  Message components.
- `content`: (string) Content of the message. May contain HTML.
- `score_condition`: (string) One of `"perfect"`, `"imperfect"`, or `"any"`.
- `num_attempts_condition`: (string) One of `"can_try_again"`,
  `"cannot_try_again"`, or `"any"`.

Score Summary (`sb-review-score`)
---------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-review-score"` for Score Summary
  components.

Per-Question Feedback (`sb-review-per-question-feedback`)
---------------------------------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-review-per-question-feedback"` for Score
  Summary components.

Long Answer (`pb-answer`)
-------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"pb-answer"` for Long Answer components.
- `id`: (string) Unique ID (name) of the component.
- `weight`: (float) The weight of this component.
- `question`: (string) The question/text displayed above the input field.

### `student_view_user_state`

- `answer_data`: (object) A dict with info about students submitted answer. See
  below for more info.

#### `answer_data`

The `answer_data` field contains these items:

- `student_input`: (string) Text that the student entered.

### `student_results`

- `status`: (string) One of `"correct"` or `"incorrect"`.
- `score`: (integer) Student's score. One of `1` or `0`.
- `weight`: (float) Child component's weight attribute.
- `student_input`: (string) Text entered by the user.

### POST Submit Data

When submitting the problem either via Problem Builder or Step Builder, the data
entry corresponding to the Long Answer block should be a single object
containing the `"value"` property. Example: `{"value": "Student's input"}`.

Long Answer Recap (`pb-answer-recap`)
-------------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID (the ID of the associated Long Answer).
- `display_name`: (string) The XBlock's display name (the title of this Long Answer Recap section).
- `description`: (string) The XBlock's description (the text message displayed in
  the Long Answer Recap section).
- `type`: (string) Always equals `"pb-answer-recap"` for Long Answer Recap components.
- `id`: (string) Unique ID (name) of the component.

### `student_view_user_state`

Same as the Long Answer `student_view_user_state`, above.

Multiple Choice Question (`pb-mcq`)
-----------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"pb-mcq"` for MCQ components.
- `id`: (string) Unique ID (name) of the component.
- `question`: (string) The content of the question.
- `message`: (string) General feedback provided when submitting.
- `weight`: (float) The weight of the problem.
- `choices`: (array) A list of objects providing info about available
  choices. See below for more info.
- `tips`: (array) A list of objects providing info about tips defined for the
  problem. See below for more info.

#### `choices`

Each entry in the `choices` array contains these values:

- `content`: (string) Display name of the choice.
- `value`: (string) The value of the choice. This is the value that gets
  submitted and stored when users submits their answer.

#### `tips`

Each entry in the `tips` array contains these values:

- `content`: (string) The text content of the tip.
- `for_choices`: (array) A list of string values corresponding to choices to
  which this tip applies to.

### `student_view_user_state`

- `student_choice`: (string) The value of the last submitted choice.

### `student_results`

- `status`: (string) One of `"correct"` or `"incorrect"`.
- `score`: (integer) Student's score. One of `1` or `0`.
- `weight`: (float) Child component's weight attribute.
- `submission`: (string) The value of the choice that the user selected.
- `message`: (string) General feedback. May contain HTML.

### POST Submit Data

When submitting the problem the data should be a single object containing the
`"value"` property which has the value of the selected choice.
Example: `{"value": "blue"}`


Rating Question (`pb-rating`)
-----------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
Identical to [MCQ questions](#multiple-choice-question-pb-mcq) except that the
`type` field always equals `"pb-rating"`.

### `student_view_user_state`

- `student_choice`: (string) The value of the last submitted choice.

### `student_results`

Identical to [MCQ questions](#multiple-choice-question-pb-mcq).

### POST Submit Data

When submitting the problem the data should be equal to the string value of the
selected choice. Example: `"3"`.


Swipeable Binary Response (`pb-swipe`)
--------------------------------------

### `student_view_data`
- `id`: (string) The XBlock's ID
- `block_id`: (string) The XBlock's usage ID
- `display_name`: (string) The XBlock's display name
- `type`: (string): The XBlock's identifier, "pb-swipe"
- `text`: (string) The text to display on the card
- `img_url`: (string) URL of the image to display as the background of the card
- `correct`: (boolean) Whether the student's swipe is correct or not
- `feedback`: (object) Feedback to display to users in case of correct or 
  incorrect response.

### `student_view_user_state`

- `student_choice`: (boolean) The value of the last submitted choice.

### POST Submit Data

When submitting the problem the data should be a single object containing the
`"value"` property which has a boolean value indicating which swipe the student took:

- Right -> True
- Left -> False

Example: `{"value": true}` if the student made a *rightwards* swipe.

The returned result will contain the following:

- `submission`: (boolean) The value just POST'd.
- `status`: (string) `"correct"` if the swipe is correct, `"incorrect"` otherwise.
- `score`: (integer) 1 if the swipe is correct, otherwise 0.
- `feedback`: (string) The ``feedback_correct`` message or ``feedback_incorrect`` 
  message based on whether the feedback is correct or incorrect. 

Multiple Response Question (`pb-mrq`)
-------------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"pb-mrq"` for Multiple Response Question
  components.
- `id`: (string) Unique ID (name) of the component.
- `title`: (string) Display name of the component.
- `weight`: (float) Weight of the problem.
- `question`: (string) The content of the question.
- `message`: (string) General feedback provided when submitting.
- `hide_results`: (boolean) `true` if results should be hidden.
- `choices`: (array) A list of objects providing info about available
  choices. See below for more info.
- `tips`: (array) A list of objects providing info about tips defined for the
  problem. See below for more info.

#### `tips`

Each entry in the `tips` array contains these values:

- `content`: (string) The text content of the tip.
- `for_choices`: (array) A list of string values corresponding to choices to
  which this tip applies to.

### `student_view_user_state`

- `student_choices`: (array) A list of string values corresponding to choices
  last submitted by the student.

### `student_results`

- `status`: (string) One of `"correct"`, `"incorrect"`, or `"partial"`.
- `score`: (float) Student's score. Float in the range `0 - 1`.
- `weight`: (float) Child component's weight attribute.
- `submissions`: (array) A list of string values corresponding to the choices
  that the user selected.
- `message`: (string) General feedback. May contain HTML.
- `choices`: (array) A list of dicts containing info about available
  choices. See below for more info.

#### `choices`

Each item in the `choices` array contains these fields:

- `completed`: (boolean) Boolean indicating whether the state of the choice is
  correct.
- `selected`: (boolean) `true` if the user selected this choice.
- `value`: (string) The value of the choice.

### POST Submit Data

The submitted data should be a JSON array of string values corresponding to
selected choices. Example: `["red","blue"]`.

Ranged Value Slider (`pb-slider`)
---------------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"pb-slider"` for Ranged Value Slider
  components.
- `id`: (string) Unique ID (name) of the component.
- `title`: (string) Display name of the component.
- `hide_header`: (boolean) `true` if header should be hidden.
- `question`: (string) The content of the question.
- `min_label`: (string) Label for the low end of the range.
- `max_label`: (string) Label for the high end of the range.

### `student_view_user_state`

- `student_value`: (float) The value last selected by the user.

### `student_results`

- `status`: (string) Always `"correct"` for Ranged Value Slider components.
- `score`: (integer) Always equals `1` for Ranged Value Slider components.
- `weight`: (float) Child component's weight attribute.
- `submission`: (float) The float value of the user submission, or `null` if the
  component has never been submitted.

### POST Submit Data

The submitted data should be a float value representing the value selected by
the user. Example: `0.65`.

Completion (`pb-completion`)
----------------------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"pb-completion"` for Completion components.
- `id`: (string) Unique ID (name) of the component.
- `title`: (string) Display name of the problem.
- `hide_header`: (boolean) `true` if the header should be hidden.
- `question`: (string) The content of the question.
- `answer`: (string) Represents the answer that the student can (un)check.

### `student_view_user_state`

- `student_value`: (boolean) Boolean indicating whether the user checked the
  checkbox. Can also be `null` if the user never checked or unchecked the
  checkbox.

### `student_results`

- `status`: (string) Always `"correct"` for Completion components.
- `score`: (integer) Always equals `1` for Completion components.
- `weight`: (float) Child component's weight attribute.
- `submission`: (boolean) The boolean value of the user submission, or `null` if
  the component has never been submitted.

### POST Submit Data

The submitted data should be JSON boolean, `true` if the checkbox is checked and
`false` if it is not. Example: `true`.

Plot (`sb-plot`)
----------------

### `student_view_data`

- `block_id`: (string) The XBlock's usage ID.
- `display_name`: (string) The XBlock's display name.
- `type`: (string) Always equals `"sb-plot"` for Plot components.
- `title`: (string) Display name of the component.
- `q1_label`: (string) Quadrant I label.
- `q2_label`: (string) Quadrant II label.
- `q3_label`: (string) Quadrant III label.
- `q4_label`: (string) Quadrant IV label.
- `point_color_default`: (string) Point color to use for default overlay
  (string). - `plot_label`: Label for default overlay which shows student's
  answers to scale questions.
- `point_color_average`: (string) Point color to use for the average overlay.
- `overlay_data`: (string) JSON data representing points on overlays.
- `hide_header`: (boolean) Always `true` for Plot components.

### `student_view_user_state`

- `average_claims`: (array) Averaged claim data
- `default_claims`: (array) Default claim data
