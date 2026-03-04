#!/usr/bin/env python3
import os

import aws_cdk as cdk

from stacks import CognitoStack, DistributionStack

account = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION", "ap-northeast-1")
env_name = os.environ["ENV"]
project = "sgp"

domain_name = os.environ["DOMAIN_NAME"]
acm_certificate_arn = os.environ["ACM_CERTIFICATE_ARN"]
hosted_zone_name = os.environ["HOSTED_ZONE_NAME"]
cognito_domain_prefix = os.environ["COGNITO_DOMAIN_PREFIX"]

app = cdk.App()

# Stack 1: Cognito (deploy before backends)
cognito_stack = CognitoStack(
  app,
  f"stack-{project}-{env_name}-infra-cognito",
  project=project,
  env_name=env_name,
  domain_name=domain_name,
  cognito_domain_prefix=cognito_domain_prefix,
  env=cdk.Environment(account=account, region=region),
  description="Cognito User Pool for ShogiProject",
)

# Stack 2: Distribution (deploy after backends)
distribution_stack = DistributionStack(
  app,
  f"stack-{project}-{env_name}-infra-distribution",
  project=project,
  env_name=env_name,
  domain_name=domain_name,
  acm_certificate_arn=acm_certificate_arn,
  hosted_zone_name=hosted_zone_name,
  env=cdk.Environment(account=account, region=region),
  description="S3 + CloudFront + Route 53 for ShogiProject",
)

app.synth()
