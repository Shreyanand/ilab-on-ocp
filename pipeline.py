# type: ignore
# pylint: disable=no-value-for-parameter,import-outside-toplevel,import-error,no-member
from typing import List, Literal, Optional
import click
from kfp import dsl, compiler
from kfp.kubernetes import (
    use_config_map_as_env,
    use_secret_as_env,
    CreatePVC,
    DeletePVC,
    mount_pvc,
)

K8S_NAME = "kfp-model-server"
MOCKED_STAGES = ["sdg", "train", "eval"]


def pipeline_wrapper(mock: List[Literal[MOCKED_STAGES]]):
    """Wrapper for KFP pipeline, which allows for mocking individual stages."""

    # Imports for SDG stage
    if "sdg" in mock:
        from sdg.faked import git_clone_op, sdg_op
    else:
        from sdg import git_clone_op, sdg_op

    # Imports for Training stage
    from utils import artifact_to_pvc_op

    if "train" in mock:
        from training.faked import pytorchjob_manifest_op
        from utils.faked import kubectl_apply_op, kubectl_wait_for_op
    else:
        from training import pytorchjob_manifest_op
        from utils import kubectl_apply_op, kubectl_wait_for_op

    @dsl.pipeline(
        display_name="InstructLab",
        name="instructlab",
        description="InstructLab pipeline",
    )
    def pipeline(
        num_instructions_to_generate: int = 2,
        repo_url: str = "https://github.com/instructlab/taxonomy.git",
        repo_branch: Optional[str] = None,
        repo_pr: Optional[int] = None,
        storage_class_name: str = "ocs-external-storagecluster-ceph-rbd",
    ):

        # SDG stage
        git_clone_task = git_clone_op(
            repo_branch=repo_branch, repo_pr=repo_pr, repo_url=repo_url
        )

        sdg_task = sdg_op(
            num_instructions_to_generate=num_instructions_to_generate,
            taxonomy=git_clone_task.outputs["taxonomy"],
            repo_branch=repo_branch,
            repo_pr=repo_pr,
        )
        use_config_map_as_env(
            sdg_task, K8S_NAME, dict(endpoint="endpoint", model="model")
        )
        use_secret_as_env(sdg_task, K8S_NAME, {"api_key": "api_key"})

        # Training stage
        # We need to pass storage_class_name since 'standard'  !=  default storage class
        # https://github.com/kubeflow/pipelines/blob/1cded35cf5e93d8c8d32fefbddceb2eed8de9a0a/backend/src/v2/driver/driver.go#L1428-L1436
        # At least we made it a pipeline parameter
        # FIXME: change `ReadWriteOnce` to `ReadWriteMany` once we can provision Filesystem as this access_mode
        pvc_create_task = CreatePVC(
            pvc_name_suffix="-train",
            access_modes=["ReadWriteOnce"],
            size="1Gi",
            storage_class_name=storage_class_name,
        )

        artifact_to_pvc_task = artifact_to_pvc_op(data=sdg_task.outputs["sdg"], pvc_path="/data")
        mount_pvc(task=artifact_to_pvc_task, pvc_name=pvc_create_task.output, mount_path="/data/")

        # Using pvc_create_task.output as PyTorchJob name since dsl.PIPELINE_* global variables do not template/work in KFP v2
        # https://github.com/kubeflow/pipelines/issues/10453
        pytorchjob_manifest_task = pytorchjob_manifest_op(
            pvc_name=pvc_create_task.output, name_suffix=pvc_create_task.output
        )

        kubectl_apply_task = kubectl_apply_op(manifest=pytorchjob_manifest_task.outputs['manifest'])
        kubectl_apply_task.after(artifact_to_pvc_task)
        kubectl_apply_task.set_caching_options(False)

        kubectl_wait_task = kubectl_wait_for_op(
            condition="condition=Succeeded",
            kind="pytorchjobs",
            name=pytorchjob_manifest_task.outputs['name'],
        )
        kubectl_wait_task.after(kubectl_apply_task)
        kubectl_wait_task.set_caching_options(False)

        pvc_delete_task = DeletePVC(pvc_name=pvc_create_task.output)
        pvc_delete_task.after(kubectl_wait_task)

        return

    return pipeline


@click.command()
@click.option(
    "--mock",
    type=click.Choice(MOCKED_STAGES, case_sensitive=False),
    help="Mock part of the pipeline",
    multiple=True,
    default=[],
)
def cli(mock):

    p = pipeline_wrapper(mock)

    with click.progressbar(length=1, label="Generating pipeline") as bar:
        compiler.Compiler().compile(p, "pipeline.yaml")
        bar.update(1)


if __name__ == "__main__":
    cli()
