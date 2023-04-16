import streamlit as st
import pandas as pd
import httpx
import io
from turmasdetalhes import turmastd


update_to_map = {
  '6798792': 'ivonete.cardoso2@aluno.enova.educacao.ba.gov.br',
  '8413675': 'roberta.oliveira79@aluno.enova.educacao.ba.gov.br',
  '202230303770': 'emili.lopes@aluno.enova.educacao.ba.gov.br',
  '7609517': 'sandra.dias14@aluno.enova.educacao.ba.gov.br',
  '10243667': 'lara.silva362@aluno.enova.educacao.ba.gov.br',
  '10335655': 'lara.silva362@aluno.enova.educacao.ba.gov.br',
  '10623789': 'pablo.pereira74@aluno.enova.educacao.ba.gov.br',
  '202230607612': 'pablo.pereira74@aluno.enova.educacao.ba.gov.br',
  '10454350': 'ana.silva3885@aluno.enova.educacao.ba.gov.br',
  '9744763': 'vanessa.reis54@aluno.enova.educacao.ba.gov.br',
  '8692652': 'cleide.botelho@aluno.enova.educacao.ba.gov.br',
  '202330359203': 'nathalia.silva140@aluno.enova.educacao.ba.gov.br',
  '202330396673': 'luis.barros20@aluno.enova.educacao.ba.gov.br',
  '9191831': 'maria.santos9172@aluno.enova.educacao.ba.gov.br',
  '10469163': 'maria.santos9172@aluno.enova.educacao.ba.gov.br',
  '7665197': 'gildete.silva22@aluno.enova.educacao.ba.gov.br',
  '202231902994': 'gisele.barra1@aluno.enova.educacao.ba.gov.br',
  '8724475': 'gisele.barra1@aluno.enova.educacao.ba.gov.br',
  '9746312': 'uilian.santos50@aluno.enova.educacao.ba.gov.br',
  '8838678': 'luis.vilarinho@aluno.enova.educacao.ba.gov.br',
  '10650462': 'luciana.lima68@aluno.enova.educacao.ba.gov.br',
  '10431591': 'cauan.padre1@aluno.enova.educacao.ba.gov.br',
  '9298745': 'marcela.campos4@aluno.enova.educacao.ba.gov.br'
}




pre_leque = ['escolha a turma aqui'] + sorted(list(turmastd.keys()))
leque = tuple(pre_leque)
option = st.selectbox('Selecione a turma:', leque)
if 'escolha a turma aqui' not in option:
  response = httpx.get(
    'https://freq-willapp.herokuapp.com/allstudents/2023%401124856')
  data = response.json()
  df = pd.DataFrame(data)
  df = df[df['turma'] == option]

  if not df.empty:
    df = df[['matrícula', 'estudante']]
    ndf = df.set_index('matrícula')
    ndf['email'] = ndf.index
    to_map = pd.read_pickle('./statics/dict_enova.pkl').to_dict()
    to_map.update(update_to_map)
    ndf['email'] = ndf['email'].map(to_map)
    st.dataframe(ndf['email'], use_container_width=True, height=1600)

    buffer = io.StringIO()
    ndf['email'].to_csv(buffer, header=False, index=False)
    # create a download button that downloads the buffer content as a txt file
    st.download_button(label="Download da lista de Emails em arquivo de texto",
                       data=buffer.getvalue().encode('utf-8'),
                       file_name=f'{option}_email_list.txt',
                       mime='text/plain')
