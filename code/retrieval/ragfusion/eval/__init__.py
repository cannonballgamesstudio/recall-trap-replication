"""A/B eval support: static index bring-up helpers.

These exist for the minimal serving stand-up that the SWE-bench A/B eval needs
(see docs/specs/2026-06-28-rag-harness-ab-eval-design.md, section 9) —
NOT the production reconciler/ZFS path. They build one srclight index per
(repo, ref) over a plain checkout and register it 'ready' so retrievald can serve it.
"""

from ragfusion.eval.index_register import index_and_register

__all__ = ["index_and_register"]
