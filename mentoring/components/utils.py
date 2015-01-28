"""
Helper methods

Should eventually be moved to xblock-utils.
"""


def child_isinstance(block, child_id, block_class_or_mixin):
    """
    Is "block"'s child identified by usage_id "child_id" an instance of
    "block_class_or_mixin"?

    This is a bit complicated since it avoids the need to actually
    instantiate the child block.
    """
    def_id = block.runtime.id_reader.get_definition_id(child_id)
    type_name = block.runtime.id_reader.get_block_type(def_id)
    child_class = block.runtime.load_block_type(type_name)
    return issubclass(child_class, block_class_or_mixin)
