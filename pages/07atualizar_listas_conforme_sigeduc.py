import streamlit as st
import pandas as pd
import numpy as np
from pymongo import MongoClient
import time
import io
from fix_names import nametofix
import jwt

import pickle

SECRETNAME = 'estudantes '
try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec1 = st.secrets["colec1"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = st.secrets["db1"]
  colec1 = st.secrets["colec1"]


ph = st.empty()
form = ph.container()
form.write("##### SUBA SUA CHAVE DE ACESSO ADMINISTRATIVA")
uploaded_file = form.file_uploader("Upload seu login_data.pkl file",
                                   type=["pkl"])
if uploaded_file is not None:
  login_data = pickle.load(io.BytesIO(uploaded_file.read()))
else:
  login_data = None

if login_data is not None and \
    all(key in login_data for key in ['access_token', 'token_type', 'bonds', 'prof_user', 'expires_in']):

  try:
    decoded_token = jwt.decode(login_data['access_token'],
                               algorithms=["HS256"],
                               options={"verify_signature": False})
    if decoded_token['exp'] < time.time():
      raise Exception("Token expired")
    form.success("You are logged in.")

  except Exception as e:
    form.write("Seu tempo de acesso expirou. Por favor, faça login novamente.")
    login_data = None
  except:
    form.write(
      "Sua chave de acesso é inválida. por favor, faça login novamente.")
    login_data = None

try:
  to_next = (not login_data == None)
except ValueError:
  to_next = login_data.any()

if to_next:
  ph.empty()
  full_name = login_data['prof_user']['full_name']
  st.markdown(
    f'### {full_name}, bem vindo ao sistema de atualização de alunos no banco de dados'
  )
  st.write(
    "##### faça upload do arquivo com a lista de alunos vindas do SIGEDUC")
  uploaded_file = st.file_uploader("escolha o arquivo")
  if uploaded_file is not None:
    if SECRETNAME in uploaded_file.name:
      df = pd.read_csv(uploaded_file, delimiter=';', encoding='latin-1')[[
        'MATRICULA', 'NOME', 'ETAPA-SÉRIE', 'TURMA', 'SITUACAO'
      ]]
      df1 = df.rename(
        columns={
          'MATRICULA': "matrícula",
          'NOME': "estudante",
          'TURMA': "turma",
          'ETAPA-SÉRIE': 'serie',
          'SITUACAO': 'status'
        })
      trans = {202231507433: 'HERICA DE ALMEIDA SANTOS'}
      trans.update(nametofix)
      for rm, nome in trans.items():
        df1.loc[df1['matrícula'] == rm, 'estudante'] = nome

      df1['matrícula'] = df1['matrícula'].astype(str)
      df1 = df1.replace(np.nan, '', regex=True)
      filtragem_de_turmas = df1['turma'].unique().tolist()
      if '' in filtragem_de_turmas:
        filtragem_de_turmas.remove('')
      df2 = df1[df1['turma'].isin(filtragem_de_turmas)]
      df2['turno'] = df2['turma']

      def find_turno(turma):
        if 'MAT' in turma:
          return 'MATUTINO'
        elif 'VES' in turma:
          return 'VESPERTINO'
        elif 'NOT' in turma:
          return 'NOTURNO'
        elif 'INT7T' in turma:
          return 'PERÍODO INTEGRAL DE 7 HORAS'
        else:
          return 'TURNO NÃO ENCONTRADO'

      df2['turno'] = df2['turno'].apply(lambda x: find_turno(x))
      df2['status'] = 'MATRICULADO'
      df2['_id'] = df2.index + 1

      st.write(df2)
      if df2.shape[0] > 0:
        if st.button('Atualizar banco de dados'):
          st.write('enviando os dados ... aguarde uns segundos')
          to_json = list(df2.T.to_dict().values())
          st.json(to_json)
          try:
            cluster = MongoClient(f"{dbcred}")
            db = cluster[db1]
            db.list_collection_names()
            collection = db[colec1]
            collection.drop()
            collection.insert_many(to_json)
            st.success('Banco de dados atualizado com sucesso')
          except:
            st.error('erro ao atualizar banco de dados')
