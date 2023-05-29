import streamlit as st
import pandas as pd
import pymongo
from turmasdetalhes import prodt
import base64
#  a code for open 2023frequencia.json utf-8 file and convert it to python dict
from datetime import datetime, timedelta
from pymongo import MongoClient
from turmasdetalhes import turmastd
import numpy as np
from cader import do_cader_x
import uuid
from myecm import logador



def download_excel_file(layout, lista, nome, prof):
  """
  Function that takes a bytes object and downloads it as an Excel file
  """
  layout.markdown('˅˅˅˅˅˅˅˅˅˅˅˅˅˅˅')
  layout.download_button(
    label="Baixar Caderneta",
    data=lista,
    file_name=f"{nome.replace(' ', '_')}_{prof.replace(' ', '_')}.xlsx",
    mime=
    "application/vnd.openxmlformats-    officedocument.spreadsheetml.sheet",
  )
  layout.markdown('˄˄˄˄˄˄˄˄˄˄˄˄˄˄˄')
  layout.write('')
  layout.write('')

try:
  dbcred = st.secrets["dbcred"]
  db1 = st.secrets["db1"]
  colec5 = st.secrets["colec5"]
  colec6 = st.secrets["colec6"]
  colec2 = st.secrets["colec2"]
  colec3 = st.secrets["colec3"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']
  db1 = os.environ["db1"]
  colec5 = os.environ["colec5"]
  colec6 = os.environ["colec6"]
  colec2 = os.environ["colec2"]
  colec3 = os.environ["colec3"]

cluster = MongoClient(dbcred)
db = cluster[db1]




client = pymongo.MongoClient(dbcred)
db = client[db1]
collection2 = db[colec2]
collection3 = db[colec3]
# with open('2023frequencia.json', encoding='utf-8') as f:
#     data = json.load(f)
# with open('2023@jus.json', encoding='utf-8') as f:
#     data = json.load(f)
# with open('2023@1124856.json', encoding='utf-8') as f:
#     data = json.load(f)

unidades = {
    'I': {
        'inicio': '06-02-2023',
        'fim': '05-05-2023'
    },
    'II': {
        'inicio': '08-05-2023',
        'fim': '31-08-2023'
    },
    'III': {
        'inicio': '01-09-2023',
        'fim': '15-12-2023'
    },
}

unidades_dr = eval(str(unidades))
for unidade, datas in unidades.items():
    inicio = datetime.strptime(datas['inicio'], '%d-%m-%Y')
    fim = datetime.strptime(datas['fim'], '%d-%m-%Y')
    fim += timedelta(days=1)
    daterange = pd.date_range(start=inicio, end=fim, inclusive='both')
    unidades_dr[unidade] = daterange


@st.cache_data(ttl=3600)
def get_data_at_db():
    collection2 = db[colec5]
    freq_all = pd.DataFrame(list(collection2.find()))
    collection3 = db[colec6]
    all_jus = pd.DataFrame(list(collection3.find()))
    return freq_all, all_jus


def date_convert(date):
    date = date.split('/')
    date = datetime(int(date[2]), int(date[1]), int(date[0]))
    return date

def gera_pivot(unidade_selected, turma_selected, componente):
    freq_all, all_jus = get_data_at_db()
    daterange = pd.DatetimeIndex(unidades_dr[unidade_selected])
    freq_all['date'] = freq_all['data'].apply(date_convert)
    mask = freq_all['date'].dt.date.isin(daterange.date)
    df_filtered = freq_all[mask]
    df_turma_ = df_filtered[df_filtered['turma'] == turma_selected]
    with_who_missed = df_turma_[df_turma_['componente'] == componente]
    with_who_missed_sorted = with_who_missed.sort_values(by='date')
    def applied(row):
        row['aula'] = row['data'] + ' - ' + (f"{row['horários'][0]}°h" if len(row['horários']) == 1 else f"{row['horários'][0]}°h/{row['horários'][1]}°h")
        return row
    with_who_missed_sorted = with_who_missed_sorted.apply(applied, axis=1)

    def get_who_miss(c_row):
        to_return = {}
        par = ~pd.DataFrame(c_row['frequência']).set_index('matrícula')['isPresent']
        middle = (par[par]*len(c_row['horários'])).to_dict()
        for rm, nfaltas in middle.items():
            inner = {}
            inner['matrícula'] = rm
            inner['faltas'] = nfaltas
            inner['componente'] = c_row['componente']
            inner['date'] = c_row['date']
            inner['data'] = c_row['data']
            inner['aula'] = c_row['aula']
            to_return.update({str(rm)+'_'+c_row['created_at']:inner})
        return to_return if to_return else np.nan
    for_df  = {}
    for item in with_who_missed_sorted.apply(get_who_miss, axis=1).dropna().values:
        for_df.update(item)
    df = pd.DataFrame(for_df).T
    if df.empty:
        return {}, {}, {}, pd.DataFrame(), pd.DataFrame()
    class_jus = all_jus[all_jus['matrícula'].isin(df.matrícula)]
    def classificar_justificativa(row_, class_jus_):
        df_ = class_jus_[class_jus_["matrícula"] == row_["matrícula"]]
        if df_.empty:
            return 'NÃO'
        else:
            for j, row in df_.iterrows():
                data_inicio = datetime.strptime(row["data_init"], '%d/%m/%Y')
                data_fim = datetime.strptime(row["data_end"], '%d/%m/%Y')
                verdade = data_inicio.date() <= row_.date.to_pydatetime().date() <= data_fim.date()
                if verdade:
                    if row.tem_atestado:
                        return "SIM, COM ATESTADO MÉDICO"
                    return 'SIM'
            return 'NÃO'
    df['JUSTIFICATIVA'] = df.apply(
        lambda row: classificar_justificativa(row, class_jus),
        axis=1
    )
    pivot = pd.pivot_table(df, index='matrícula', columns='aula', values='faltas', aggfunc='sum')
    pivot['TOTAL_DE_FALTAS'] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
    pivot = pivot.fillna(0.0).astype(int)
    abonado = df.copy()
    dfabono = abonado.drop(
        abonado[abonado['JUSTIFICATIVA'] == 'SIM, COM ATESTADO MÉDICO'].index
        )
    pivot2 = pd.pivot_table(dfabono, index='matrícula', columns='aula', values='faltas', aggfunc='sum')
    pivot2['TOTAL_DE_FALTAS'] = pivot2.sum(axis=1)
    pivot2 = pivot2.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
    pivot2 = pivot2.fillna(0.0).astype(int)

    def date_to_uuid(date_string):
        uuid_obj = uuid.uuid5(uuid.NAMESPACE_URL, date_string)
        return str(uuid_obj)

    aula_id = {aula: date_to_uuid(_id) for aula, _id in zip(with_who_missed_sorted.aula, with_who_missed_sorted._id)}
    aula_data = {aula: data for aula, data in zip(with_who_missed_sorted.aula, with_who_missed_sorted.date)}
    aula_content_dict = {aula: content for aula, content in zip(with_who_missed_sorted.aula, with_who_missed_sorted.conteúdo)}
    return aula_data, aula_content_dict, aula_id, pivot, pivot2


def main(user, logout):    # Custom function to generate download links
    def get_download_link(file_name):
        csv_data = f'Data for {file_name}'  # Replace with actual file data
        b64 = base64.b64encode(csv_data.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">Download</a>'
        return href

    # Display column

    @st.cache_data(ttl=3600)
    def gera_meta():
        return list(collection3.find())[1]

    main_meta_dict = gera_meta()['programação']

    st.markdown('# Cadernetas Preenchidas pelo App CallDariaEdit')
    st.subheader("permissão de visualizar todos alunos pelo usuário adm ou professor: " + user)
    st.button("sair", on_click=logout)
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
        if user  in prodt[0].values():
            list_de_profs = list(filter(lambda x: user in x,  prodt[1].keys()))
        else:
            list_de_profs = list(prodt[1].keys())
        st.success('Fichas de desempenho de professor selecionado')
        professor = st.selectbox('Selecione o professor', list_de_profs)
        dfp = df[df['professor'] == prodt[1][professor]]
        st.markdown(f'### {professor}')
        st.table(dfp.set_index('professor'))
        envios = filter(lambda x: x['matrícula'] == prodt[1][professor], medias)
        dict_envios = {}
        for idx, data_selected in enumerate(envios):
            dict_envios[idx] = st.columns([1, 1, 1])  # Adjust column widths as needed
            turma = data_selected.get('turma')
            componente = data_selected.get('componente')
            dict_envios[idx][0].write(turma)
            dict_envios[idx][1].write(componente)
            if dict_envios[idx][2].button('gerar_caderneta', key=idx):
                aula_data, aula_content_dict, aula_id, pivot, pivot2 = gera_pivot(unidade.split()[0], turma, componente)
                bytes_data = do_cader_x(
                    lmed=data_selected.get('médias'),
                    turma=turma,
                    componente=componente,
                    professor=professor,
                    unidade=unidade.split()[0],
                    aula_id=aula_id,
                    aula_data=aula_data,
                    aula_content_dict=aula_content_dict,
                    pivot=pivot,
                    pivot2=pivot2
                )
                if bytes_data:
                    download_excel_file(layout=dict_envios[idx][2], lista=bytes_data, nome=f'{turma}_{componente}', prof=professor)                


logador(external_fucntion=main, permitions=['isAdmin', 'isTeacher'])



