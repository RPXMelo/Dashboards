# Infraestrutura — Dashboards

CDK (Python) que provisiona a hospedagem estática deste site: S3 (privado) + CloudFront + Route53 + ACM.

Duas stacks independentes, cada uma com bucket, distribuição CloudFront e subdomínio próprios:

| Stack                 | Conteúdo servido      | Domínio (produção)                | Domínio (staging)                          |
|------------------------|------------------------|------------------------------------|---------------------------------------------|
| `Dashboards-*`         | Todo o repo, exceto `auditoria/` | `dashboards.planlogweb.com.br`     | `staging.dashboards.planlogweb.com.br`       |
| `Auditoria-*`          | Apenas a pasta `auditoria/`      | `auditoria5s.planlogweb.com.br`    | `staging.auditoria5s.planlogweb.com.br`      |

Para trocar domínio ou hosted zone, edite `HOSTED_ZONE_DOMAIN`/`SUBDOMAIN` em `stacks/dashboards_stack.py` ou `stacks/auditoria_stack.py`, conforme o caso.

## Pré-requisitos únicos (antes do primeiro deploy)

1. A hosted zone `planlogweb.com.br` já precisa existir no Route53 da conta AWS de destino.
2. No GitHub, configure em **Settings → Secrets and variables → Actions**:
   - **Preferencial:** `AWS_ROLE_TO_ASSUME` (secret ou variable) para autenticação via OIDC.
   - **Alternativa:** `AWS_ACCESS_KEY_ID` e `AWS_SECRET_ACCESS_KEY`.

   A role/usuário IAM correspondente precisa de permissão para: S3, CloudFront, ACM, Route53, e para o bootstrap do CDK (CloudFormation, SSM, IAM — geralmente via policy `AdministratorAccess` ou uma policy dedicada ao CDK).

## Deploy

Cada stack tem seu próprio workflow, disparado apenas quando os arquivos relevantes mudam:

- **`.github/workflows/deploy.yml`** — stack `Dashboards-*`. Dispara em push a `main`/`develop`, exceto quando só `auditoria/**` muda.
- **`.github/workflows/deploy-auditoria.yml`** — stack `Auditoria-*`. Dispara em push a `main`/`develop` apenas quando `auditoria/**` (ou a própria stack/workflow) muda.

Cada workflow faz: `cdk deploy <stack>` (cria/atualiza a infra isolada) → `aws s3 sync` do respectivo conteúdo → invalidação do seu CloudFront.

## Deploy manual (local)

```bash
cd infrastructure
pip install -r requirements.txt
npm install -g aws-cdk

cdk bootstrap aws://<ACCOUNT_ID>/us-east-1

cdk deploy Dashboards-Production --context env=production   # ou Dashboards-Staging --context env=staging
cdk deploy Auditoria-Production  --context env=production   # ou Auditoria-Staging  --context env=staging
```
