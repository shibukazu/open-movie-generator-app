# Open Movie Generator CLI

YouTube などによく見られるような動画を自動で動画を生成する CLI ツールです。

現時点では下記に対応しています。

- 2ch や 5ch のスレッドの内容からフル動画またはショート動画を生成する

  > [!WARNING]
  > 現時点では下記に挙げる一部のスレッドにのみ対応しています。
  >
  > https://nova.5ch.net

- GPT を用いて架空のスレッドの内容からフル動画またはショート動画を生成する
- GPT を用いてトリビアショート動画を生成する

さらに、高度な抽象化とコンポーネント分離により、原稿生成、音声合成、動画生成、サムネイル生成の各機能を独立して拡張することが可能です。

## Example

### 掲示板ショート動画

生成される動画の例

<video src="https://github.com/user-attachments/assets/81256445-3a07-4481-a4dd-11516d59f733" width="500" height="300" controls></video>

生成されるサムネイル画像の例

<img src="https://github.com/user-attachments/assets/07f40bc4-8c9f-44b5-96da-04c638294016" width="270" height="480">

### 掲示板フル動画

生成される動画の例（一部抜粋）

<video src="https://github.com/user-attachments/assets/8f3b3ceb-7501-4f01-a16d-976371d93d46" width="500" height="300" controls></video>

生成されるサムネイル画像の例

<img src="https://github.com/user-attachments/assets/4cceeab0-f93b-4180-bf23-9cffe2472b32" width="500" height="300">

### トリビアショート動画

生成される動画の例

<video src="https://github.com/user-attachments/assets/df70588c-7049-47fb-ad0f-c4a173d45255" width="500" height="300" controls></video>

生成されるサムネイル画像の例

<img src="https://github.com/user-attachments/assets/9e926ebd-0499-451c-9a2a-94da2e0b1487" width="270" height="480">

## Install and Configure

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

### 5ch スレッドからフル動画を生成する

```bash
uv run src/cmd/main.py generate bulletin https://nova.5ch.net/test/read.cgi/livegalileo/1730087373/
```

### 5ch スレッドからショート動画を生成する

```bash
uv run src/cmd/main.py generate bulletin https://nova.5ch.net/test/read.cgi/livegalileo/1730087373/ --movie-generator-type=irasutoya_short --thumbnail-generator-type=bulletin_board_short
```

### GPT を用いた架空のスレッドからフル動画を生成する

```bash
uv run src/cmd/main.py generate pseudo-bulletin モネ,睡蓮,印象派
```

### GPT を用いた架空のスレッドからショート動画を生成する

```bash
uv run src/cmd/main.py generate pseudo-bulletin モネ,睡蓮,印象派 --movie-generator-type=irasutoya_short --thumbnail-generator-type=bulletin_board_short
```

### GPT を用いたトリビアショート動画を生成する

```bash
uv run src/cmd/main.py generate trivia 日本人,漫画,文化
```

## Caution

このプロジェクトは 5ch のスクレイピングを推奨するものではありません。スクレイピングによる情報の取得は自己責任で行ってください。

また、5ch のスレッドを用いたコンテンツを作成し、公開する場合は著作権の使用許諾を得る必要があります。
詳しくは下記を参照してください。

https://5ch.net/matome.html
