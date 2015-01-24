class StepParentMixin(object):
    """
    An XBlock mixin for a parent block containing Step children
    """

    @property
    def steps(self):
        """
        Generator returning the usage_id for all of this XBlock's 
        children that are "Steps"
        """
        step_ids = []
        for child_id in self.children:
            child = self.runtime.get_block(child_id)
            if isinstance(child, StepMixin):
                step_ids.append(child_id)
        return step_ids


class StepMixin(object):
    """
    An XBlock mixin for a child block that is a "Step"
    """
    @property
    def step_number(self):
        return list(self.get_parent().steps).index(self.scope_ids.usage_id) + 1

    @property
    def lonely_step(self):
        if self.scope_ids.usage_id not in self.get_parent().steps:
            raise ValueError("Step's parent should contain Step", self, self.get_parent().steps)
        return len(self.get_parent().steps) == 1
