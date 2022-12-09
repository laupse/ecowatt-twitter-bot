import os
import sys
import dagger


def main():
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:

        if len(sys.argv) == 2 and sys.argv[1] == "--push":
            final = build(client, export_archive=False)

            image_ref = os.getenv("IMAGE_REF")
            if image_ref is not None:
                final.publish(image_ref)
                return 0

            image_registry = os.getenv("IMAGE_REGISTRY")
            image_tag = os.getenv("IMAGE_TAG")
            if image_registry is not None:
                final.publish(image_ref.format(
                    "%s/ecowatt-twitter-bot:%s", image_registry, image_tag))
                return 0

            print("IMAGE_REF or IMAGE_REGISTRY+IMAGE_TAG env is required")
            return 1

        final = build(client)
        return 0


def build(client: dagger.Client, export_archive=True):
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
             .exec(["ln", "-s", "/usr/share/zoneinfo/Europe/Paris /etc/localtime"])
             .with_file(".", executable)
             .with_entrypoint("/ecowatt-twitter-bot"))
    if export_archive:
        final.export("ecowatt-twitter-bot.tar.gz")

    return final


if __name__ == "__main__":
    sys.exit(main())