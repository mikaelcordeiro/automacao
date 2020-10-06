import sqlite3


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

        'Alunos já preenchidos :)'

    return banco.commit()


def gerar_df() -> list:
    banco = sqlite3.connect('banco_dados/teste.db')

    cursor = banco.cursor()

    cursor.execute("""SELECT * FROM medias_totais""")

    return cursor.fetchall()
