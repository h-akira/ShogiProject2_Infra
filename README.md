# Infra

CDK で Cognito / S3 / CloudFront / Route 53 をデプロイするスタック。

## 必要な環境変数

| 変数 | 説明 | 例 |
|------|------|-----|
| `ENV` | 環境識別子 | `dev`, `pro` |
| `CDK_DEFAULT_REGION` | デプロイリージョン | `ap-northeast-1` |
| `DOMAIN_NAME` | カスタムドメイン名 | `shogi-dev.h-akira.net` |
| `ACM_CERTIFICATE_ARN` | ACM 証明書 ARN（us-east-1） | `arn:aws:acm:us-east-1:...` |
| `HOSTED_ZONE_NAME` | Route 53 ホストゾーン名 | `h-akira.net` |
| `COGNITO_DOMAIN_PREFIX` | Cognito ドメインプレフィックス | `sgp-dev` |

## ローカル開発

```bash
cp .env.sample .env
# .env を編集して実際の値を入れる
source .env
cdk deploy --all
```

## CI/CD

`CICD/infra.yaml` の CloudFormation スタックでデプロイされる CodeBuild が、
上記の環境変数を CodeBuild 環境変数として注入した上で `buildspec.yml` を実行する。
