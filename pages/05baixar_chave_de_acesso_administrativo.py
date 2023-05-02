import streamlit as st
import pandas as pd
import httpx
import io
import pickle

SECRETNAME = 'estudantes '

st.markdown("### BAIXAR CHAVE DE ACESSO ADMINISTRATIVA :old_key:")
st.sidebar.markdown(
  "### ATUALIZAR LISTA DE ALUNOS NO BANCO DE DADOS :old_key:")

st.write("## Fomulário de login")

series_data = None

if series_data is None:
  username = st.text_input("usuário")
  password = st.text_input("senha", type="password")

  if st.button("logar"):
    payload = {'username': username, 'password': password}
    with httpx.Client() as client:
      response = client.post("https://freq-willapp.herokuapp.com/token",
                             data=payload)

    if response.status_code == 200:
      data = response.json()
      prof = data['prof_user']
      st.success("Login realizado com sucesso!")
      if prof['isAdmin']:
        series_data = pd.Series(data)
      else:
        st.warning('porém você não é usuário admin.!')
    else:
      st.error(
        "falha na tentativa de login. Por favor verifique suas credenciais!")


def download_button(data_to_serialize):
  buffer = io.BytesIO()
  pickle.dump(data_to_serialize, buffer)
  buffer.seek(0)
  st.download_button(label="Download chave de acessono!",
                     data=buffer,
                     file_name="login_data.pkl",
                     mime="application/octet-stream")


try:
  to_next = (not series_data == None)
except ValueError:
  to_next = series_data.any()
if to_next:
  download_button(series_data)
