import streamlit as st
import pandas as pd
import httpx
import io
from turmasdetalhes import turmastd

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
    ndf['email'] = ndf['email'].map(to_map)
    st.dataframe(ndf['email'], use_container_width=True, height=1600)

    buffer = io.StringIO()
    ndf['email'].to_csv(buffer, header=False, index=False)
    # create a download button that downloads the buffer content as a txt file
    st.download_button(label="Download da lista de Emails em arquivo de texto",
                       data=buffer.getvalue().encode('utf-8'),
                       file_name=f'{option}_email_list.txt',
                       mime='text/plain')
