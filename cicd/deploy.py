import os
import sys
import dagger


def deploy():
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        image_ref = os.getenv("IMAGE_REF")
        if image_ref is None:
            print("IMAGE_REF env is required")
            return 1

        kustomize_file = os.getenv("KUSTOMIZE_FILE_PATH")
        if kustomize_file is None:
            kustomize_file = "./kustomize/local.yaml"

        needed_files = ["kustomization.yaml", "deployment.yaml",
                        "./templates", "kubeconfig.yaml"] + [kustomize_file]

        dir = client.host().directory(
            ".", include=needed_files)

        kubectl = (client
                   .container()
                   .from_("alpine/k8s:1.23.13")
                   .with_file("/root/.kube/config", dir.file("kubeconfig.yaml"))
                   .with_mounted_directory("/src", dir)
                   .with_workdir("/src")
                   .exec(["kustomize", "edit", "set", "image", "ecowatt-twitter-bot="+image_ref])
                   .exec(["kustomize", "edit", "add", "patch", "--path", kustomize_file])
                   .exec(["kubectl", "kustomize"])
                   .exec(["kubectl", "apply", "-k", "."]).exit_code())

        return 0


if __name__ == "__main__":
    sys.exit(deploy())
