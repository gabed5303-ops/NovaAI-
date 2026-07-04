"""The plugin system: how Nova gains new abilities without changing its core.

`base.py` defines what a plugin is. `manager.py` finds plugins (both the
built-in ones in `builtin/` and any third-party ones installed on the system)
and runs their setup/teardown. `builtin/` holds example plugins that ship with
Nova.
"""
