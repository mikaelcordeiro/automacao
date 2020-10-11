import sqlite3
import time
import streamlit as st
import pandas as pd


def producao_banco(alunos: list, media_total: list):
    banco = sqlite3.connect('banco_dados/teste.db')

    cursor = banco.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS medias_totais(

                        ID tinyint unsigned not null, 

                        Aluno varchar(70) not null, 

                        primary key(ID))""")

    try:

        for y, x in enumerate(alunos):

            cursor.execute(f"""INSERT INTO medias_totais (ID, Aluno) VALUES ('{y}', '{x}')""")

    except:

        with st.spinner('Alunos já preenchidos :smile:'):

            time.sleep(1.3)

    finally:

        return banco.commit()


def gerar_df() -> pd.DataFrame:
    banco = sqlite3.connect('banco_dados/teste.db')

    cursor = banco.cursor()

    cursor.execute("""SELECT * FROM medias_totais""")

    colunas_banco = [i[0] for i in cursor.description]

    df_banco = pd.DataFrame(cursor.fetchall(), columns=colunas_banco).drop(columns=['ID']).set_index('Aluno')

    return df_banco


def adiciona_media_geral(media_total: list, data_inicial, data_final):
    banco = sqlite3.connect('banco_dados/teste.db')

    cursor = banco.cursor()

    try:

        cursor.execute(
            f"""ALTER TABLE medias_totais ADD COLUMN '{data_inicial}-{data_final}' DECIMAL(1,4)""")

        for i, media in enumerate(media_total):

            cursor.execute(f"""UPDATE medias_totais 

                                set '{data_inicial}-{data_final}' = {media} 

                                where ID = {i}""")

    except:

        with st.spinner('Esse intervalo de datas já existe no banco de dados :stuck_out_tongue:'):

            time.sleep(1.3)

    finally:

        return banco.commit()
