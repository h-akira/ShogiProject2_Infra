#!/usr/bin/env python3
import os

import aws_cdk as cdk
from aws_cdk import DefaultStackSynthesizer

from stacks import CognitoStack, DistributionStack

account = os.getenv("CDK_DEFAULT_ACCOUNT")
region = os.getenv("CDK_DEFAULT_REGION", "ap-northeast-1")
env_name = os.environ["ENV"]
project = "sgp"

domain_name = os.environ["DOMAIN_NAME"]
acm_certificate_arn = os.environ["ACM_CERTIFICATE_ARN"]
hosted_zone_name = os.environ["HOSTED_ZONE_NAME"]
cognito_auth_domain = os.environ["COGNITO_AUTH_DOMAIN"]
cognito_certificate_arn = os.environ["COGNITO_CERTIFICATE_ARN"]

app = cdk.App()

# CDK context: バックエンドがデプロイ済みかどうか
# buildspec.yml から -c backends_deployed=true/false で渡される
backends_deployed = app.node.try_get_context("backends_deployed") == "true"

synthesizer = DefaultStackSynthesizer(
  qualifier=env_name,  # "dev" or "pro"
)

# Stack 1: Distribution (S3 + CloudFront + Route 53)
# バックエンド未デプロイ時は S3 オリジンのみ、デプロイ済みなら API Gateway オリジンも追加
distribution_stack = DistributionStack(
  app,
  f"stack-{project}-{env_name}-infra-distribution",
  project=project,
  env_name=env_name,
  domain_name=domain_name,
  acm_certificate_arn=acm_certificate_arn,
  hosted_zone_name=hosted_zone_name,
  backends_deployed=backends_deployed,
  synthesizer=DefaultStackSynthesizer(qualifier=env_name),
  env=cdk.Environment(account=account, region=region),
  description="S3 + CloudFront + Route 53 for ShogiProject",
)

# Stack 2: Cognito (親ドメインの A レコードが必要なので Distribution の後)
cognito_stack = CognitoStack(
  app,
  f"stack-{project}-{env_name}-infra-cognito",
  project=project,
  env_name=env_name,
  domain_name=domain_name,
  cognito_auth_domain=cognito_auth_domain,
  cognito_certificate_arn=cognito_certificate_arn,
  synthesizer=synthesizer,
  env=cdk.Environment(account=account, region=region),
  description="Cognito User Pool for ShogiProject",
)
cognito_stack.add_dependency(distribution_stack)

app.synth()
