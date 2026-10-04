# ADR 0001: GitHub API モジュールの抽出による疎結合化

## ステータス
採用済み

## コンテキスト（背景）

PR #103 以前、`envkp/core.py` には以下の重複したコードパターンが存在していました：

- GitHub API への GET リクエストと JSON パース処理（4箇所）
- GitHub API への DELETE リクエスト処理（3箇所）
- GitHub API URL の構築処理（4箇所）
- DELETE 操作の結果チェック処理（2箇所）

これらの重複により、コードの保守性が低下していました。また、GitHub 固有の実装が `core.py` に直接埋め込まれていたため、今後 GitLab などの他のプラットフォームへの対応を検討する際、大幅なリファクタリングが必要になる可能性がありました。

## 決定事項

GitHub API に関連する機能を独立したモジュール `envkp/github_api.py` に抽出し、以下のユーティリティ関数を提供することを決定しました：

- `build_repo_url(repo, *path_segments)`: GitHub API URL の一元管理
- `api_get(url, headers)`: GET リクエスト + JSON パース
- `api_delete(url, headers)`: DELETE リクエスト + ステータスコード取得
- `check_delete_result(status_code, entity_desc)`: DELETE 操作の結果出力

このアプローチにより、以下のメリットが得られます：

1. **コードの重複排除**: 重複していたコードパターンを削減し、保守性を向上
2. **疎結合化**: GitHub 固有の実装を独立モジュールに分離し、`core.py` をプラットフォームに依存しないビジネスロジックに集中させることが可能
3. **拡張性の確保**: 今後 GitLab などの他のプラットフォームに対応する際、インターフェースを共通化した上で実装を追加することが容易

## 結果

- 重複コードが削減され、54行のコードが削除されました
- 新規モジュール `envkp/github_api.py` が追加されました（40行、ドキュメントを含む）
- 動作の変更はありません。すべての API 呼び出しと制御フローは保持されています
- 事前に存在していた ruff の警告（E711, F841）はこの PR では変更されていません

## 今後の展開

このアーキテクチャ決定に基づき、GitLab などの他のプラットフォームに対応する際は以下の手順を検討します：

1. 抽象的なインターフェース（例: `api_get`, `api_delete` など）を定義
2. `github_api.py` と同様の実装を `gitlab_api.py` として追加
3. `core.py` において、プラットフォーム設定に応じて適切な API モジュールを選択する仕組みを導入

## 関連リンク

- PR #103: https://github.com/hwakabh/envkeeper/pull/103
- Devin セッション: https://app.devin.ai/sessions/2dde0d021aa8420b87467fdbc52e47c6
