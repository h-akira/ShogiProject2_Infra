<!-- AI instruction (pinned): IC 番号は他文書から参照されるため、初回制定以後に変更が生じた場合、番号を詰めてはならない（欠番が生じてもそのままにする） -->

# 設計決定事項（Infra Confirm）

インフラユニットにおける設計上の決定事項を管理する。各項目は `IC-<セクション>.<連番>` で識別し、他文書から参照可能とする。

本文中の `UC-x.x` はプロジェクト共通の [ユニット間の契約](../../docs/units_contracts.md) の番号を指す。

---

## 1. 全体

### IC-1.1: バックエンド不在時のデプロイ対応

CDK コンテキスト変数 `backends_deployed` でバックエンドスタックの存在を切り替え、初回は S3 オリジンのみでデプロイ可能にする。Infra とバックエンドのデプロイ順序に依存しない構成にするため。

### IC-1.2: ACM 証明書・ホストゾーンの CDK 管理外化

ACM 証明書および Route 53 ホストゾーンは CDK 管理外とし、手動で作成・管理する。CDK スタック削除時の影響を限定するため。詳細は [manual_resources.md](./manual_resources.md) を参照。

---

## 2. DistributionStack

### IC-2.1: S3（OAC）オリジンで静的ファイル配信

CloudFront のデフォルトビヘイビアは S3（OAC）オリジンで静的ファイルを配信する。SPA 配信基盤として使用。

### IC-2.2: API Gateway（main）へのプロキシ

`backends_deployed=True` 時、`/api/v1/main/*` を API Gateway（main）にプロキシする（UC-3.1）。フロントエンドと同一ドメインで API を提供し CORS を回避する。

### IC-2.3: API Gateway（analysis）へのプロキシ

`backends_deployed=True` 時、`/api/v1/analysis/*` を API Gateway（analysis）にプロキシする（UC-3.1）。理由は IC-2.2 と同様。

### IC-2.4: SPA フォールバック

API パス以外かつ拡張子なしのリクエストを `/index.html` にフォールバックする。SPA ルーティング対応のため。

### IC-2.5: IP 制限

`allowed_ips` が指定されている場合、リスト外の IP からのアクセスを `403` で拒否する。開発環境等でのアクセス制限に使用。

### IC-2.6: S3 バケットの保持ポリシー

S3 バケットに `RemovalPolicy.RETAIN` を設定する。フロントエンドデータの誤削除を防止するため。

### IC-2.7: バックエンドスタックの疎結合参照

API Gateway オリジンは `Fn.import_value` でバックエンドスタックのエクスポートを参照する（UC-2.2）。スタック間の疎結合を維持するため。

---

## 3. CognitoStack

### IC-3.1: UserPool の保持ポリシー

UserPool に `RemovalPolicy.RETAIN` を設定する。ユーザーデータの誤削除を防止するため。

### IC-3.2: PKCE による認証フロー

UserPoolClient はクライアントシークレットなし + Authorization Code Grant（PKCE）を使用する（UC-3.1）。SPA はクライアントシークレットを安全に保持できないため。

### IC-3.3: 管理操作用の認証フロー

UserPoolClient で `ADMIN_USER_PASSWORD_AUTH` を有効化する。Lambda からの管理操作用であり、SPA 認証は OAuth フローを使用する。
