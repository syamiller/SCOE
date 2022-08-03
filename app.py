import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO


@st.cache()
def load_data():
    df_2021 = pd.read_csv('data_2021.csv')
    return df_2021

df_2021 = load_data()

catchers = df_2021.catcher_name.unique()
pitchers = df_2021.pitcher_name.unique()
batters = df_2021.batter_name.unique()


lookup_dict = {'Catchers' : catchers, 'Pitchers' : pitchers, 'Batters' : batters}

st.header('Strikes Called Over Expected 2021 Season')
choice = st.selectbox(
    "Choose a Position",
    lookup_dict.keys()
)

player_choice = st.selectbox("Choose a Player", lookup_dict[choice])

fig = go.Figure()

if choice == 'Catchers':
    player_data = df_2021[df_2021['catcher_name'] == player_choice]
    player_id = player_data.fielder_2.tolist()[0]
elif choice == 'Pitchers':
    player_data = df_2021[df_2021['pitcher_name'] == player_choice]
    player_id = player_data.pitcher.tolist()[0]
else:
    player_data = df_2021[df_2021['batter_name'] == player_choice]
    player_id = player_data.batter.tolist()[0]



fig.add_trace(
    go.Scatter(
        x = player_data[player_data['called_strike'] == 1].plate_x,
        y = player_data[player_data['called_strike'] == 1].y,
        mode = 'markers',
        name = 'Called Strike',
        marker=dict(
            color = 'black',
            size = player_data[player_data['called_strike'] == 1].strike_proba * 10 + 2
        )
    )
)

fig.add_trace(
    go.Scatter(
        x = player_data[player_data['called_strike'] == 0].plate_x,
        y = player_data[player_data['called_strike'] == 0].y,
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
mid = (avg_top + avg_bot) / 2

resp = requests.get(f'https://img.mlbstatic.com/mlb-photos/image/upload/q_100/v1/people/{player_id}/headshot/67/current')
img = Image.open(BytesIO(resp.content))

fig.add_shape(type='rect', x0=-0.83333, x1=0.83333, y0=avg_bot-mid, y1=avg_top-mid, line=dict(color='black'))

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
    title = f"Shadow Zone Pitches for {player_choice}"
)

st.plotly_chart(fig)
