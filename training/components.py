# type: ignore
# pylint: disable=import-outside-toplevel,missing-function-docstring

from kfp import dsl
from typing import NamedTuple

IMAGE = "registry.access.redhat.com/ubi9/python-311:latest"

@dsl.component(base_image=IMAGE)
def pytorchjob_manifest_op(name_suffix: str,
                           pvc_name: str,
                           num_proc_per_node: int = 2,
                           nnodes: int = 2,
                           num_workers: int = 1,
                           base_image: str = "quay.io/michaelclifford/test-train:0.0.15",
                           data_path: str = "training/sample-data/train_all_pruned_SDG.jsonl"
                           ) -> NamedTuple('outputs', manifest=str, name=str):
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
          nprocPerNode: {str(num_proc_per_node)}
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
                        - python3.11 -u "run.py" --nnodes {nnodes} --nproc_per_node {num_proc_per_node} --node_rank $(RANK) --rdzv_endpoint $(MASTER_ADDR):$(MASTER_PORT) --data_path {data_path}
                      command:
                        - /bin/bash
                        - '-c'
                        - '--'
                      image: {base_image}
                      name: pytorch
                      resources:
                        limits:
                          nvidia.com/gpu: {num_proc_per_node}
                        requests:
                          nvidia.com/gpu: {num_proc_per_node}
                      volumeMounts:
                        - mountPath: /workspace
                          name: workspace
                  volumes:
                    - name: workspace
                      persistentVolumeClaim:
                        claimName: {pvc_name}
            Worker:
              replicas: {num_workers}
              template:
                metadata:
                  annotations:
                    sidecar.istio.io/inject: 'false'
                spec:
                  containers:
                    - args:
                        - - python3.11 -u "run.py" --nnodes {nnodes} --nproc_per_node {num_proc_per_node} --node_rank $(RANK) --rdzv_endpoint $(MASTER_ADDR):$(MASTER_PORT) --data_path {data_path}
                      command:
                        - /bin/bash
                        - '-c'
                        - '--'
                      image: {base_image}
                      name: pytorch
                      resources:
                        limits:
                          nvidia.com/gpu: {num_proc_per_node}
                        requests:
                          nvidia.com/gpu: {num_proc_per_node}
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
