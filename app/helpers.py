import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO


@st.cache()
@st.experimental_singleton()
def load_data():
    data = pd.read_csv('app/data/shadow_zone_data_2022.csv', low_memory=False)
    logos = pd.read_csv('app/data/team_logos.csv')
    return data, logos



@st.cache()
def get_grouped_data(choice, data):
    if choice == 'Catchers':
        grouped_data = data[['catcher_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['catcher_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'catcher_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()
    elif choice == 'Pitchers':
        grouped_data = data[['pitcher_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['pitcher_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'pitcher_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()
    else:
        grouped_data = data[['batter_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['batter_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'batter_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()

    grouped_data['total_strikes_OE'] = grouped_data['called_strike'] - grouped_data['expected_strikes']
    grouped_data['strike_rate'] = grouped_data['called_strike'] / grouped_data['pitch_number']
    grouped_data['expected_strike_rate'] = grouped_data['expected_strikes'] / grouped_data['pitch_number']
    grouped_data['strike_rate_OE'] = grouped_data['strike_rate'] - grouped_data['expected_strike_rate']
    grouped_data = grouped_data.sort_values('strike_rate_OE', ascending=False)
    grouped_data['strike_rate_OE'] = grouped_data['strike_rate_OE'] * 100
    grouped_data[['expected_strikes', 'total_strikes_OE', 'strike_rate', 'expected_strike_rate', 'strike_rate_OE']] = grouped_data[['expected_strikes', 'total_strikes_OE', 'strike_rate', 'expected_strike_rate', 'strike_rate_OE']].round(2)

    return grouped_data[grouped_data['pitch_number'] > 150]


@st.cache()
def get_player_data(grid_response, data, choice):
    sroe = grid_response['selected_rows'][0]['strike_rate_OE']

    if choice == 'Catchers':
        selected = grid_response['selected_rows'][0]['catcher_name']
        player_data = data[data['catcher_name'] == selected]
        player_id = player_data.fielder_2.tolist()[0]
    elif choice == 'Pitchers':
        selected = grid_response['selected_rows'][0]['pitcher_name']
        player_data = data[data['pitcher_name'] == selected]
        player_id = player_data.pitcher.tolist()[0]
    else:
        selected = grid_response['selected_rows'][0]['batter_name']
        player_data = data[data['batter_name'] == selected]
        player_id = player_data.batter.tolist()[0]

    return sroe, selected, player_data, player_id


@st.cache()
def create_fig(sroe, selected, player_data, player_id):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x = player_data[player_data['called_strike'] == 1].plate_x,
            y = player_data[player_data['called_strike'] == 1].plate_z,
            mode = 'markers',
            name = 'Called Strike',
            marker=dict(
                color = 'green',
                size = player_data[player_data['called_strike'] == 1].strike_proba * 10 + 2
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x = player_data[player_data['called_strike'] == 0].plate_x,
            y = player_data[player_data['called_strike'] == 0].plate_z,
            mode = 'markers',
            name = 'Ball',
            marker=dict(
                color = 'red',
                size = player_data[player_data['called_strike'] == 0].strike_proba * 10 + 2
            )
        )
    )

    avg_top = player_data.sz_top.mean()
    avg_bot = player_data.sz_bot.mean()

    resp = requests.get(f'https://img.mlbstatic.com/mlb-photos/image/upload/q_100/v1/people/{player_id}/headshot/67/current')
    img = Image.open(BytesIO(resp.content))

    fig.add_shape(type='rect', x0=-0.83333, x1=0.83333, y0=avg_bot, y1=avg_top, line=dict(color='black'))

    fig.add_layout_image(dict(
            source=img,
            xref="paper", yref="paper",
            x=1.2, y=0.65,
            sizex=0.2, sizey=0.2,
            xanchor="right", yanchor="bottom"
        ))

    fig.update_layout(
        height=750,
        width=750,
        margin=dict(r=20, l=100, b=75, t=125),
        title = f"Shadow Zone Pitches for {selected} - Strike Rate Over Expected: {sroe}%"
    )

    return fig

