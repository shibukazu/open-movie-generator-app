# Open Movie Generator CLI

YouTube などによく見られるような動画を自動で生成する CLI ツールです。

現時点では下記に対応しています。

- 2ch や 5ch のスレッドの内容からフル動画またはショート動画を生成する
- GPT を用いて生成した架空のスレッドの内容からフル動画またはショート動画を生成する
- GPT を用いて生成した雑学からショート動画を生成する

さらに、高度な抽象化とコンポーネント分離により、原稿生成、音声合成、動画生成、サムネイル生成の各機能を独立して拡張することが可能です。

> [!WARNING]
> 現時点では下記に挙げる一部のスレッドにのみ対応しています。
>
> - https://nova.5ch.net




## Example

### 掲示板風動画

|生成される動画|生成されるサムネイル|
|:-:|:-:|
|<video src="https://github.com/user-attachments/assets/275c5cef-e978-411a-b250-20c7af59e977" width="320" height="180" controls></video>|<img src="https://github.com/user-attachments/assets/0da68086-596a-4bc5-bab1-74ef0f49859f" width="320" height="180">|


### トリビア動画

|生成される動画|生成されるサムネイル|
|:-:|:-:|
|<video src="https://github.com/user-attachments/assets/2b2a7356-08a8-4899-8769-496b6b31854c" width="180" height="320" controls></video>|<img src="https://github.com/user-attachments/assets/a02b1db2-1c30-4653-9b42-572f565f2366" width="180" height="320">|


## インストール

すべての依存関係(VOICEVOX および uv)をインストールするためのスクリプトを用意しています。

```bash
./script/install.sh
```

その後.env.template に基づき、.env ファイルを作成します。

> [!NOTE]
> 動画生成には各種リソースを各ユーザーごとに用意していただく必要があります。
> 以下のリソースを用意してください。
>
> - 動画の BGM を material/movie/bgm に配置
> - 動画の背景動画を material/movie/bgv に配置
> - 動画で用いるキャラクター画像を material/movie/character に配置
> - サムネイルで用いる背景画像を material/thumbnail/background に配置
>
> ※ キャラクター画像は \_man\_ もしくは \_woman\_ というキーワードを含むファイル名としてください

## Let's Try

### 5ch スレッドに基づいたフル動画を生成する

```bash
uv run src/cmd/main.py generate bulletin $url
```

### 5ch スレッドに基づいたショート動画を生成する

```bash
uv run src/cmd/main.py generate bulletin $url --short
```

### 架空のスレッドに基づいたフル動画を生成する

```bash
uv run src/cmd/main.py generate pseudo-bulletin モネ,睡蓮,印象派
```

### 架空のスレッドに基づいたショート動画を生成する

```bash
uv run src/cmd/main.py generate pseudo-bulletin モネ,睡蓮,印象派 --short
```

### 雑学ショート動画を生成する

```bash
uv run src/cmd/main.py generate trivia 日本人,漫画,文化 --short
```

## 注意事項

このプロジェクトは 5ch のスクレイピングを推奨するものではありません。スクレイピングによる情報の取得は自己責任で行ってください。

また、5ch のスレッドを用いたコンテンツを作成し、公開する場合は著作権の使用許諾を得る必要があります。
詳しくは下記を参照してください。

https://5ch.net/matome.html

## ライセンス

本プロジェクトは商用・非商用を問わず、自由に利用することができます。

本プロジェクトはGitHub上のForkを除き、再配布を禁止しています。

また、本プロジェクトを用いて作成された動画を公開する際には本レポジトリをクレジットとして明記してください。


