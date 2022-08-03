from tokenize import group
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from PIL import Image
import requests
from io import BytesIO
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode


@st.cache()
def load_data():
    data = pd.read_csv('data/shadow_zone_data_2022.csv')
    return data

data = load_data()


st.title('Strikes Called Over Expected So Far 2022')
choice = st.selectbox(
    "Choose a Position",
    ['Catchers', 'Pitchers', 'Batters']
)


if choice == 'Catchers':
    grouped_data = data[['catcher_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['catcher_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'catcher_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()
elif choice == 'Pitchers':
    grouped_data = data[['pitcher_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['pitcher_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'pitcher_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()
else:
    grouped_data = data[['batter_name', 'pitch_number', 'called_strike', 'strike_proba']].groupby(['batter_name']).agg({'pitch_number' : 'count', 'called_strike' : 'sum', 'strike_proba' : 'sum'}).rename(columns={'batter_name' : 'name', 'strike_proba' : 'expected_strikes'}).reset_index()

grouped_data = grouped_data[grouped_data['pitch_number'] > 100]

# if choice == 'Catchers':
#     catchers = grouped_data.name.tolist()
#     pitchers = []
#     batters = []
# elif choice == 'Pitchers':
#     pitchers = grouped_data.name.tolist()
#     catchers = []
#     batters = []
# else:
#     batters = grouped_data.name.tolist()
#     catchers = []
#     pitchers = []


# lookup_dict = {'Catchers' : catchers, 'Pitchers' : pitchers, 'Batters' : batters}

# player_choice = st.selectbox("Choose a Player", lookup_dict[choice])


grouped_data['total_strikes_OE'] = grouped_data['called_strike'] - grouped_data['expected_strikes']
grouped_data['strike_rate'] = grouped_data['called_strike'] / grouped_data['pitch_number']
grouped_data['expected_strike_rate'] = grouped_data['expected_strikes'] / grouped_data['pitch_number']
grouped_data['strike_rate_OE'] = grouped_data['strike_rate'] - grouped_data['expected_strike_rate']
grouped_data = grouped_data.sort_values('strike_rate_OE', ascending=False)
grouped_data['strike_rate_OE'] = grouped_data['strike_rate_OE'] * 100
grouped_data[['expected_strikes', 'total_strikes_OE', 'strike_rate', 'expected_strike_rate', 'strike_rate_OE']] = grouped_data[['expected_strikes', 'total_strikes_OE', 'strike_rate', 'expected_strike_rate', 'strike_rate_OE']].round(2)
# st.write(grouped_data.reset_index().drop(['index'], 1).style.background_gradient(subset='strike_rate_OE'))
gb = GridOptionsBuilder.from_dataframe(grouped_data.drop(columns=['total_strikes_OE', 'strike_rate', 'expected_strike_rate'], axis=1))
gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
gb.configure_selection('single', use_checkbox=True)
col_name = grouped_data.columns.tolist()[0] 
gb.configure_column(col_name, )
gridOptions = gb.build()


grid_response = AgGrid(
    grouped_data.drop(columns=['total_strikes_OE', 'strike_rate', 'expected_strike_rate'], axis=1),
    gridOptions=gridOptions,
    data_return_mode='AS_INPUT', 
    update_mode='MODEL_CHANGED', 
    fit_columns_on_grid_load=False,
    theme='streamlit', #Add theme color to the table
    height=350, 
    width='100%',
    reload_data=True
)


try:

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


    st.write(f'''
    # Strike Rate Over Expected: {str(sroe)}%
    ''')
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
        title = f"Shadow Zone Pitches for {selected}"
    )

    st.plotly_chart(fig)

except:

    st.warning('Select a player to see their strike zone chart')
