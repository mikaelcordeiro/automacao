import base64
import time
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


def date_datetime(date):
    return pd.to_datetime(date, errors='coerce', format='%d/%m/%Y')


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


def evolucao(dados: pd.DataFrame) -> pd.DataFrame:
    st.warning('Escolha o intervalo mais recente primeiro :wink:')

    escolhas = st.multiselect('Escolha DOIS intervalos de datas:', dados.columns)

    if len(escolhas) == 2:

        df_evolucao = dados[escolhas]

        df_evolucao['Evolucao'] = df_evolucao[escolhas[0]] - df_evolucao[escolhas[1]]

        return df_evolucao

    else:

        with st.spinner(f'{len(escolhas)} intervalo escolhido, faltam {2 - len(escolhas)} :stuck_out_tongue:'):

            time.sleep(1.3)


def grafico(dados: pd.DataFrame, aluno: str) -> pd.DataFrame:

    return dados.loc[aluno, :]


def melhora_piora(dados: pd.DataFrame) -> pd.DataFrame:
    n_alunos_melhoraram = []

    n_alunos_pioraram = []

    for i in range(dados.columns.size):

        if i == 0:

            n_alunos_melhoraram.append('-')

            n_alunos_pioraram.append('-')

        else:

            n_alunos_melhoraram.append(dados[dados.iloc[:, i] > dados.iloc[:, i - 1]].shape[0])

            n_alunos_pioraram.append(dados[dados.iloc[:, i] < dados.iloc[:, i - 1]].shape[0])

    return pd.DataFrame(columns=dados.columns,
                 data=[n_alunos_melhoraram, n_alunos_pioraram],
                 index=['Número de alunos que MELHORARAM', 'Número de alunos que PIORARAM'])


def downloader(df: pd.DataFrame, texto: str):
    csv = df.to_csv(index=True)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f"<a href='data:file/csv;base64,{b64}'>{texto}</a>"
    return href


def dashboard():
    config()

    st.image('imagens/principal.png', width=600)

    st.subheader('Dashboard para acompanhar o progresso dos alunos')

    st.sidebar.image('imagens/logo_grande.png', use_column_width=True)

    st.sidebar.subheader('Escolha o intervalo de datas')

    data_zero = st.sidebar.date_input(label='Escolha a data inicial',
                              value=date(2020, 2, 1),
                              min_value=date(2020, 2, 1),
                              max_value=date(2020, 12, 31))

    data_um = st.sidebar.date_input(label='Escolha a data final',
                              value=date(2020, 7, 1),
                              min_value=date(2020, 2, 1),
                              max_value=date(2020, 12, 31))

    data_zero_datetime = date_datetime(data_zero.strftime("%d/%m/%Y"))

    data_um_datetime = date_datetime(data_um.strftime("%d/%m/%Y"))

    file = st.sidebar.file_uploader('Arraste a planilha, ou clique em "browse files"')

    if file is not None:

        df = leitura(file)

        datas = retirando_datas(df['Conteúdo'])

        df = df.join(datas)

        df = df[df["Datas"].between(data_zero_datetime, data_um_datetime)]

        disciplinas = st.sidebar.multiselect('Selecione as disciplinas desejadas',
                                             df['Caderno'].unique())

        df = df[(df['Caderno'].isin(disciplinas) & (df['Status da seção'] == 'aberta'))]

        tipos_selecionados = tipos_de_atividade(df, disciplinas)

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

        tabela

        st.markdown(downloader(tabela, texto='Aperte aqui para baixar a Tabela de Progresso em formato .csv'),
                    unsafe_allow_html=True)

        banco.producao_banco(media_total=tabela['Média Total'].tolist()[:-2], alunos=df['Aluno'].unique().tolist())

        banco.adiciona_media_geral(media_total=tabela['Média Total'].tolist()[:-2], data_inicial=data_zero, data_final=data_um)

        df_banco = banco.gerar_df()  # tabela crua que veio do banco de dados

        tabela_tres = melhora_piora(dados=df_banco)

        st.subheader('Gráfico de Médias Totais das semanas analisadas')

        escolhido = st.selectbox('Escolha um aluno', df_banco.index)

        st.line_chart(grafico(df_banco, escolhido).dropna())

        st.markdown(downloader(df_banco.append(tabela_tres),
                                   texto='Aperte aqui para baixar a tabela de Médias Totais em formato .csv'),
                        unsafe_allow_html=True)

        st.subheader('Tabela de Médias Totais e Evolução das semanas escolhidas')

        df_evolucao = evolucao(dados=df_banco)

        if df_evolucao is not None:
            df_evolucao

            st.markdown(downloader(df_evolucao['Evolucao'],
                                           texto='Aperte aqui para baixar a coluna Evolução em formato .csv'),
                                unsafe_allow_html=True)


if __name__ == '__main__':
    dashboard()
