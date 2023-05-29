import streamlit as st
import httpx
from datetime import datetime, timedelta
from pytz import timezone  # Import pytz for time zone handling
import pandas as pd
from external import do_file, do_file2
from namepaths import dict_tipos
from pymongo import MongoClient

st.markdown("# BAIXAR LISTA DE ALUNOS :clipboard:")

TIPOS = tuple(dict_tipos.keys())
from turmasdetalhes import turmastd

pre_leque = ['escolha a turma aqui'] + sorted(list(turmastd.keys()))
leque = tuple(pre_leque)
option = st.selectbox('Selecione a turma:', leque)


def download_excel_file(lista, turma, tipo):
  """
  Function that takes a bytes object and downloads it as an Excel file
  """
  st.download_button(
    label="Baixar arquivo no formato do Excel",
    data=lista,
    file_name=f"{turma}_{tipo.replace(' ', '_')}.xlsx",
    mime=
    "application/vnd.openxmlformats-    officedocument.spreadsheetml.sheet",
  )

try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec1 = st.secrets["colec1"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = os.environ["db1"]
  colec1 = os.environ["colec1"]

cluster = MongoClient(dbcred)
db = cluster[db1]

@st.cache_data(ttl=3600)
def get_data_at_db_7():
    data = db[colec1].find()
    return pd.DataFrame(data)

def main():
  tipo = st.selectbox('Selecione o tipo de lista', ('tipo', *TIPOS))
  # Make API request to get data
  if tipo in TIPOS:
    df = get_data_at_db_7()
    df = df[df['turma'] == option]

    if not df.empty:
      df = df[['matrícula', 'estudante']]
      st.write(df, unsafe_allow_html=True)
      if '3' in tipo:
        func_do_file = do_file2
      else:
        func_do_file = do_file
      bytes_data = func_do_file(df.estudante.to_list(),
                                turma=option,
                                file_name=dict_tipos.get(tipo))
      if bytes_data:
        download_excel_file(lista=bytes_data, turma=option, tipo=tipo)


if 'escolha a turma aqui' not in option:
  main()
