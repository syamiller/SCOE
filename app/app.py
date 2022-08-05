import streamlit as st
import plotly.graph_objects as go
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode
from helpers import load_data, get_grouped_data, get_player_data, create_fig


st.set_page_config(layout='wide')

data, logos = load_data()

st.title('''
Strike Rate Over Expected This Season :fire:
''')

col1, padding, col2 = st.columns((10,2,10))

with col1:
    choice = st.selectbox(
    "Choose a Position",
    ['Catchers', 'Pitchers', 'Batters']
    )

    grouped_data = get_grouped_data(choice, data)

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

with col2:
    try:
        sroe, selected, player_data, player_id = get_player_data(grid_response, data, choice)
        fig = create_fig(sroe, selected, player_data, player_id)
        st.plotly_chart(fig)
    except:
        st.warning('Select a player to see their strike zone chart')
