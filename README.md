# Kibo Converter

Desktop app for converting image folders in batches.

フォルダ単位で画像を一括変換するデスクトップアプリです。HEIC を含む画像を、`PNG` / `JPEG` / `WEBP` へ変換し、ジョブ定義の保存・進捗表示・ログ出力に対応します。

## 何ができるか

- 入力フォルダ内の画像をまとめて別形式へ変換する
- 対象拡張子を指定する
- サブフォルダもまとめて処理する
- 長辺サイズを指定して縮小する
- 同名ファイルの扱いを「上書き」か「別名保存」から選ぶ
- 実行中も UI を固めずに進捗とログを確認する

## 最短ユースケース

1. iPhone の `HEIC` 画像が入ったフォルダを入力元に選ぶ
2. 出力先フォルダを選ぶ
3. 出力形式を `PNG` にする
4. 必要ならリサイズや重複時の扱いを調整する
5. `変換を実行` を押して、進捗とログを確認する

## 画面の見方

- 入力元フォルダ: 変換したい画像が入っている場所
- 対象にする拡張子: どの画像を処理対象にするか
- 出力先フォルダ: 変換後の画像を保存する場所
- 出力形式 / リサイズ: 変換後の形式と画像サイズの設定
- 実行パネル: 進捗、ログ、キャンセル操作を確認する場所

## 対応範囲と注意点

- このリポジトリは minimum viable product（MVP）段階のラスタ画像変換アプリです
- 動画・音声・文書の変換は対象外です
- HEIC（iPhone などで使われる高効率画像形式）対応は `pillow-heif` と OS 側の実行環境に依存します
- macOS 由来の `._*` など、一部の OS 付随ファイルは既定で入力スキャンから除外されます

詳細は次のドキュメントを参照してください。

- [既知の制限事項](docs/known-limitations.md): MVP の範囲、HEIC 環境依存、除外ルール、性能上の注意点
- [手動テストチェックリスト](docs/manual-test-checklist.md): GUI の確認観点、初見ユーザー観点、回帰確認の手順

## コードをどこから読むか

- `src/kibo_converter/main.py`: アプリ起動の入口
- `src/kibo_converter/ui/`: 画面部品とメインウィンドウ
- `src/kibo_converter/application/`: ジョブ実行、事前チェック、設定保存などのユースケース
- `src/kibo_converter/domain/`: ジョブ定義、出力ルール、処理条件などの中核ルール
- `src/kibo_converter/infrastructure/`: ファイル走査、画像入出力、ログ出力などの外部 I/O

代表的な流れは `MainWindow` でフォーム入力を受け取り、`ui/view_models.py` が `JobDefinition` へ変換し、`application/job_executor.py` がバックグラウンドで処理を実行する形です。`ui/view_models.py` は Qt の重い ViewModel 層ではなく、フォーム状態の変換と表示文言の整形を担う薄い橋渡しです。

## 開発環境

Python 3.11 以上を想定しています。主な動作確認対象は Windows です。

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

共通:

```bash
pip install -e ".[dev]"
```

## テスト

```bash
python -m pytest -v
```

- `tests/unit/`: ドメイン・アプリケーション・インフラの単体テスト
- `tests/integration/`: ファイル走査、画像変換、保存済みジョブ再実行などの結合テスト
- `tests/ui/`: `qtbot` を使うウィジェット実体の UI テスト
- `tests/unit/ui/`: 表示文言整形やフォーム変換など、UI 周辺の純粋関数テスト

HEIC の統合テストは `pillow-heif` が利用可能な環境で、テスト内で生成した HEIC を用いて実行されます。生成できない場合はフィクスチャへフォールバックし、それも無い場合は skip されます。

## 起動

```bash
python -m kibo_converter.main
```

またはインストール後:

```bash
kibo-converter
```
