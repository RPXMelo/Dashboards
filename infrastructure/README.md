# Infraestrutura — Dashboards

CDK (Python) que provisiona a hospedagem estática deste site: S3 (privado) + CloudFront + Route53 + ACM.

Domínio: `dashboards.planlogweb.com.br` (produção) / `staging.dashboards.planlogweb.com.br` (staging).
Para trocar o domínio ou a hosted zone, edite `HOSTED_ZONE_DOMAIN` e `SUBDOMAIN` em `stacks/dashboards_stack.py`.

## Pré-requisitos únicos (antes do primeiro deploy)

1. A hosted zone `planlogweb.com.br` já precisa existir no Route53 da conta AWS de destino.
2. No GitHub, configure em **Settings → Secrets and variables → Actions**:
   - **Preferencial:** `AWS_ROLE_TO_ASSUME` (secret ou variable) para autenticação via OIDC.
   - **Alternativa:** `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`.

   A role/usuário IAM correspondente precisa de permissão para: S3, CloudFront, ACM, Route53, e para o bootstrap do CDK (CloudFormation, SSM, IAM — geralmente via policy `AdministratorAccess` ou uma policy dedicada ao CDK).

## Deploy

- Push em `main` → stack `Dashboards-Production`, domínio `dashboards.planlogweb.com.br`.
- Push em `develop` → stack `Dashboards-Staging`, domínio `staging.dashboards.planlogweb.com.br`.

O workflow `.github/workflows/deploy.yml` faz: `cdk deploy` (cria/atualiza infra) → `aws s3 sync` (publica os arquivos) → invalidação do CloudFront.

## Deploy manual (local)

```bash
cd infrastructure
pip install -r requirements.txt
npm install -g aws-cdk

cdk bootstrap aws://<ACCOUNT_ID>/us-east-1
cdk deploy --context env=production   # ou env=staging
```
