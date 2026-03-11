from aws_cdk import (
  Stack,
  CfnOutput,
  RemovalPolicy,
  Duration,
  aws_cognito as cognito,
  aws_certificatemanager as acm,
  aws_route53 as route53,
  aws_route53_targets as targets,
)
from constructs import Construct


class CognitoStack(Stack):

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    *,
    project: str,
    env_name: str,
    domain_name: str,
    cognito_auth_domain: str,
    cognito_certificate_arn: str,
    hosted_zone_name: str,
    **kwargs,
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Cognito User Pool
    user_pool = cognito.UserPool(
      self, "UserPool",
      user_pool_name=f"userpool-{project}-{env_name}-infra",
      self_sign_up_enabled=True,
      sign_in_aliases=cognito.SignInAliases(email=True),
      auto_verify=cognito.AutoVerifiedAttrs(email=True),
      password_policy=cognito.PasswordPolicy(
        min_length=8,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=True,
      ),
      account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
      removal_policy=RemovalPolicy.RETAIN,
      sign_in_case_sensitive=False,
    )

    # Cognito Custom Domain
    cognito_certificate = acm.Certificate.from_certificate_arn(
      self, "CognitoCertificate", cognito_certificate_arn,
    )
    user_pool_domain = user_pool.add_domain(
      "CognitoDomain",
      custom_domain=cognito.CustomDomainOptions(
        domain_name=cognito_auth_domain,
        certificate=cognito_certificate,
      ),
    )

    # Route 53 Alias Record for Cognito Custom Domain
    hosted_zone = route53.HostedZone.from_lookup(
      self, "HostedZone",
      domain_name=hosted_zone_name,
    )
    route53.ARecord(
      self, "CognitoAliasRecord",
      zone=hosted_zone,
      record_name=cognito_auth_domain,
      target=route53.RecordTarget.from_alias(
        targets.UserPoolDomainTarget(user_pool_domain),
      ),
    )

    # User Pool Client (SPA - no secret, Authorization Code + PKCE)
    callback_url = f"https://{domain_name}/callback"
    logout_url = f"https://{domain_name}/"

    user_pool_client = user_pool.add_client(
      "UserPoolClient",
      user_pool_client_name=f"client-{project}-{env_name}-infra",
      generate_secret=False,
      auth_flows=cognito.AuthFlow(
        user_password=False,
        user_srp=False,
        admin_user_password=True,
      ),
      o_auth=cognito.OAuthSettings(
        flows=cognito.OAuthFlows(
          authorization_code_grant=True,
        ),
        scopes=[
          cognito.OAuthScope.OPENID,
          cognito.OAuthScope.EMAIL,
          cognito.OAuthScope.PROFILE,
          cognito.OAuthScope.COGNITO_ADMIN,
        ],
        callback_urls=[callback_url],
        logout_urls=[logout_url],
      ),
      supported_identity_providers=[
        cognito.UserPoolClientIdentityProvider.COGNITO,
      ],
      access_token_validity=Duration.hours(1),
      id_token_validity=Duration.hours(1),
      refresh_token_validity=Duration.days(30),
      enable_token_revocation=True,
      prevent_user_existence_errors=True,
    )

    # CloudFormation Exports
    CfnOutput(
      self, "CognitoUserPoolArn",
      value=user_pool.user_pool_arn,
      export_name=f"{project}-{env_name}-infra-CognitoUserPoolArn",
    )
    CfnOutput(
      self, "CognitoUserPoolId",
      value=user_pool.user_pool_id,
      export_name=f"{project}-{env_name}-infra-CognitoUserPoolId",
    )
    CfnOutput(
      self, "CognitoClientId",
      value=user_pool_client.user_pool_client_id,
      export_name=f"{project}-{env_name}-infra-CognitoClientId",
    )
    CfnOutput(
      self, "CognitoDomain",
      value=cognito_auth_domain,
      export_name=f"{project}-{env_name}-infra-CognitoDomain",
    )
