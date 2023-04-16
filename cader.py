from openpyxl import load_workbook
import io
from turmasdetalhes import turmastd

#   if lfreq.shape[0] > 46:
#     source_filename = r'./static/Merged_fileVersionXL.xlsx'
# else:
#     source_filename = r'./static/Merged_file.xlsx'

source_filename = r'./statics/Merged_file.xlsx'


def do_cader(lfreq, turma, componente, professor, unidade):
  naulas_dadas = ''
  naulas = ''
  t_dict = turmastd.get(turma, {})
  turno = t_dict.get('TURNO')
  modalidade = t_dict.get('MODALIDADE')
  oferta_do_ensino = t_dict.get('TURNO')
  serie = t_dict.get('ANO/SERIE/OUTROS')
  wb = load_workbook(filename=source_filename)
  ws1 = wb['diario']
  ws2 = wb['conteudo']

  ws1['A3'] = f'Ano/Série/Outros: {serie}'
  ws1['J2'] = f'Modalidade: {modalidade}'
  ws1['J3'] = f'Turma: {turma}'
  ws1['AH2'] = f'Oferta do Ensino: {oferta_do_ensino}'
  ws1['AH3'] = f'Turno: {turno}'
  ws1['A4'] = f'Componente: {componente}'
  ws1['A5'] = f'Unidade: {unidade}'
  ws1['J4'] = f'Professor: {professor}'
  ws1['J5'] = f'Aulas Previstas: {naulas}'
  ws1['AH5'] = f'Aulas Dadas: {naulas_dadas}'

  for row, nome in enumerate(lfreq):
    ws1[F'B{row + 9}'] = nome

  ws2['A3'] = f'Ano/Série/Outros: {serie}'
  ws2['J2'] = f'Modalidade: {modalidade}'
  ws2['J3'] = f'Turma: {turma}'
  ws2['AH2'] = f'Oferta do Ensino: {oferta_do_ensino}'
  ws2['AH3'] = f'Turno: {turno}'
  ws2['A4'] = f'Componente: {componente}'
  ws2['A5'] = f'Unidade: {unidade}'
  ws2['J4'] = f'Professor: {professor}'
  ws2['J5'] = f'Aulas Previstas: {naulas}'
  ws2['AH5'] = f'Aulas Dadas: {naulas_dadas}'

  buffer = io.BytesIO()
  wb.save(buffer)
  bytes_data = buffer.getvalue()
  buffer.close()
  return bytes_data