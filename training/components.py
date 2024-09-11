# type: ignore
# pylint: disable=import-outside-toplevel,missing-function-docstring

from kfp import dsl
from typing import NamedTuple

IMAGE = "registry.access.redhat.com/ubi9/python-311:latest"



@dsl.component(base_image=IMAGE)
def pytorchjob_manifest_op(name_suffix: str, pvc_name: str) -> NamedTuple('outputs', manifest=str, name=str):
    import inspect
    Outputs = NamedTuple('outputs', manifest=str, name=str)
    name = f"train-{name_suffix}"
    manifest = inspect.cleandoc(
        f"""
        apiVersion: kubeflow.org/v1
        kind: PyTorchJob
        metadata:
          name: {name}
        spec:
          pytorchReplicaSpecs:
            Master:
              replicas: 1
              template:
                metadata:
                  annotations:
                    sidecar.istio.io/inject: 'false'
                spec:
                  containers:
                    - args:
                        - python3.11 -u "run.py"
                      command:
                        - /bin/bash
                        - '-c'
                        - '--'
                      image: 'quay.io/michaelclifford/test-train:0.0.11'
                      name: pytorch
                      resources: {{}}
                      volumeMounts:
                        - mountPath: /workspace
                          name: workspace
                  volumes:
                    - name: workspace
                      persistentVolumeClaim:
                        claimName: {pvc_name}
        """
    )

    return Outputs(manifest, name)
