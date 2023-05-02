#  a code for open 2023frequencia.json utf-8 file and convert it to python dict
import json 
from datetime import datetime, timedelta
import pandas as pd
from pymongo import MongoClient
import streamlit as st
from turmasdetalhes import turmastd


st.markdown('# Faltômetro')
st.sidebar.markdown("# Faltômetro")

try:
  dbcred = st.secrets["dbcred"]
except FileNotFoundError:
  import os
  dbcred = os.environ['dbcred']

cluster = MongoClient(dbcred)
db = cluster["college"]

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

unidade_selected = st.selectbox('Selecione a unidade', ['ESCOLHA A UNIDADE:', 'I', 'II', 'III'])

pre_leque = ['ESCOLHA A TURMA'] + sorted(list(turmastd.keys()))
leque = tuple(pre_leque)
turma_selected = st.selectbox('Selecione a turma:', leque)

if 'ESCOLHA' not in unidade_selected and 'ESCOLHA' not in turma_selected:
    collection = db['2023@1124856'] 
    df = pd.DataFrame(list(collection.find()))
    all_stds = pd.DataFrame(list(collection.find()))
    collection = db['2023frequencia']
    df = pd.DataFrame(list(collection.find()))
    freq_all = pd.DataFrame(list(collection.find()))
    collection = db['2023@jus']
    df = pd.DataFrame(list(collection.find()))
    all_jus = pd.DataFrame(list(collection.find()))
    
    daterange = pd.DatetimeIndex(unidades_dr[unidade_selected])
    freq_all['datetime'] = pd.to_datetime(freq_all['created_at'])
    mask = freq_all['datetime'].dt.date.isin(daterange.date)
    df_filtered = freq_all[mask]

    master_faltas_df = pd.DataFrame()
    for index, current_row in df_filtered.iterrows():
        new_df = pd.DataFrame()
        one_freq = (~pd.DataFrame(current_row['frequência']).set_index('matrícula')['isPresent'].T)
        local_series = one_freq[one_freq].astype(int)*len(current_row['horários'])
        new_df['matrícula'] = local_series.index
        new_df['faltas'] = local_series.values
        new_df['date'] = current_row['datetime']
        new_df['turma'] = current_row['turma']
        new_df['componente'] = current_row['componente']
        new_df['horários'] = str(current_row['horários'])
        new_df['vínculo'] = current_row['vínculo']
        new_df['professor'] = current_row['professor']
        new_df['pro_matrícula'] = current_row['matrícula']
        master_faltas_df = pd.concat([new_df, master_faltas_df], ignore_index=True)

    amostra_alunos = all_stds[all_stds['turma'] == turma_selected].matrícula.values

    amostra_nome = all_stds[all_stds['matrícula'].isin(amostra_alunos)]
    d_mat_nome = {
        matrícula: nome for matrícula, nome in zip(amostra_nome.matrícula, amostra_nome.estudante)
    }

    mask = master_faltas_df.matrícula.isin(amostra_alunos)
    sel_turma_current = master_faltas_df[mask]
    class_jus = all_jus[all_jus['matrícula'].isin(sel_turma_current.matrícula)]
    def classificar_justificativa(row_, class_jus_):
        df = class_jus_[class_jus_["matrícula"] == row_["matrícula"]]
        if df.empty:
            return 'NÃO'
        else:
            for j, row in df.iterrows():
                data_inicio = datetime.strptime(row["data_init"], '%d/%m/%Y')
                data_fim = datetime.strptime(row["data_end"], '%d/%m/%Y')
                verdade = data_inicio.date() <= row_.date.to_pydatetime().date() <= data_fim.date()
                if verdade:
                    if row.tem_atestado:
                        return "SIM, COM ATESTADO MÉDICO"
                    return 'SIM'
            return 'NÃO'


    sel_turma_current['JUSTIFICATIVA'] = sel_turma_current.apply(
        lambda row: classificar_justificativa(row, class_jus),
        axis=1
    )
    minhas_datas = unidades[unidade_selected]
    inicio_ = minhas_datas['inicio']
    fim_ = minhas_datas['fim']
    st.markdown(f'### TURMA: {turma_selected}')
    st.markdown(f'### UNIDADE: {unidade_selected}')
    st.markdown(f'### PERÍODO: {inicio_} à {fim_} ')
    pivot = pd.pivot_table(sel_turma_current, index='matrícula', columns='componente', values='faltas', aggfunc='sum')
    pivot['TOTAL_DE_FALTAS'] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
    pivot = pivot.fillna(0.0)
    pivot = pivot.astype(int)
    pivot = pivot.replace(0, '-')
    pivot['NOME'] = pivot.index.map(d_mat_nome)
    cols = pivot.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    pivot = pivot.loc[:, cols]
    pivot = pivot.set_index('NOME')
    st.markdown('#### faltas por componente **SEM** abondo de atestado médico')
    st.write(pivot)
    sel_turma_current_ = sel_turma_current.copy()
    sel_turma_current = sel_turma_current_.drop(sel_turma_current_[sel_turma_current_['JUSTIFICATIVA'] == 'SIM, COM ATESTADO MÉDICO'].index)
    pivot = pd.pivot_table(sel_turma_current, index='matrícula', columns='componente', values='faltas', aggfunc='sum')
    pivot['TOTAL_DE_FALTAS'] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by='TOTAL_DE_FALTAS', ascending=False)
    pivot = pivot.fillna(0.0)
    pivot = pivot.astype(int)
    pivot = pivot.replace(0, '-')
    pivot['NOME'] = pivot.index.map(d_mat_nome)
    cols = pivot.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    pivot = pivot.loc[:, cols]
    pivot = pivot.set_index('NOME')
    st.markdown('#### faltas por componente **COM** abondo de atestado médico')
    st.dataframe(pivot, use_container_width=True)
else:
    st.markdown('### ESCOLHA A UNIDADE E A TURMA NO MENU LATERAL')
