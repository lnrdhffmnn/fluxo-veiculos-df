import altair as alt
import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup

BASE_URL = 'https://dados.gov.br'
DATASET_URL = BASE_URL + '/dataset/volume-medio-diario-de-trafego'
ROADS_URL = BASE_URL + '/dataset/3cb44f4a-576c-45b8-8f13-ae94a6623277/resource/2bd0f48e-d3a1-47c6-bd12-83aed24e9461/download/2022-08-18-scr.csv'
CSV_ENCODING = 'latin-1'


def format_key(x: str) -> str:
    x = x.strip().removesuffix('CSV')
    x = x.split(' ')[-1].replace('/', ' de ')
    x = x.capitalize()

    return x


@st.cache
def load_ranges() -> dict[str, str]:
    ranges = {}
    r = requests.get(DATASET_URL)

    soup = BeautifulSoup(r.text, 'lxml')

    li_list = soup.select('li.resource-item')

    for li in li_list:
        key = format_key(li.select_one('a.heading').get_text())

        value = li.select_one('a.resource-url-analytics')
        value = value['href'].split('url=')[1]

        ranges[key] = value

    return ranges


@st.cache
def load_data(csv_url: str):
    df = pd.read_csv(csv_url, encoding=CSV_ENCODING)
    return df


@st.cache
def load_roads(road_list: list[str] = []) -> dict[str, str]:
    roads = {}
    df = pd.read_csv(ROADS_URL, delimiter=';')

    df['TRECHO'] = df['INÍCIO'] + ' <=> ' + df['FIM']
    filtered_df = df[['COD. TRECHO', 'TRECHO']].sort_values(by='TRECHO')

    for _, row in filtered_df.iterrows():
        if len(road_list) > 0 and row['COD. TRECHO'] in road_list:
            roads[row['TRECHO']] = row['COD. TRECHO']

    return roads


def main():
    st.title('Fluxo de veículos no DF')

    ranges = load_ranges()
    time_range = st.sidebar.selectbox(
        'Intervalo de tempo',
        ranges.keys()
    )

    data = load_data(ranges[time_range])
    roads = load_roads(list(data['Trecho'].drop_duplicates()))

    vehicle_type = st.sidebar.selectbox(
        'Tipo de veículo',
        data['Porte'].drop_duplicates().sort_values()
    )
    road = st.sidebar.selectbox(
        'Trecho',
        roads.keys()
    )

    filtered_data = data[
        (data['Porte'] == vehicle_type) &
        (data['Trecho'] == roads[road])
    ].groupby(['Trecho', 'Intervalo', 'Porte']).sum().reset_index()

    st.caption(' / '.join([vehicle_type, road, time_range]))

    alt_chart = alt.Chart(filtered_data).mark_bar().encode(
        x='Intervalo',
        y='Fluxo',
        color='Fluxo',
        tooltip=['Intervalo', 'Fluxo', 'Porte']
    ).interactive()
    st.altair_chart(alt_chart, use_container_width=True)

    with st.expander('Amostra dos dados brutos'):
        st.dataframe(data.head(10), use_container_width=True)


if __name__ == '__main__':
    main()
