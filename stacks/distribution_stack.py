from aws_cdk import (
  Stack,
  Fn,
  CfnOutput,
  RemovalPolicy,
  aws_s3 as s3,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as origins,
  aws_certificatemanager as acm,
  aws_route53 as route53,
  aws_route53_targets as targets,
)
from constructs import Construct


class DistributionStack(Stack):

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    *,
    project: str,
    env_name: str,
    domain_name: str,
    acm_certificate_arn: str,
    hosted_zone_name: str,
    backends_deployed: bool = False,
    allowed_ips: str = "",
    **kwargs,
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # S3 Bucket for frontend static files
    bucket = s3.Bucket(
      self, "FrontendBucket",
      bucket_name=f"s3-{project}-{env_name}-infra-frontend",
      removal_policy=RemovalPolicy.RETAIN,
      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
    )

    # ACM Certificate (us-east-1)
    certificate = acm.Certificate.from_certificate_arn(
      self, "Certificate", acm_certificate_arn,
    )

    # API Gateway origins (conditional)
    additional_behaviors = {}
    if backends_deployed:
      main_api_id = Fn.import_value(
        f"{project}-{env_name}-backend-main-ApiGatewayId"
      )
      main_api_stage = Fn.import_value(
        f"{project}-{env_name}-backend-main-ApiGatewayStageName"
      )
      analysis_api_id = Fn.import_value(
        f"{project}-{env_name}-backend-analysis-ApiGatewayId"
      )
      analysis_api_stage = Fn.import_value(
        f"{project}-{env_name}-backend-analysis-ApiGatewayStageName"
      )

      region = Stack.of(self).region
      main_api_origin = origins.HttpOrigin(
        Fn.join("", [main_api_id, ".execute-api.", region, ".amazonaws.com"]),
        origin_path=Fn.join("", ["/", main_api_stage]),
      )
      analysis_api_origin = origins.HttpOrigin(
        Fn.join("", [analysis_api_id, ".execute-api.", region, ".amazonaws.com"]),
        origin_path=Fn.join("", ["/", analysis_api_stage]),
      )

      additional_behaviors = {
        "/api/v1/main/*": cloudfront.BehaviorOptions(
          origin=main_api_origin,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
          cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
          origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        ),
        "/api/v1/analysis/*": cloudfront.BehaviorOptions(
          origin=analysis_api_origin,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
          cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
          origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        ),
      }

    # 許可IPリストを生成
    ip_list = [ip.strip() for ip in allowed_ips.split(",") if ip.strip()] if allowed_ips else []

    # CloudFront Functions: IP制限 + SPA fallback
    if ip_list:
      ip_array_js = ",".join(f"'{ip}'" for ip in ip_list)
      ip_check_code = (
        f"var allowedIps=[{ip_array_js}];"
        "var ip=event.viewer.ip;"
        "if(allowedIps.indexOf(ip)===-1){"
        "return{statusCode:403,statusDescription:'Forbidden',"
        "body:{encoding:'text',data:'Access Denied'}};"
        "}"
      )
    else:
      ip_check_code = ""

    spa_rewrite_function = cloudfront.Function(
      self, "SpaRewriteFunction",
      function_name=f"cf-func-{project}-{env_name}-spa-rewrite",
      code=cloudfront.FunctionCode.from_inline(
        "function handler(event){"
        "var request=event.request;"
        f"{ip_check_code}"
        "var uri=request.uri;"
        "if(!uri.startsWith('/api/')&&!uri.includes('.')){"
        "request.uri='/index.html';"
        "}"
        "return request;"
        "}"
      ),
    )

    # CloudFront Distribution
    distribution = cloudfront.Distribution(
      self, "Distribution",
      default_behavior=cloudfront.BehaviorOptions(
        origin=origins.S3BucketOrigin.with_origin_access_control(bucket),
        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        function_associations=[
          cloudfront.FunctionAssociation(
            function=spa_rewrite_function,
            event_type=cloudfront.FunctionEventType.VIEWER_REQUEST,
          ),
        ],
      ),
      additional_behaviors=additional_behaviors if additional_behaviors else None,
      domain_names=[domain_name],
      certificate=certificate,
      default_root_object="index.html",
    )

    # Route 53 Alias Record
    hosted_zone = route53.HostedZone.from_lookup(
      self, "HostedZone",
      domain_name=hosted_zone_name,
    )
    route53.ARecord(
      self, "AliasRecord",
      zone=hosted_zone,
      record_name=domain_name,
      target=route53.RecordTarget.from_alias(
        targets.CloudFrontTarget(distribution),
      ),
    )

    # CloudFormation Exports
    CfnOutput(
      self, "S3BucketName",
      value=bucket.bucket_name,
      export_name=f"{project}-{env_name}-infra-S3BucketName",
    )
    CfnOutput(
      self, "CloudFrontDistributionId",
      value=distribution.distribution_id,
      export_name=f"{project}-{env_name}-infra-CloudFrontDistributionId",
    )
    CfnOutput(
      self, "DomainName",
      value=domain_name,
      export_name=f"{project}-{env_name}-infra-DomainName",
    )
