# coding: UTF-8

import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(os.getcwd(), '.env')
load_dotenv(dotenv_path)

"""==============================
Bot credential
# BOT TOKEN
=============================="""
# https://github.com/mo9mo9study/discord.VCtimeRecord.git
# このリポジトリの機能を動かすBOTのTOKEN
Token = os.environ.get("DISCORD_BOT_TOKEN")


"""==============================
Google credential
=============================="""
FirebaseAipkey=os.environ.get("FIREBASE_API_KEY")
FirebaseshortLinksPrefix=os.environ.get("FIREBASE_DYNAMICLINKS_PREFIX")
