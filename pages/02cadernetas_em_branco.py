import streamlit as st

st.markdown(
  "## BAIXAR CADERNETAS PERSONALIZADAS TURMA/PROFESSOR/COMPONENTE/UNIDADE")
st.markdown("### cadernetas :blue[SEM] registros de frênquência e notas. :newspaper:")

import httpx
import pandas as pd
from cader import do_cader
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
def get_data_at_db3():
    data = db[colec1].find()
    return pd.DataFrame(data)

nome_rm = prodt[1]
rm_nome = prodt[0]
to_select = tuple(nome_rm.keys())
zip_data = None
with st.form("formulário"):
  st.write("preencha os campos")

  prof_sel = st.selectbox('Selecione o professor',
                          ('PROFESSOR(A)', *to_select))
  und = st.selectbox("Selecione a unidade",
                     ("unidade:", "I UND.", 'II UND.', 'III UND.'))
  submitted = st.form_submit_button("gerar cadernetas")
  if submitted:
    if prof_sel[0].isdigit() and 'I' in und:
      df = get_data_at_db3()

      matrícula = nome_rm.get(prof_sel)
      prof_name = rm_nome.get(matrícula)
      my_ch = programação.get(matrícula)

      bytes_dict = {}
      for turma_nome, lcomps in my_ch.items():
        df_ = df[df['turma'] == turma_nome]
        dfX = df_[['matrícula', 'estudante']]
        for componente in lcomps:
          bytes_data = do_cader(
            dfX.estudante.to_list(),
            turma=turma_nome,
            professor=prof_name,
            componente=componente,
            unidade=und,
          )
          if bytes_data:
            bytes_dict.update(
              {f'{turma_nome}_{nsafe(componente)}': bytes_data})
          else:
            continue

      if bytes_dict:
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
          for nome, bytes_data in bytes_dict.items():
            zip_file.writestr(f"{nome}.xlsx", bytes_data)

        zip_data = zip_buffer.getvalue()

    else:
      st.error("selecione o professor e a unidade primeiro!")

if zip_data:
  st.download_button(
    label="Baixar as cadernetas em um arquivo zipado",
    data=zip_data,
    file_name=f"{nsafe(prof_sel)}_all_files.zip",
    mime="application/zip",
  )
