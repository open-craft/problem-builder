from xblock.core import XBlock
from xblock.fields import Scope, String
from xblock.fragment import Fragment
from xblockutils.studio_editable import StudioEditableXBlockMixin


# Make '_' a no-op so we can scrape strings
def _(text):
    return text


class BeeperBlock(StudioEditableXBlockMixin, XBlock):
    """ Dummy XBlock to demonstrate navigation to children """
    content = String(
        display_name=_("Beeper Text"),
        help=_("Text to display"),
        scope=Scope.content,
        default="",
    )
    editable_fields = ('content',)

    def student_view(self, context):
        normalized_id = self.scope_ids.usage_id.replace(run=None, branch=None, version_guid=None)
        fragment = Fragment()
        if context.get('activate_block_id', None) == normalized_id:
            fragment.add_javascript("alert('{content}')".format(content=self.content))
        return fragment

    def author_view(self, content):
        fragment = Fragment()
        fragment.add_content(unicode(
            _("<div>Beeper ID: {id}</div><div>Beeper Message: {message}</div>").format(id=self.id, message=self.content)
        ))
        return fragment

    @property
    def id(self):
        """
        Get the url_name for this block. In Studio/LMS it is provided by a mixin, so we just
        defer to super(). In the workbench or any other platform, we use the usage_id.
        """
        try:
            return super(BeeperBlock, self).url_name
        except AttributeError:
            return unicode(self.scope_ids.usage_id)
