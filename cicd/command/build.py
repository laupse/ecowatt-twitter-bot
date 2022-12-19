import sys
import click
import dagger


def publish(final: dagger.Container, image_ref, image_registry, image_tag):
    if image_ref is not None:
        final.publish(image_ref)
        return

    if image_registry is not None and image_tag is not None:
        final.publish(f"{image_registry}/ecowatt-twitter-bot:{image_tag}")
        return

    print("image is not be push IMAGE_REF or IMAGE_REGISTRY+IMAGE_TAG env is required")
    sys.exit(1)


@click.command()
@click.option('--export-archive', default=True, is_flag=True)
@click.option('--push', default=False, is_flag=True)
@click.option('--image-ref', default=None, envvar="IMAGE_REF")
@click.option('--image-registry', default=None, envvar="IMAGE_REGISTRY")
@click.option('--image-tag', default=None, envvar="IMAGE_TAG")
def build(export_archive, push, image_ref, image_registry, image_tag):
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:

        src = (client
               .host()
               .directory(".", include=["Cargo*", "./src"]))

        build = (client
                 .container()
                 .from_("rust:1.63.0")
                 .with_env_variable("USER", "root")
                 .with_workdir("/ecowatt-twitter-bot")
                 .with_directory(".", src)
                 .exec(["cargo", "build", "--release"]))

        executable = (build.file(
            "/ecowatt-twitter-bot/target/release/ecowatt-twitter-bot"))

        final = (client.container()
                 .from_("rust:1.63.0-slim")
                 .exec(["apt-get", "update"])
                 .exec(["apt-get", "install", "-y", "dialog", "apt-utils", "tzdata"])
                 .exec(["rm", "/etc/localtime"])
                 .exec(["ln", "-s", "/usr/share/zoneinfo/Europe/Paris", "/etc/localtime"])
                 .with_file(".", executable)
                 .with_entrypoint("/ecowatt-twitter-bot"))
        if export_archive and not push:
            final.export("ecowatt-twitter-bot.tar.gz")

        if push:
            publish(final, image_ref, image_registry, image_tag)

        return final
