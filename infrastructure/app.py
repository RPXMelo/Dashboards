#!/usr/bin/env python3
import aws_cdk as cdk

from stacks.dashboards_stack import DashboardsStack

app = cdk.App()

env_name = app.node.try_get_context("env") or "production"
stack_name = "Dashboards-Production" if env_name == "production" else "Dashboards-Staging"

DashboardsStack(
    app,
    stack_name,
    env_name=env_name,
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region="us-east-1",
    ),
)

app.synth()
