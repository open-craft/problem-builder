Using Problem Builder and Step Builder
======================================

First, enable the blocks in Studio (see "Enabling in Studio", below).

Next, decide whether you want to use **Problem Builder** or **Step Builder** to
create your exercise. Select the name of the block below for detailed usage
instructions.

* [Problem Builder](Problem Builder.md) is simply a group of one or more
  question[s].
* [Step Builder](Step Builder.md) lets authors build more complex exercises
  where questions are grouped into "steps" and students answer the questions in
  each step at a time. An optional "review step" can be added to the end of the
  exercise, which can summarize the student's results and provide tailored
  feedback and study suggestions.

Once you add a Problem Builder or Step Builder component to a course, you can
then click on the "View" link (seen at the top right of the component) to open
the component for editing. You can then add [any of the supported question and
content types](Questions.md).


Enabling in Studio
------------------

You can enable the Problem Builder and Step Builder XBlocks in Studio by
modifying the advanced settings for your course:

1. From the main page of a specific course, navigate to **Settings** ->
   **Advanced Settings** from the top menu.
2. Find the **Advanced Module List** setting.
3. To enable Problem Builder for your course, add `"problem-builder"` to the
   modules listed there.
4. To enable Step Builder for your course, add `"step-builder"` to the modules
   listed there.
5. Click the **Save changes** button.

Note that it is perfectly fine to enable both Problem Builder and Step Builder
for your course -- the blocks do not interfere with each other.

NOTE: The ``pb-swipe`` component is currently in development and as such is 
disabled by default. It needs to be 
[manually enabled](Questions.md#swipeable-binary-choice-question).
