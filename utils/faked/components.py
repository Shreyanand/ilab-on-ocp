# type: ignore
# pylint: disable=unused-argument,missing-function-docstring
from kfp import dsl

IMAGE = "registry.access.redhat.com/ubi9/python-311:latest"


@dsl.component(base_image=IMAGE)
def kubectl_apply_op(manifest: str):
    return


@dsl.component(base_image=IMAGE)
def kubectl_wait_for_op(condition: str, kind: str, name: str):
    return
