"""
AWS CDK Stack — Auditoria (site estático, deploy exclusivo)
Provisiona:
  - S3 bucket privado para os arquivos estáticos da pasta auditoria/
  - CloudFront distribution (HTTPS, domínio customizado)
  - Certificado ACM com validação DNS via Route53
  - Registro A no Route53 apontando para o CloudFront

Domínio raiz: planlogweb.com.br (hosted zone existente)
Subdomínio:   auditoria5s.planlogweb.com.br (produção)
              staging.auditoria5s.planlogweb.com.br (staging)

Totalmente isolado da DashboardsStack: bucket, distribuição e domínio próprios.
"""
from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    aws_certificatemanager as acm,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_route53 as route53,
    aws_route53_targets as route53_targets,
    aws_s3 as s3,
)
from constructs import Construct

HOSTED_ZONE_DOMAIN = "planlogweb.com.br"
SUBDOMAIN = "auditoria5s"


class AuditoriaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "production", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        prefix = f"auditoria-{env_name}"
        domain_prefix = "staging." if env_name == "staging" else ""
        full_domain = f"{domain_prefix}{SUBDOMAIN}.{HOSTED_ZONE_DOMAIN}"

        # ------------------------------------------------------------------
        # S3 — bucket privado dos arquivos estáticos
        # ------------------------------------------------------------------
        self.site_bucket = s3.Bucket(
            self, "SiteBucket",
            bucket_name=f"{prefix}-web",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # ------------------------------------------------------------------
        # Route53 + ACM
        # ------------------------------------------------------------------
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=HOSTED_ZONE_DOMAIN,
        )

        certificate = acm.Certificate(
            self, "Certificate",
            domain_name=full_domain,
            validation=acm.CertificateValidation.from_dns(hosted_zone),
        )

        # ------------------------------------------------------------------
        # CloudFront — CDN com HTTPS na frente do bucket
        # ------------------------------------------------------------------
        self.distribution = cloudfront.Distribution(
            self, "Distribution",
            domain_names=[full_domain],
            certificate=certificate,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=404,
                    response_page_path="/index.html",
                    ttl=Duration.seconds(0),
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # Américas + Europa
        )

        route53.ARecord(
            self, "ARecord",
            zone=hosted_zone,
            record_name=f"{domain_prefix}{SUBDOMAIN}",
            target=route53.RecordTarget.from_alias(
                route53_targets.CloudFrontTarget(self.distribution)
            ),
        )

        CfnOutput(self, "SiteBucketName", value=self.site_bucket.bucket_name)
        CfnOutput(self, "CloudFrontDistributionId", value=self.distribution.distribution_id)
        CfnOutput(self, "CloudFrontDomain", value=self.distribution.distribution_domain_name)
        CfnOutput(self, "SiteCustomDomain", value=f"https://{full_domain}")
