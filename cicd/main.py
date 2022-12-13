import logging
import sys
import click
from command import deploy, build


@click.group()
def cli():
    pass


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format='%(levelname)s - %(message)s')
    cli.add_command(build.build)
    cli.add_command(deploy.deploy)
    cli()
