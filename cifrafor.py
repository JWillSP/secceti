import datetime
from pytz import timezone

def gera_cifra(student_id):
    now = datetime.datetime.now(tz=timezone('America/Sao_Paulo'))
    day_of_week = str(now.weekday() + 2)
    day_of_month = str(now.day)
    if int(day_of_month) < 10:
        day_of_month = '0' + day_of_month

    ciphertext = student_id[-3:] + day_of_week + day_of_month 
    return ciphertext