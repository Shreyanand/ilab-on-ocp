# type: ignore
# pylint: disable=import-outside-toplevel,missing-function-docstring,unused-argument

from kfp import dsl
from typing import NamedTuple


@dsl.component(base_image="registry.access.redhat.com/ubi9/python-311:latest")
def pytorchjob_manifest_op(
    name_suffix: str,
    pvc_name: str,
    num_proc_per_node: int,
    nnodes: int,
    num_workers: int,
    base_image: str,
    data_path: str                      
) -> NamedTuple("outputs", manifest=str, name=str):
    Outputs = NamedTuple("outputs", manifest=str, name=str)
    return Outputs("", "")
