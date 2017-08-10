Native API Documentation
========================

This documents the APIs that can be used to implement native wrappers. There are
three types of APIs:

- `student_view_data`: Exposes block settings and content as JSON data. Can be
  retrieved via the edX Course Blocks API. Does not include user-specific data
  (i.e. items derived from `Scope.user_state` fields).
- `student_view_user_state`: XBlock handler which returns user state data in
  JSON format.
- Custom XBlock handlers used for submitting user input and recording user actions.

Problem Builder (`problem-builder`)
-----------------------------------

### `student_view_data`

- `max_attempts`: Max number of allowed attempts (integer).
- `extended_feedback`: `true` if extended feedback is enabled for this block
  (boolean).
- `feedback_label`: Feedback message header (string).
- `messages`: A dict with three string entries: `completed`, `incomplete`, and
  `max_attempts_reached`. See below for info on each (object).
- `components`: A list of `student_view_data` output of all immediate child
  components which implement `student_view_data`. Child components which don't
  implement `student_view_data` are omitted from the list (array).

#### `messages`

These messages are displayed as feedback, depending on the state of the block.

- `completed`: Message to be shown if the user successfully completes the
  problem. May contain HTML (string).
- `incomplete`: Message to be shown if the user did not successfully complete
  the problem, but still has available attempts left. May contain HTML (string).
- `max_attempts_reached`: Message to be shown if the user did not complete the
  problem and has no available attempts left.

### `student_view_user_state`

- `num_attempts`: Number of attempts used so far (integer).
- `completed`: `true` if the user successfully completed the problem at least
  once (boolean).
- `student_results`: A list of user submitted answers with metadata for each
  child component. See below for more info (array).
- `components`: A dict of `student_view_user_state` output of all immediate
  child components which implement `student_view_user_state`. Dict keys are
  component IDs and the value corresponding to each key is the output of
  `student_view_user_state`(object). Child components which don't implement
  `student_view_user_state` are not included in the dict.

#### `student_results`

The `student_results` field is an array of two-element arrays. Each nested array
has the form of `[component_name, data]`. Only components which the student
already submitted are present in the array. The structure of the `data` object
depends on the type of the child component and is described separately for each
type of child component below.

### Custom Handlers

#### `submit`

The `submit` XBlock JSON handler is used for submitting student input. The
`POST` data should be a dict where keys are child component names. The values
depend on the component type and are described separately for each type of child
component below.

Returns a JSON object which contains these fields:

- `results`: Same as `student_results` described under
  `student_view_user_state` above.
- `completed`: Same as `completed` described under `student_view_user_state`
  above.
- `message`: One of the `completed`, `incomplete`, or `max_attempts_reached`
  feedback messages described under `messages` above. Can be `null` if no
  messages has been defined. May contain HTML (string).
- `max_attempts`: Same as `max_attempts` under `student_view_data`.
- `num_attempts`: Same as `num_attempts` under `student_view_user_state`.


Step Builder (`step-builder`)
-----------------------------

### `student_view_data`

- `title`: The display name of the component (string).
- `show_title`: `true` if the title should be displayed (boolean).
- `weight`: The weight of the problem (float).
- `extended_feedback`: `true` if extended feedback is enabled for this block
  (boolean).
- `max_attempts`: Max number of allowed attempts (integer).
- `components`: A list of `student_view_data` output of all immediate child
  components which implement `student_view_data`. For `step-builder`, immediate
  children are typically `sb-step` and `sb-review-step` type components. Child
  components which don't implement `student_view_data` are omitted from the list
  (array).

### `student_view_user_state`

Same as Problem Builder above, but also contains these additional fields:

- `active_step`: The index of the step which is currently active. Starts at zero
  (integer).

### Custom Handlers

#### `submit`

The `submit` XBlock JSON handler is used for submitting student input. The
`POST` data should be a dict where keys are child component names. The values
depend on the component type and are described separately for each type of child
component below.

In addition to child component names, the `POST` data should also include the
`active_step` field. The value should be the index of the current step.

#### `try_again`

The `try_again` XBlock JSON handler can be used when the student reaches the
final step. Sending a `POST` request to `try_again` will reset the problem and
all of its children.

Returns a JSON object containing the new value of `active_step`.

Mentoring Step (`sb-step`)
--------------------------

### `student_view_data`

