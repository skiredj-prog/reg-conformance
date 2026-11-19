"""Runtime-neutral conformance harness.

Vectors are written once, as scenarios over a small set of primitives
(`RuntimePort`). A runtime is hooked by implementing only the primitives it
supports; anything else is reported as ADAPTER_REQUIRED, never as PASS.
"""
