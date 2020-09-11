import streamlit as st
import pandas as pd
import time
from datetime import timedelta, date


def config():

    return st.set_option('deprecation.showfileUploaderEncoding', False)


@st.cache(suppress_st_warning=True)
def leitura(file):
    df = pd.read_excel(file, header=0, usecols="A, D, F, G, I, M, N, S")

    return df


def list_date(label):
    dates = st.sidebar.select_slider(label, options=[dt.strftime("%d/%m/%Y") for dt in daterange(date(2020, 8, 1), date(2020, 12, 31))])

    return dates


def date_datetime(date):

    return pd.to_datetime(date, errors='coerce', format='%d/%m/%Y')


def progresso(tempo=.13):
    bar = st.sidebar.progress(0)

    for i in range(100):
        bar.progress(i + 1)
        time.sleep(tempo)


def daterange(date1, date2):
    for n in range(int((date2 - date1).days)+1):
        yield date1 + timedelta(n)


def retirando_datas(dataframe: pd.DataFrame):
    datas = [i[-10:] for i in dataframe]

    datas = pd.Series(datas, name='Datas')

    return pd.to_datetime(datas, errors='coerce', format='%d/%m/%Y')


def tipos_de_atividade(df: pd.DataFrame, disciplinas: list):
    atividades_por_materia = dict()

    selecionadas_por_materia = dict()

    for materia in disciplinas:
        atividades_por_materia[materia] = df[df['Caderno'] == materia]['Tipo do conteúdo'].unique()

        selecionadas_por_materia[materia] = st.multiselect(f'Selecione os tipos de conteúdo desejados de {materia}',
                                                           atividades_por_materia[materia])

    return selecionadas_por_materia


def dashboard():

    config()

    st.title('Associação Marie Curie Vestibulares')

    'Dashboard para acompanhar o progresso dos alunos'

    st.sidebar.subheader('Comece bem aqui a sua análise')

    st.sidebar.write('Escolha o intervalo de datas')

    data_zero = list_date("Data Inicial")

    data_um = list_date("Data Final")

    data_zero_datetime = date_datetime(data_zero)

    data_um_datetime = date_datetime(data_um)

    file = st.sidebar.file_uploader('Arraste a planilha, ou clique em "browse files"')

    if file is not None:

        df = leitura(file)

#        progresso()

        datas = retirando_datas(df['Conteúdo'])

        df = df.join(datas)

        df = df[df["Datas"].between(data_zero_datetime, data_um_datetime)]

        disciplinas = st.sidebar.multiselect('Selecione as disciplinas desejadas',
                                     df['Caderno'].unique())

        df = df[(df['Caderno'].isin(disciplinas) & (df['Status da seção'] == 'aberta'))]

        tipos_selecionados = tipos_de_atividade(df, disciplinas)

        if st.button('Gerar Tabela'):

            tipos_selecionados


if __name__ == '__main__':

    dashboard()
