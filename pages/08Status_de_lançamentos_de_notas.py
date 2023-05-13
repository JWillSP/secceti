import json
import streamlit as st
import pandas as pd
import pymongo
from turmasdetalhes import prodt

try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec2 = st.secrets["colec2"]
  colec3 = st.secrets["colec3"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = st.secrets["db1"]
  colec2 = st.secrets["colec2"]
  colec3 = st.secrets["colec3"]

client = pymongo.MongoClient(dbcred)
db = client[db1]
collection2 = db[colec2]
collection3 = db[colec3]


@st.cache_data(ttl=3600)
def gera_meta():
    return list(collection3.find())[1]

main_meta_dict = gera_meta()['programação']


unidade = st.selectbox("Selecione a unidade",
                     ("unidade:", "I UND.", 'II UND.', 'III UND.'))

@st.cache_data(ttl=3600)
def gera_medias(und):
    return list(collection2.find({"unidade": und.split()[0]}))

medias = gera_medias(unidade)


if "I" in unidade and medias:


    uniques_planejamentos = set()
    dict_of_prof_planejamento = {}
    for prof_code, prof_collec in main_meta_dict.items():
        list_of_planejamentos = []
        for class_name, matter_list in prof_collec.items():
            for matter in matter_list:
                uniques_planejamentos.add((class_name, matter))
                list_of_planejamentos.append((class_name, matter))
        dict_of_prof_planejamento[prof_code] = list_of_planejamentos

    set_of_done = set()
    for item in medias:
        set_of_done.add((item['turma'], item['componente']))
    # not_done  = uniques_planejamentos -  set_of_done
    col1, col2, col3 = st.columns(3)
    col3.metric(label=r"% de envios", value=f"{round((len(set_of_done)/len(uniques_planejamentos)*100), 1)} %")
    dict_to_df = {}
    contador = 0
    for prof_rm, prof_list in dict_of_prof_planejamento.items():
        for item in prof_list:
            if item in set_of_done:
                dict_to_df.update({contador:{'professor':prof_rm, 'turma':item[0], 'componente':item[1], 'status':'entregue'}})
            else:
                dict_to_df.update({contador:{'professor':prof_rm, 'turma':item[0], 'componente':item[1], 'status':'aguardando'}})
            contador += 1
    df = pd.DataFrame(dict_to_df).T
    dffall = df.copy()
    dffall['professor'] = dffall['professor'].map(prodt[0])
    dffall = dffall.dropna()
    st.success('Fichas de desempenho turma/componente de todos professores')
    st.dataframe(dffall.set_index('professor'))
    st.success('Fichas de desempenho turma/componente individual por professor')
    for pro in df.groupby('professor'):
        try:
            st.write(prodt[0][pro[0]])
            st.table(pro[1].set_index('professor'))
        except:
            continue



