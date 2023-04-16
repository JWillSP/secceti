from pymongo import MongoClient
import streamlit as st

cluster = MongoClient(f"{st.secrets['dbcred']}")
db = cluster["college"]
st.success(db.list_collection_names())

vinculo = "2023@1124856"


def get_profs():
  query = {'$query': {"bond1": vinculo}, '$orderby': {"full_name": 1}}
  if profs := db["userprofs"].find(query):
    rm_nome = {
      item["username"]: item["full_name"]
      for item in profs if not item.get("isAdmin", False)
    }
    nome_rm = {(K + ' - ' + v): K for K, v in rm_nome.items()}
    return (rm_nome, nome_rm)


def get_progs():
  if progs := db["META"].find_one({'_id': vinculo}):
    return progs
