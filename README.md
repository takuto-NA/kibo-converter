# Kibo Converter

フォルダ単位で画像を一括変換するデスクトップアプリです。HEIC を含む画像を PNG などへ変換し、ジョブ定義の保存・進捗表示・ログ出力に対応します。

## 開発環境

Python 3.11 以上を想定しています。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## テスト

```bash
python -m pytest -v
```

HEIC の統合テストは `pillow-heif` が利用可能な環境で、テスト内で生成した HEIC を用いて実行されます。

## 起動

```bash
python -m kibo_converter.main
```

またはインストール後:

```bash
kibo-converter
```
