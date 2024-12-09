import streamlit as st
import pandas as pd
import numpy as np
import requests
from typing import Annotated, List
from enum import Enum
from sqlmodel import Session, create_engine, select, Field, SQLModel

tables = [v for k,v in SQLModel.metadata.tables.items()]
for t in tables:
   SQLModel.metadata.remove(t)

class Source(str, Enum):
    core = 'Основная Книга Правил'
    Sand_and_Dust = 'Песок и Пыль'
    Power_And_Pawns_Emperors_Court = 'Власть и Пешки: Императорский Двор'
    The_Great_Game_Houses_of_the_Landsraad = 'Великая Игра: Дома Ландсраада'

class Talent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default=None, index=True)
    source: Source = Field(default=None, index=True)
    requirements: str | None = Field(default=None, index=True)
    flavor: str = Field(default=None, index=True)
    text: str = Field(default=None, index=True)

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///db/{sqlite_file_name}"

engine = create_engine(sqlite_url)

@st.cache_resource
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@st.cache_data
def read_talents():
    with Session(engine) as session:
        talents = session.exec(select(Talent).order_by(Talent.name)).all()
    return pd.DataFrame.from_records(list(map(dict, talents)))

@st.cache_data
def search_talents(**kwargs):
    with Session(engine) as session:
        statement = select(Talent)
        if name:
            statement = statement.where(Talent.name.like('%' + name + '%'))
        if source:
            statement = statement.where(Talent.source == Source(source))
        if requirements:
            statement = statement.where(Talent.requirements.like('%' + requirements + '%'))
        if flavor:
            statement = statement.where(Talent.flavor.like('%' + flavor + '%'))
        if text:
            statement = statement.where(Talent.text.like('%' + text + '%'))
        talents = session.exec(statement).all()
    return pd.DataFrame.from_records(list(map(dict, talents)))

def set_table(df):
    st.session_state.table = st.table(df)

@st.cache_data
def treat_df(df):
    df['requirements'] = df['requirements'].apply(lambda r: r if r else 'Нет')
    columns = {
        'name': 'Название',
        'source': 'Источник',
        'requirements': 'Требование',
        'text': 'Текст',
        'flavor': 'Описание'
        }
    df = df.rename(columns=columns)[columns.values()]
    return df

def reset():
    submit = False

if __name__ == '__main__':
    st.set_page_config(page_title='Сборник талантов', page_icon='./public/dune_logo.ico', layout="wide")

    st.title('Сборник талантов игры Дюна: Приключения в Империи')

    st.sidebar.header('Поиск талантов')
    with st.sidebar.form('Поиск талантов'):
        name = st.text_input('Название', key='name')
        source = st.selectbox('Источник', 
            ('Основная Книга Правил',
             'Песок и Пыль',
             'Великая Игра: Дома Ландсраада',
             'Власть и Пешки: Императорский Двор'
            ), index=None, placeholder='Выберете талант...')
        requirements = st.text_input('Требование', key='requirements')
        text = st.text_input('Текст', key='text')
        flavor = st.text_input('Описание', key='flavor')
        submit = st.form_submit_button('Поиск')
    
    if submit:
        kwargs = {'name': name, 'source': source, 'requirements': requirements, 'text': text, 'flavor': flavor}
        try:
            set_table(treat_df(search_talents(**kwargs)))
        except KeyError:
            st.write('По вашему запросу ничего не найдено!\n Пожалуйста, нажмите кнопку "Сбросить"')
    else:
        set_table(treat_df(read_talents()))

    st.sidebar.button('Сбросить', key='reset', on_click=reset)
