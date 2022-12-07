import os
import sys
import anyio
import dagger


def build():
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        cargo = client.host().directory(
            ".", include=["Cargo*"])

        build = (client
                 .container()
                 .from_("rust:1.63.0")
                 .with_env_variable("USER", "root")
                 .exec(["cargo", "new", "--bin", "ecowatt-twitter-bot"]))

        build = (build
                 .with_workdir("/ecowatt-twitter-bot")
                 .with_directory(".", cargo)
                 .exec(["cargo", "build", "--release"]))

        src = (client
               .host()
               .directory(".", include=["src"]))

        executable = (build
                      .with_directory(".", src)
                      .exec(["cargo", "build", "--release"])
                      .file("/ecowatt-twitter-bot/target/release/ecowatt-twitter-bot"))

        final = (client.container()
                 .from_("rust:1.63.0-slim")
                 .exec(["apt-get update"])
                 .exec(["apt-get", "install", "-y", "dialog", "apt-utils", "tzdata"])
                 .exec(["rm", "/etc/localtime"])
                 .exec(["ln", "-s", "/usr/share/zoneinfo/Europe/Paris /etc/localtime"])
                 .with_file(".", executable))

        image_ref = os.getenv("IMAGE_REF")
        if image_ref is not None:
            str = final.publish(image_ref)
            return

        image_registry = os.getenv("IMAGE_REGISTRY")
        image_tag = os.getenv("IMAGE_TAG")
        if image_registry is not None:
            build.publish(image_ref.format(
                "%s/ecowatt-twitter-bot:%s", image_registry, image_tag))


if __name__ == "__main__":
    build()
