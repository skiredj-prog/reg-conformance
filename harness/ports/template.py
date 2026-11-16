"""Starting point for hooking a new runtime.

Copy this file, rename the class, then:
  1. implement one primitive,
  2. add its name to `capabilities`,
  3. run `python -m harness --port your.module:YourPort`.

Until a capability is listed, every scenario that needs it is reported
ADAPTER_REQUIRED. Nothing can pass by default.

You own two mappings, and both belong in this file, in the open:
  - your native verdicts  -> REG dispositions (PASS, FLAG, HOLD, HARD_VETO)
  - your native refusals  -> REG reason codes (see harness.port.R_*)
"""
from .. import port as P


class TemplatePort(P.RuntimePort):
    name = "template"
    interface_mode = "port:template"
    evidence_level = 2
    capabilities = frozenset()          # add capabilities as you implement them
    not_applicable = {}                 # vector_id -> why it cannot apply
    declared_gaps = {}                  # vector_id -> gap you already know about

    def reset(self):
        """Bring your runtime back to a clean, pinned state."""
