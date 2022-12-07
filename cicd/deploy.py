import os
import sys
import dagger


def deploy():
    with dagger.Connection(dagger.Config(log_output=sys.stdout, execute_timeout=1800)) as client:
        image_ref = os.getenv("IMAGE_REF")
        if image_ref is None:
            print("IMAGE_REF env is required")
            return 1

        dir = client.host().directory(
            ".", include=["*.yml", "*.yaml", "./templates"])

        kubectl = (client
                   .container()
                   .from_("alpine/k8s:1.23.13")
                   .with_file("/root/.kube/config", dir.file("kubeconfig.yaml")))

        daily_template = dir.file("/templates/daily_prevision_tweet.j2")
        template = dir.file("/templates/prevision_tweet.j2")
        deploy_template = dir.file("deploy.template.yml")

        _ = (kubectl
             .exec(["kubectl", "delete", "configmap", "ecowatt-twitter-bot-template", "--ignore-not-found=true"])
             .exit_code())

        _ = (kubectl
             .with_file("daily_prevision_tweet.j2", daily_template)
             .with_file("prevision_tweet.j2", template)
             .exec(["kubectl", "create", "configmap", "ecowatt-twitter-bot-template", "--from-file=daily_prevision_tweet.j2", "--from-file=prevision_tweet.j2"])
             .exit_code())

        deployment = (client.container().from_("alpine:3.15")
                      .with_file(".", deploy_template)
                      .exec(["sed", f"s/IMAGE_REF/{image_ref}/g", "deploy.template.yml"]).stdout())
        _ = (kubectl
             .with_file("deploy.template.yml", deployment)
             .exec(["kubectl", "apply", "-f", "deploy.template.yml"])
             .exit_code())


if __name__ == "__main__":
    sys.exit(deploy())
