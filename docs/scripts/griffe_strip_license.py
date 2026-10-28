"""Griffe extension removing the metadata/license header from the module docstrings."""

import griffe


class StripLicenseHeader(griffe.Extension):
    def on_module_members(self, *, mod: griffe.Module, **kwargs) -> None:
        if mod.docstring and mod.docstring.value.lstrip().startswith("Metadata:"):
            mod.docstring = None
