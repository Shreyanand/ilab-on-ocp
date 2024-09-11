# type: ignore
# pylint: disable=no-value-for-parameter,import-outside-toplevel,import-error,no-member,missing-function-docstring
from typing import Optional
from kfp import dsl


@dsl.container_component
def kubectl_apply_op(manifest: str):
    return dsl.ContainerSpec(
        "registry.redhat.io/openshift4/ose-cli",
        ["/bin/sh", "-c"],
        [f'echo "{manifest}" | kubectl apply -f -'],
    )


@dsl.container_component
def kubectl_wait_for_op(
    condition: str,
    kind: str,
    name: str,
    # namespace: Optional[str] = None,
    # timeout: Optional[str] = None,
):
    return dsl.ContainerSpec(
        "registry.redhat.io/openshift4/ose-cli",
        ["/bin/sh", "-c"],
        [
            f"kubectl wait --for={condition} {kind}/{name} --timeout=2h",
        ],
    )


@dsl.container_component
def artifact_to_pvc_op(data: dsl.Input[dsl.Artifact], pvc_path: str):
    return dsl.ContainerSpec(
        "registry.access.redhat.com/ubi9/toolbox",
        ["/bin/sh", "-c"],
        [f"cp -r {data.path} {pvc_path}"],
    )
