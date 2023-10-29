#!/usr/bin/env python3

from aws_cdk import App, Environment
from stacks.qsmr_ecr_stack import EcsStepFunctionStack

app = App()
env_EU = Environment(account="991049544436", region="eu-north-1")
EcsStepFunctionStack(app, env=env_EU)

app.synth()
