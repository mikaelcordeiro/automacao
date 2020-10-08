import time
import base64
import streamlit as st
import pandas as pd
from banco_dados import banco
from datetime import timedelta, date


def config():
    return st.set_option('deprecation.showfileUploaderEncoding', False)


@st.cache(suppress_st_warning=True)
def leitura(file):
    df = pd.read_excel(file, header=0, usecols="A, D, F, G, I, M, N, S")

    return df


def list_date(label):
    dates = st.sidebar.select_slider(label, options=[dt.strftime("%d/%m/%Y") for dt in
                                                     daterange(date(2020, 2, 1), date(2020, 12, 31))])

    return dates


def date_datetime(date):
    return pd.to_datetime(date, errors='coerce', format='%d/%m/%Y')


def progresso(tempo=.13):
    bar = st.sidebar.progress(0)

    for i in range(100):
        bar.progress(i + 1)
        time.sleep(tempo)


def daterange(date1, date2):
    for n in range(int((date2 - date1).days) + 1):
        yield date1 + timedelta(n)


def retirando_datas(dataframe: pd.DataFrame):
    datas = [i[-10:] for i in dataframe]

    datas = pd.Series(datas, name='Datas')

    return pd.to_datetime(datas, errors='coerce', format='%d/%m/%Y')


def tipos_de_atividade(df: pd.DataFrame, disciplinas: list) -> dict:
    atividades_por_materia = dict()

    selecionadas_por_materia = dict()

    for materia in disciplinas:
        atividades_por_materia[materia] = df[df['Caderno'] == materia]['Tipo do conteúdo'].unique()

        selecionadas_por_materia[materia] = st.multiselect(f'Selecione os tipos de conteúdo desejados de {materia}',
                                                           atividades_por_materia[materia])

    return selecionadas_por_materia


def resumo_disciplinas(dados: pd.DataFrame) -> pd.DataFrame:
    media_disciplina = dados.mean(axis=0).round(2)

    numero_acessos = dados[dados != 0].count(axis=0)

    tabela = pd.DataFrame(columns=media_disciplina.index,
                          data=[media_disciplina.values, numero_acessos],
                          index=['Média de Acesso por Caderno', 'Número de Acesso por Caderno '])

    return tabela


def downloader(df: pd.DataFrame, texto: str):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f"<a href='data:file/csv;base64,{b64}'>{texto}</a>"
    return href


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

            st.subheader(f'Tabela de Progresso entre as datas {data_zero} - {data_um}')

            tabela = pd.DataFrame(index=df['Aluno'].unique())

            for materia in tipos_selecionados.keys():

                notas = list()

                for aluno in df['Aluno'].unique():

                    medias_do_aluno = list()

                    for selecionado in tipos_selecionados[materia]:
                        media = df[(df['Caderno'] == materia)
                                   & (df['Tipo do conteúdo'] == selecionado)
                                   & (df['Aluno'] == aluno)]['Progresso'].mean()

                        medias_do_aluno.append(media)

                    notas.append(max(medias_do_aluno))

                tabela[materia] = notas

            tabela['Média Total'] = tabela.mean(axis=1)

            tabela_dois = resumo_disciplinas(tabela)

            tabela = tabela.append(tabela_dois.iloc[:, :])

            tabela  # colocar cor aqui

            st.markdown(downloader(tabela, texto='Aperte aqui para baixar a Tabela de Progresso em formato .csv'),
                        unsafe_allow_html=True)

            st.subheader('Tabela de Médias Totais e Evolução das semanas analisadas')

            banco.producao_banco(media_total=tabela['Média Total'].tolist()[:-2], alunos=df['Aluno'].unique().tolist())

            banco.adiciona_media_geral(media_total=tabela['Média Total'].tolist()[:-2], data_inicial=data_zero, data_final=data_um)

            df_banco = banco.gerar_df()

            df_banco

            st.markdown(downloader(df_banco, texto='Aperte aqui para baixar a tabela de Médias Totais em formato .csv'),
                        unsafe_allow_html=True)


if __name__ == '__main__':
    dashboard()
