import streamlit as st
import httpx
from datetime import datetime, timedelta
from pytz import timezone  # Import pytz for time zone handling
import pandas as pd
from cifrafor import gera_cifra
from myecm import logador
from pymongo import MongoClient
from cader import normalizador


try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec4 = st.secrets["colec4"]
  colec3 = st.secrets["colec3"]
  colec1 = st.secrets["colec1"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = os.environ["db1"]
  colec4 = os.environ["colec4"]
  colec3 = os.environ["colec3"]
  colec1 = os.environ["colec1"]

cluster = MongoClient(dbcred)
db = cluster[db1]

@st.cache_data(ttl=3600)
def get_data_at_db6():
    data = db[colec1].find()
    return pd.DataFrame(data)

@st.cache_data(ttl=3600)
def get_data_at_db_1():
    para_componentes = db[colec3].find_one({"_id": colec1}).get('matriz')
    return para_componentes


st.cache_resource(ttl=3600)
def find_std_grades(student_id):
    return db[colec4].find({"matrícula": student_id}, {"_id": 0})


def main(user, logout):
  st.title("BOLETINS")
  st.subheader("permissão de visualizar todos alunos pelo usuário adm ou professor: " + user)
  st.button("sair", on_click=logout)
  search_term = st.text_input('Busque pelo nome do estudante', value='NOME DO ESTUDANTE')
  if search_term:
    df = get_data_at_db6()
    df = df[df['estudante'].str.contains(search_term, case=False)]
    if not df.empty:
      df = df[['matrícula', 'estudante', 'turma']]
      st.dataframe(df, use_container_width=True)
      if df.shape[0] < 6:
        dict_nome_matricula = {
          str(index) + ' - ' + row['estudante']: row['matrícula']
          for index, row in df.iterrows()
        }
        option = st.selectbox('Selecione o estudante correto:',
                              tuple(dict_nome_matricula.keys()))
        if option:
            student_id = dict_nome_matricula.get(option)
            turma = df[df['matrícula'] == student_id]['turma'].values[0]
            my_matters = get_data_at_db_1().get(turma)
            their_grades = pd.DataFrame.from_dict(find_std_grades(student_id))
            pivot = pd.pivot_table(their_grades, index='componente', columns='unidade', values='med')
            new_pivot = pivot[pivot.index.isin(my_matters)]
            if 'TF' in turma or 'TJ' in turma:
               new_pivot = new_pivot.applymap(normalizador)
            new_pivot
            st.dataframe(new_pivot, use_container_width=True)
            st.table(new_pivot)


logador(external_fucntion=main, permitions=['isAdmin', 'isTeacher'])