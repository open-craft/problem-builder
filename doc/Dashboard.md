"Dashboard" Self-Assessment Summary Block
=========================================

A "Dashboard" XBlock provides a concise way to summarize a student's answers to
groups of multiple choice questions.

You configure it like this, by pasting in the `url_name`s of some Problem
Builder ("Mentoring") blocks:
![Screen shot of Dashboard XBlock configuration](img/dashboard-configuration.png)


And it will then look like this (after a student has submitted their answers):
![Screen shot of a Dashboard XBlock](img/dashboard-example.png)


Visual Representation
---------------------

The Dashboard also supports an optional visual representation. This is a
powerful feature, but setting it up is quite involved.

The end result is shown below. You can see a diagram, in which a colored arrow
appears as the student works through the various "Steps". Each "Step" is one
mentoring block, which contains several multiple choice questions. Based on the
average value of the student's choices, the step is given a color.

In this example, steps that have not been attempted are transparent, steps that
have been attempted but with an average less than two are grey, and steps with
an average higher than two are green.

![Screen shot of visual representation](img/dashboard-visual.png)

To achieve the result shown above requires a set of "stacked" image files (one
for each step), as well as an overlay image (in this case, the overlay image
contains all the text).

To build this example, the images used look like this:  
![Images Used](img/dashboard-visual-instructions.png)

The block was configured to use these images as follows:
![Screen shot of visual representation rule configuration](img/dashboard-visual-config.png)

Notice that step 2 has turned green due to the default rule "hueRotate 280" for
any steps with an average above 2, and the first step has a blurred, grey
background due to the first rule for average values less than 2.

The **Visual Representation Settings** used to define the visual representation
must be in JSON format. The supported entries are:

* **`"images"`**: A list of image URLs, one per PB block, in the same order as
  the 'blocks' list (the list of `url_name`s described above). If the images you
  wish to use are on your computer, first upload them to the course's "Files and
  Uploads" page. You can then find the URL for each image listed on that page.
  Note that each URL must start with "http://" or "https://".
    * All images listed here will be layered on top of each other, and can be
    colorized, faded, etc. based on the average value of the student's choices
    for the corresponding group of MCQs.
* **`"overlay"`**: (Optional) The URL of an image to be drawn on top of the
  layered images, with no effects applied.
* **`"background"`**: (Optional) The URL of an image to be drawn behind the
  layered images, with no effects applied.
* **`"colorRules"`**: (Optional) The rules used to determine how the student's
  average choice values affect each layer's image. Each rule is evaluated in
  order, and the first matching rule is used. Each rule is a JSON object
  (`{ ... }`) that may consist of any of the following optional entries.
  * `if`: An optional expression involving `x` (the student's average choice
    value). If this is true, then this rule will be used. If this is false, the
    rule will not be used. If no `if` clause is set, the rule will always be
    used, unless an earlier rule matched first.  
    Examples:
      - `"if": "x > 3"`
      - `"if": "0 < x < 1"`
      - `"if": "(x > 3) and (x < 6 or x > 100)"`
  * `hueRotate`: If this rule matches, adjust the color of all parts of the
    image that have some saturation. In the above example, this is used to
    change from a turquiose color to a light green. Valid values are between 0
    (no change) and 360. Note that this effect will *not* affect any parts of
    the image have no saturation (i.e. are white, black, or any shade of grey).  
    Examples:
      - `"hueRotate": "180"`
      - `"hueRotate": "x * 30"`
  * `blur`: If this rule matches, apply a gaussian blur to blur this layer's
    image. The standard deviation of the blur must be specified.  
    Examples:
      - `"blur": "3"`
      - `"blur": "x"`
  * `saturate`: If this rule matches, adjust the saturation of the image. `1`
    means no change, and `0` means fully desaturated. Valid values are between
    zero and one.  
    Examples:
      - `"saturate": "0.2"`
