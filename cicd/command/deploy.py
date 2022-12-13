import subprocess
import sys
import click
import dagger
import docker
import docker.errors
import re
import logging


@click.command()
@click.option('--local', default=False, is_flag=True)
@click.option('--image-ref', default="ecowatt-twitter-bot")
def deploy(local, image_ref):
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        kustomize_file = f"./kustomize/prod.yaml"
        if local:
            kustomize_file = f"./kustomize/local.yaml"

        needed_files = ["kustomization.yaml", "deployment.yaml",
                        "./templates", "kubeconfig.yaml"] + [kustomize_file]

        dir = (client
               .host()
               .directory(".", include=needed_files))

        k8s = (client
               .container()
               .from_("alpine/k8s:1.23.13")
               .with_file("/root/.kube/config", dir.file("kubeconfig.yaml")))

        if local:
            k8s, image_ref = prepare_local_k8s(client, k8s)

        _ = (k8s
             .with_mounted_directory("/src", dir)
             .with_workdir("/src")
             .exec(["kustomize", "edit", "set", "image", "ecowatt-twitter-bot="+image_ref])
             .exec(["kustomize", "edit", "add", "patch", "--path", kustomize_file])
             .exec(["kubectl", "kustomize"])
             .exec(["kubectl", "apply", "-k", "."]).exit_code())


def prepare_local_k8s(client: dagger.Client, k8s: dagger.Container):

    docker_client = docker.from_env()

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
                    raise e

        elif container.name == "kind-control-plane":
            logging.info("Update kubeconfig with apiserver ip")
            api_server_ip = (docker.APIClient()
                             .inspect_network("kind")["Containers"][container.id]["IPv4Address"].split("/")[0])

            k8s = (k8s
                   .exec(["sed", "-i", f"s/kind-control-plane/{api_server_ip}/g", "/root/.kube/config"])
                   .exec(["cat", "/root/.kube/config"]))

    deploy_mock_server(docker_client, client, k8s)

    image_ref = load_image_into_kind(
        docker_client, "ecowatt-twitter-bot.tar", "ecowatt-twitter-bot")

    return k8s, image_ref


def deploy_mock_server(docker_client: docker.DockerClient, client: dagger.Client, k8s: dagger.Container):

    api_files = client.host().directory(
        "./mock", exclude=["__pycache__"])

    k8s_files = client.host().directory(
        "./mock", exclude=["__pycache__", ".py"])

    _ = (client
         .container()
         .from_("python:3.11.1-alpine3.17")
         .exec(["pip", "install", "fastapi", "uvicorn"])
         .with_file(".", api_files.file("main.py"))
         .with_entrypoint("uvicorn")
         .with_default_args(["main:app", "--host", "0.0.0.0"])
         .export("./mock/api.tar"))

    image_ref = load_image_into_kind(
        docker_client, "./mock/api.tar", "mock-api")

    _ = (k8s
         .with_mounted_directory("/src", k8s_files)
         .with_workdir("/src")
         .exec(["kustomize", "edit", "set", "image", "mock-api="+image_ref])
         .exec(["kubectl", "kustomize"])
         .exec(["kubectl", "apply", "-k", "."]).exit_code())


def load_image_into_kind(docker_client: docker.DockerClient, archive_path: str, name: str):
    logging.info(f"Loading {name} image into docker")
    image_ref = ""
    with open(archive_path, "rb") as image_binary:
        image = docker_client.images.load(image_binary.read())[0]
        image_name = "{}{}".format(name, image.short_id.split(":")[1])
        image.tag(image_name)

        logging.info(f"Loading {name} image into kind k8s")
        subprocess.run(
            ["kind", "load", "docker-image", image_name]).check_returncode()

        image_ref = f"docker.io/library/{image_name}"
    return image_ref


if __name__ == "__main__":

    sys.exit(deploy())
