# 手動作成 AWS リソース

CDK 管理外で手動作成するリソースの一覧（IC-1.2）。作成後、対応する値を CDK の環境変数として設定する（環境変数の定義は [cdk.md](./cdk.md#環境変数) を参照）。

## Route 53 ホストゾーン

| ホストゾーン | 用途 | 備考 |
|---|---|---|
| `shogi.example.com` | 本番環境 | 親ゾーン `example.com` から NS 委任 |
| `shogi-dev.example.com` | 開発環境 | 同上 |

## ACM 証明書（us-east-1）

リージョンは **us-east-1** に作成する。各環境ごとにルートドメインとワイルドカードの SAN を含む 1 枚の証明書を作成する。

| 環境 | SAN | 用途 |
|---|---|---|
| 本番 | `shogi.example.com` + `*.shogi.example.com` | CloudFront + Cognito |
| 開発 | `shogi-dev.example.com` + `*.shogi-dev.example.com` | 同上 |

> 1 枚の証明書で CloudFront（ルートドメイン）と Cognito（`auth.*`）の両方をカバーするため、CDK 環境変数 `ACM_CERTIFICATE_ARN` と `COGNITO_CERTIFICATE_ARN` には同じ ARN を設定する。

## 環境ごとの CDK 環境変数設定値

上記リソースの作成後、CDK デプロイ時の環境変数に以下の値を設定する。

| CDK 環境変数 | 本番 (pro) | 開発 (dev) |
|---|---|---|
| `DOMAIN_NAME` | `shogi.example.com` | `shogi-dev.example.com` |
| `HOSTED_ZONE_NAME` | `shogi.example.com` | `shogi-dev.example.com` |
| `ACM_CERTIFICATE_ARN` | *(本番用証明書 ARN)* | *(開発用証明書 ARN)* |
| `COGNITO_AUTH_DOMAIN` | `auth.shogi.example.com` | `auth.shogi-dev.example.com` |
| `COGNITO_CERTIFICATE_ARN` | `ACM_CERTIFICATE_ARN` と同じ | `ACM_CERTIFICATE_ARN` と同じ |
