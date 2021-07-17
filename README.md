# About discord.VCtimeRecord
[![GitHub forks](https://img.shields.io/github/forks/mo9mo9study/discord.VCtimeRecord.svg)](https://github.com/mo9mo9study/discord.VCtimeRecord/network)
![Discord](https://discordapp.com/api/guilds/603582455756095488/widget.png?style=shield)

# Future
- ORMを活用したDB連携のDMモジュールを作成してそれに対応したコードに書き換える
- 今後pep8に準拠した書式で記載する
- README.mdを最新情報に修正する


# 当リポジトリのファイルを事項するための準備
- 環境はvenvにて作成しています
- commit時のローカル運用
  - ディレクトリ[.githooks/]にてcommitをトリガーに動く処理を記載しています
  - pythonの[autopep8]と[flake8]をcommit対象のファイルに対して実行します
  - これを活用することでpepに準拠するように自動修正やエラー箇所を出力してくれます
- 実行に必要なパッケージはrequirements.txtに記載しています
## 初期構築
```sh
# pythonの仮想環境を作成する
python3 -m venv venv
# 仮想環境にアタッチする
source venv/bin/activate
# 必要なパッケージを仮想環境ないでインストールする
pip3 install -r requirements.txt
# pre-commitの設定
## [.git/hooks/pre-commit]を作成
pre-commit install

# 必要があればgitの設定を追加してください
## git config [--user.name/--user.email]
```

# 必要な認証情報
1. DiscordBOTの認証情報
[BOTのトークン取得方法](https://discordpy.readthedocs.io/ja/latest/discord.html#discord-intro)
2. Googleのダイナミックリンクの認証情報
```sh
# ファイルをコピーして必要な認証情報を埋め込む
cp .env.sample .env
vi .env
```

# 事前準備
- Dockerをインストールしましょう。Dockerの知識が必要です。
[https://docs.docker.com/](https://docs.docker.com/)
- ローカル開発するためのDiscordサーバーを立てておきましょう。
[サーバー作成方法](https://support.discord.com/hc/ja/articles/204849977-%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC%E3%81%AE%E4%BD%9C%E6%88%90%E3%81%AE%E4%BB%95%E6%96%B9)
- BOTをサーバーに登録します
[Discordリファレンス Botアカウント作成](https://discordpy.readthedocs.io/ja/latest/discord.html)
- サーバーIDは、サーバーネームを右クリック/チャンネルIDは、チャンネルを右クリック
[ユーザー/サーバー/メッセージIDはどこで見つけられる？](https://support.discord.com/hc/ja/articles/206346498-%E3%83%A6%E3%83%BC%E3%82%B6%E3%83%BC-%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC-%E3%83%A1%E3%83%83%E3%82%BB%E3%83%BC%E3%82%B8ID%E3%81%AF%E3%81%A9%E3%81%93%E3%81%A7%E8%A6%8B%E3%81%A4%E3%81%91%E3%82%89%E3%82%8C%E3%82%8B-)

# dockerを使って開発する人向けのメモ
⚠️ 現在、このリポジトリはDockerfileを作成していないため、以下の手順などは今後のためのメモになります
## 注意
- 現状は、ローカルのファイルを変更しても、コンテナ内のファイルは変更されません。
- 自身でマウントする環境を作るか、変更毎にdockerをbuildし直す必要があります。
## Docker imageをbuild
- ~~discord.VCtimeRecord ディレクトリ内で以下コマンドを実行~~
- ~~厳密にはDockerfileが存在する~~
- ~~Dockerを起動すると、自動でBotが起動する状態です。~~
```sh
docker build . -t discord.VCtimeRecord
docker run -v $(pwd)/entry_exit/env_vars:/dotfiles -itd discord.VCtimeRecord
docker ps # discord.VCtimeRecordが上がっていればok
```
## 起動したDocker imageのbashでログイン
```sh
docker exec -it $(docker ps -lq) bash
or
docker exec -it $(docker ps|grep discord.VCtimeRecord|awk -F' ' '{print $1}') bash
```
