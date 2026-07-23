"""
AWS CDK Stack — Dashboards (site estático)
Provisiona:
  - S3 bucket privado para os arquivos estáticos
  - CloudFront distribution (HTTPS, domínio customizado)
  - Certificado ACM com validação DNS via Route53
  - Registro A no Route53 apontando para o CloudFront

Domínio raiz: planlogweb.com.br (hosted zone existente)
Subdomínio:   dashboards.planlogweb.com.br (produção)
              staging.dashboards.planlogweb.com.br (staging)
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
SUBDOMAIN = "dashboards"

# Restringe o embed da distribuição a iframes do Google Sites via CSP
# frame-ancestors (aplicado pelo navegador com base na origem real do
# documento pai — não depende de headers enviados pelo Google Sites).
ALLOWED_FRAME_ANCESTOR = "https://sites.google.com"


class DashboardsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_name: str = "production", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = env_name
        prefix = f"dashboards-{env_name}"
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
        # Impede que o site seja embutido em iframe fora do Google Sites.
        frame_ancestors_policy = cloudfront.ResponseHeadersPolicy(
            self, "FrameAncestorsPolicy",
            response_headers_policy_name=f"{prefix}-frame-ancestors",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                content_security_policy=cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy=f"frame-ancestors {ALLOWED_FRAME_ANCESTOR};",
                    override=True,
                ),
            ),
        )

        self.distribution = cloudfront.Distribution(
            self, "Distribution",
            domain_names=[full_domain],
            certificate=certificate,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.site_bucket),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=frame_ancestors_policy,
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
