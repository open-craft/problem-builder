class StepParentMixin(object):
    """
    A parent containing the Step objects

    The parent must have a get_children_objects() method.
    """
    @property
    def steps(self):
        return [child for child in self.get_children_objects() if isinstance(child, StepMixin)]


class StepMixin(object):
    @property
    def step_number(self):
        return self.parent.steps.index(self) + 1

    @property
    def lonely_step(self):
        if self not in self.parent.steps:
            raise ValueError("Step's parent should contain Step", self, self.parents.steps)
        return len(self.parent.steps) == 1
