# ATLAS TO PARADISE — 更新ガイド

## 基本の流れ
```
data/content.json を編集 → python3 build.py → 全ファイルをアップロード
```
HTMLは直接いじらず、**content.json だけ**編集します（日本語 `ja` と英語 `en` の両方）。

## よくある更新
| やりたいこと | 編集する場所 |
|---|---|
| 更新履歴を足す | `news` に1件追加（最終更新日は自動で変わる） |
| 実績を足す | `works` に1件追加（`cat` でカテゴリ、`top:true` でトップに表示） |
| 最新作を差し替える | `works` の `latest:true` を付け替える（3件） |
| ECのデモを公開 | 該当ECの `demoLive` を `true`（`demoUrl` は公開URLに変更） |
| リンクを足す | `works` の `extra` に `{label, url}` を追加 |
| アクセント色を変える | `assets/css/style.css` の `--accent` |
| ひとことSNS等のURL | `site.sameAs` にURLを追加（GEO向け） |

## 要確認（先に入れてください）
- 写真・QR（LINE/WhatsApp）は設定済み。差し替えは同名で上書き→ build

## SEO・GEO（自動生成）
sitemap.xml / robots.txt / llms.txt / 構造化データ（Person・FAQ・実績）/ OGP / canonical