- `type`: Always equals `"sb-step"` for Mentoring Step components (string).
- `title`: Step component's display name (string).
- `show_title`: `true` if the title should be displayed (boolean).
- `next_button_label`: Text label of the "Next Step" button (string).
- `message`: Feedback or instructional message which should be displayed after
  student submits the step (string).
- `components`: A list of `student_view_data` output of all immediate child
  components which implement `student_view_data`. Child components which don't
  implement `student_view_data` are omitted from the list (array).

### `student_view_user_state`

- `student_results`: Same as `student_results` described under
  `student_view_user_state` in the Problem Builder section.
- `components`: Same as `components` described under `student_view_user_state`
  in the Problem Builder section.

Review Step (`sb-review-step`)
------------------------------

### `student_view_data`

- `type`: Always equals `"sb-review-step`" for Review Step components (string).
- `title`: Display name of the component (string).
- `components`: A list of `student_view_data` output of all immediate child
  components which implement `student_view_data`. Child components which don't
  implement `student_view_data` are omitted from the list (array).

Conditional Message (`sb-conditional-message`)
----------------------------------------------

Conditional Message component is always child of a Review Step component.

### `student_view_data`

- `type`: Always equals `"sb-conditional-message"` for Conditional Message
  components (string).
- `content`: Content of the message. May contain HTML (string).
- `score_condition`: One of `"perfect"`, `"imperfect"`, or `"any"` (string).
- `num_attempts_condition`: One of `"can_try_again"`, `"cannot_try_again"`, or
  `"any"` (string).

Score Summary (`sb-review-score`)
---------------------------------

### `student_view_data`

- `type`: Always equals `"sb-review-score"` for Score Summary components
  (string).

Per-Question Feedback (`sb-review-per-question-feedback`)
---------------------------------------------------------

### `student_view_data`

- `type`: Always equals `"sb-review-per-question-feedback"` for Score Summary
  components (string).

Long Answer (`pb-answer`)
-------------------------

### `student_view_data`

- `type`: Always equals `"pb-answer"` for Long Answer components (string).
- `id`: Unique ID (name) of the component (string).
- `weight`: The weight of this component (float).
- `question`: The question/text displayed above the input field (string).

### `student_view_user_state`

- `answer_data`: A dict with info about students submitted answer. See below for
  more info(object).

#### `answer_data`

The `answer_data` field contains these items:

- `student_input`: Text that the student entered (string).
- `created_on`: Date/Time when the answer was first submitted (string).
- `modified_on`: Date/Time when the answer was last modified (string).

### `student_results`

- `status`: One of `"correct"` or `"incorrect"` (string).
- `score`: Student's score. One of `1` or `0` (integer).
- `weight`: Child component's weight attribute (float).
- `student_input`: Text entered by the user (string).

### POST Submit Data

When submitting the problem either via Problem Builder or Step Builder, the data
entry corresponding to the Long Answer block should be an array with a single
object containing the `"value"` property: `[{"value": "Student's input"}]`.

Multiple Choice Question (`pb-mcq`)
-----------------------------------

### `student_view_data`

- `type`: Always equals `"pb-mcq"` for MCQ components (string).
- `id`: Unique ID (name) of the component (string).
- `question`: The content of the question (string).
- `message`: General feedback provided when submitting (string).
- `weight`: The weight of the problem (float).
- `choices`: A list of objects providing info about available choices. See below
  for more info (array).
- `tips`: A list of objects providing info about tips defined for the
  problem. See below for more info (array).

#### `choices`

Each entry in the `choices` array contains these values:

- `content`: Display name of the choice (string).
- `value`: The value of the choice. This is the value that gets submitted and
  stored when users submits their answer (string).

#### `tips`

Each entry in the `tips` array contains these values:

- `content`: The text content of the tip (string).
- `for_choices`: A list of string values corresponding to choices to which this
  tip applies to (array).

### `student_view_user_state`

- `student_choice`: The value of the last submitted choice (string).

### `student_results`

- `status`: One of `"correct"` or `"incorrect"` (string).
- `score`: Student's score. One of `1` or `0` (integer).
- `weight`: Child component's weight attribute (float).
- `submission`: The value of the choice that the user selected (string).
- `message`: General feedback. May contain HTML (string).
- `tips`: HTML representation of tips. May be `null` (string).

### POST Submit Data

