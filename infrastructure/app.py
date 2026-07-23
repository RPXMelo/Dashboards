#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks.auditoria_stack import AuditoriaStack
from stacks.dashboards_stack import DashboardsStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "production"
env_suffix = "Production" if env_name == "production" else "Staging"

cdk_env = cdk.Environment(
    account=app.node.try_get_context("account") or os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# Stack principal — serve todo o repositório (exceto auditoria/, que tem stack própria)
DashboardsStack(
    app,
    f"Dashboards-{env_suffix}",
    env_name=env_name,
    env=cdk_env,
)

# Stack exclusiva da pasta auditoria/ — bucket, CloudFront e subdomínio próprios,
# deployada isoladamente pelo workflow deploy-auditoria.yml
AuditoriaStack(
    app,
    f"Auditoria-{env_suffix}",
    env_name=env_name,
    env=cdk_env,
)

app.synth()
