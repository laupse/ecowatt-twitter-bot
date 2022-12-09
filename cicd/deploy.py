import os
import subprocess
import sys
import dagger
import docker
import docker.errors
import re
import logging


def deploy():
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        env = os.getenv("ENV")
        if env is None:
            logging.info("ENV env var is required")
            return 1

        image_ref = os.getenv("IMAGE_REF")
        if image_ref is None and env == "prod":
            logging.info("IMAGE_REF env var is required in prod")
            return 1

        kustomize_file = f"./kustomize/{env}.yaml"

        needed_files = ["kustomization.yaml", "deployment.yaml",
                        "./templates", "kubeconfig.yaml"] + [kustomize_file]

        dir = client.host().directory(
            ".", include=needed_files)

        k8s = (client
               .container()
               .from_("alpine/k8s:1.23.13")
               .with_file("/root/.kube/config", dir.file("kubeconfig.yaml")))

        if env == "local":
            docker_client = docker.from_env()

            logging.info("Loading image into docker")
            with open("ecowatt-twitter-bot.tar.gz", "rb") as image:
                image = docker_client.images.load(image.read())[0]
                image_id = image.short_id.split(":")[1]
                image.tag(f"ecowatt-twitter-bot{image_id}")

                subprocess.run(
                    ["kind", "load", "docker-image", f"ecowatt-twitter-bot{image_id}"]).check_returncode()

                image_ref = f"docker.io/library/ecowatt-twitter-bot{image_id}"

            kind_network = docker_client.networks.get("kind")

            for container in docker_client.containers.list():
                if re.search("dagger-engine-.*", container.name):
                    logging.info("Connecting dagger to kind network")
                    try:
                        kind_network.connect(container.name)
                    except docker.errors.APIError as e:
                        logging.debug(e.explanation)
                        if e.explanation != "endpoint with name {} already exists in network kind".format(container.name):
                            logging.error("Error when connecting to kind")
                            return 1

                elif container.name == "kind-control-plane":
                    api_server_ip = (docker.APIClient()
                                     .inspect_network("kind")["Containers"][container.id]["IPv4Address"].split("/")[0])

                    k8s = (k8s
                           .exec(["sed", "-i", f"s/kind-control-plane/{api_server_ip}/g", "/root/.kube/config"])
                           .exec(["cat", "/root/.kube/config"]))
                    break

        return (k8s
                .with_mounted_directory("/src", dir)
                .with_workdir("/src")
                .exec(["kustomize", "edit", "set", "image", "ecowatt-twitter-bot="+image_ref])
                .exec(["kustomize", "edit", "add", "patch", "--path", kustomize_file])
                .exec(["kubectl", "kustomize"])
                .exec(["kubectl", "apply", "-k", "."]).exit_code())


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    sys.exit(deploy())