When submitting the problem the data should equal to the string value of the
selected choice.

Rating Question (`pb-rating`)
-----------------------------

### `student_view_data`

Identical to MCQ questions except that the `type` field always equals
`"pb-rating"`.

### `student_view_user_state`

- `student_choice`: The value of the last submitted choice (string).

### `student_results`

Identical to MCQ questions.

### POST Submit Data

When submitting the problem the data should equal to the string value of the
selected choice.

Multiple Response Question (`pb-mrq`)
-------------------------------------

### `student_view_data`

- `type`: Always equals `"pb-mrq"` for Multiple Response Question components
  (string).
- `id`: Unique ID (name) of the component (string).
- `title`: Display name of the component (string).
- `weight`: Weight of the problem (float).
- `question`: The content of the question (string).
- `message`: General feedback provided when submitting (string).
- `hide_results`: `true` if results should be hidden (boolean).

### `student_view_user_state`

- `student_choices`: A list of string values corresponding to choices last
  submitted by the student (array).

### `student_results`

- `status`: One of `"correct"`, `"incorrect"`, or `"partial"` (string).
- `score`: Student's score. Float in the range `0 - 1` (float).
- `weight`: Child component's weight attribute (float).
- `submissions`: A list of string values corresponding to the choices that the
  user selected (array).
- `message`: General feedback. May contain HTML (string).
- `choices`: A list of dicts containing info about available choices. See below
  for more info (array).

#### `choices`

Each item in the `choices` array contains these fields:

- `completed`: Boolean indicating whether the state of the choice is correct
  (boolean).
- `selected`: `true` if the user selected this choice (boolean).
- `tips`: Tips formatted as a string of HTML (string).
- `value`: The value of the choice (string).

### POST Submit Data

The submitted data should be a JSON array of string values corresponding to
selected choices.

Ranged Value Slider (`pb-slider`)
---------------------------------

### `student_view_data`

- `type`: Always equals `"pb-slider"` for Ranged Value Slider components (string).
- `id`: Unique ID (name) of the component (string).
- `title`: Display name of the component (string).
- `hide_header`: `true` if header should be hidden (boolean).
- `question`: The content of the question (string).
- `min_label`: Label for the low end of the range (string).
- `max_label`: Label for the high end of the range (string).

### `student_view_user_state`

- `student_value`: The value last selected by the user (float).

### `student_results`

- `status`: Always `"correct"` for Ranged Value Slider components (string).
- `score`: Always equals `1` for Ranged Value Slider components (integer).
- `weight`: Child component's weight attribute (float).
- `submission`: The float value of the user submission, or `null` if the
  component has never been submitted (float).

### POST Submit Data

The submitted data should be a float value representing the value selected by
the user.

Completion (`pb-completion`)
----------------------------

### `student_view_data`

- `type`: Always equals `"pb-completion"` for Completion components (string).
- `id`: Unique ID (name) of the component (string).
- `title`: Display name of the problem (string).
- `hide_header`: `true` if the header should be hidden (boolean).
- `question`: The content of the question (string).
- `answer`: Represents the answer that the student can (un)check (string).

### `student_view_user_state`

- `student_value`: Boolean indicating whether the user checked the checkbox. Can
  also be `null` if the user never checked or unchecked the checkbox (boolean).

### `student_results`

- `status`: Always `"correct"` for Completion components (string).
- `score`: Always equals `1` for Completion components (integer).
- `weight`: Child component's weight attribute (float).
- `submission`: The boolean value of the user submission, or `null` if the
  component has never been submitted (boolean).

### POST Submit Data

The submitted data should be JSON boolean, `true` if the checkbox is checked and
`false` if it is not.

Plot (`sb-plot`)
----------------

### `student_view_data`

- `type`: Always equals `"sb-plot"` for Plot components (string).
- `title`: Display name of the component (string).
- `q1_label`: Quadrant I label (string).
- `q2_label`: Quadrant II label (string).
- `q3_label`: Quadrant III label (string).
- `q4_label`: Quadrant IV label (string).
- `point_color_default`: Point color to use for default overlay (string).
- `plot_label`: Label for default overlay which shows student's answers to scale
  questions (string).
- `point_color_average`: Point color to use for the average overlay (string).
- `overlay_data`: JSON data representing points on overlays (string).
- `hide_header': Always `true` for Plot components (boolean).
