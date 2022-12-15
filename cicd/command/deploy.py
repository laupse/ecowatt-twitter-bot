import os
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
@click.option('--gke', default=False, is_flag=True)
@click.option('--gke-project-id', envvar="GKE_PROJECT_ID")
@click.option('--gke-cluster-name', envvar="GKE_CLUSTER_NAME")
@click.option('--gke-zone', envvar="GKE_ZONE",  default="europe-west1-b")
@click.option('--dry-run', default=False, is_flag=True)
@click.option('--image-ref', default="ecowatt-twitter-bot", envvar="IMAGE_REF")
def deploy(local, gke, gke_project_id, gke_cluster_name, gke_zone, dry_run, image_ref):
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        kustomize_file = f"./kustomize/prod.yaml"
        if local:
            kustomize_file = f"./kustomize/local.yaml"

        needed_files = ["kustomization.yaml", "deployment.yaml",
                        "./templates"] + [kustomize_file]
        if not gke:
            needed_files.append("kubeconfig.yaml")

        dir = (client
               .host()
               .directory(".", include=needed_files))

        k8s = client.container()

        if not gke or local:
            k8s = (k8s
                   .from_("alpine:k8s:1.25.0")
                   .with_file("/root/.kube/config", dir.file("kubeconfig.yaml")))

        if local:
            k8s, image_ref = prepare_local_k8s(client, k8s)

        if gke:
            k8s = (k8s
                   .from_("google/cloud-sdk:412.0.0")
                   .with_new_file("creds.json", os.environ["GCP_CREDENTIALS"])
                   .exec(["curl", "-LO", "https://dl.k8s.io/release/v1.23.11/bin/linux/amd64/kubectl"])
                   .exec(["install", "-o", "root", "-g", "root", "-m", "0755", "kubectl", "/usr/local/bin/kubectl"])
                   .exec(["curl",  "-LO", "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v4.5.7/kustomize_v4.5.7_linux_amd64.tar.gz"])
                   .exec(["tar",  "-xzf", "kustomize_v4.5.7_linux_amd64.tar.gz"])
                   .exec(["install", "-o", "root", "-g", "root", "-m", "0755", "kustomize", "/usr/local/bin/kustomize"])
                   .exec(["gcloud", "config", "set", "project", gke_project_id])
                   .exec(["gcloud", "auth", "login", "--cred-file", "creds.json"])
                   .exec(["gcloud", "container", "clusters", "get-credentials", gke_cluster_name, "--zone", gke_zone, "--project", gke_project_id]))

        k8s = (k8s
               .with_mounted_directory("/src", dir)
               .with_workdir("/src")
               .exec(["kustomize", "edit", "set", "image", "ecowatt-twitter-bot="+image_ref])
               .exec(["kustomize", "edit", "add", "patch", "--path", kustomize_file]))
        if dry_run:
            _ = (k8s
                 .exec(["kubectl", "apply", "-k", ".", "--dry-run=server"])
                 .exit_code())
            return

        _ = k8s.exec(["kubectl", "apply", "-k", "."]).exit_code()


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
