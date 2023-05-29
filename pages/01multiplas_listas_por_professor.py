import streamlit as st
import httpx
# from datetime import datetime, timedelta
# from pytz import timezone  # Import pytz for time zone handling
import pandas as pd
from external import do_file, do_file2
import zipfile
import io
from turmasdetalhes import prodt
from turmasdetalhes import programação
from handlewithname import make_windows_filename_safe as nsafe
from namepaths import dict_tipos

TIPOS = tuple(dict_tipos.keys())


def download_excel_file(lista, turma, tipo):
  """
  Function that takes a bytes object and returns it as an Excel file
  """
  bytes_io = io.BytesIO(lista)
  return bytes_io.getvalue()


def rotina(df_, option='', meutipo='', prof='', comp=''):

  if '3' in tipo:
    bytes_data = do_file2(df_.estudante.to_list(),
                          turma=option,
                          file_name=dict_tipos.get(tipo),
                          prof=prof,
                          comp=comp)
  else:
    bytes_data = do_file(df_.estudante.to_list(),
                         turma=option,
                         file_name=dict_tipos.get(tipo))
  return bytes_data

from pymongo import MongoClient
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
def get_data_at_db2():
    data = db[colec1].find()
    return pd.DataFrame(data)


st.markdown("# BAIXAR TODAS LISTAS DO PROFESSOR :books:")
nome_rm = prodt[1]
to_select = tuple(nome_rm.keys())
prof_sel = st.selectbox('Selecione o professor', ('PROFESSOR(A)', *to_select))
# Make API request to get data
if prof_sel[0].isdigit():
  tipo = st.selectbox('Selecione o tipo de lista', ('tipo', *TIPOS))
  if tipo in TIPOS:
    df = get_data_at_db2()
    matrícula = nome_rm.get(prof_sel)
    my_ch = programação.get(matrícula)
    bytes_dict = {}
    for turma_nome, lcomps in my_ch.items():
      df_ = df[df['turma'] == turma_nome]
      dfX = df_[['matrícula', 'estudante']]
      for componente in lcomps:
        bytes_data = rotina(dfX,
                            option=turma_nome,
                            meutipo=tipo,
                            prof=prof_sel,
                            comp=componente)
        if bytes_data:
          bytes_dict.update({f'{turma_nome}_{nsafe(componente)}': bytes_data})
        else:
          continue

    if bytes_dict:
      zip_buffer = io.BytesIO()

      with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for nome, bytes_data in bytes_dict.items():
          zip_file.writestr(f"{nome}.xlsx", bytes_data)

      zip_data = zip_buffer.getvalue()

      st.download_button(
        label="Download All Excel Files as Zip",
        data=zip_data,
        file_name=f"{nsafe(prof_sel)}_all_files.zip",
        mime="application/zip",
      )
