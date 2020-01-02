''' Description:
by: Joel A. Gongora
date:12/29/2019
'''

import dash
from dash.dependencies import Output, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import psycopg2
from collections import deque
import pandas as pd
# import dash_bootstrap_components as dbc
from os.path import abspath
import sys
from flask_app import my_app



# if not abspath('../utils/') in sys.path:
#     sys.path.append(abspath('../utils/'))
from myconfig import db_config

dash_app = dash.Dash(
    __name__,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0"
        }
    ],
    server=my_app,
    url_base_pathname='/snotel_dashboard/'
)

mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNqdnBvNDMyaTAxYzkzeW5ubWdpZ2VjbmMifQ.TXcBE-xg9BFdV2ocecc_7g"
mapbox_style = "mapbox://styles/plotlymapbox/cjvprkf3t1kns1cqjxuxmwixz"

# Joel's Version #
# mapbox_access_token = "pk.eyJ1IjoiamdvbmdvcmEiLCJhIjoiY2p6bDd0c2c3MHNycDNjcHBoanE3bWxvdCJ9.96Kl63kGmTtmlsvTHKu6Ig"
# mapbox_style = "https://api.mapbox.com/styles/v1/jgongora/ck4spcbw01zc01cmk4dbgkzrm.html?fresh=true&title=copy&access_token=pk.eyJ1IjoiamdvbmdvcmEiLCJhIjoiY2p6bDd0c2c3MHNycDNjcHBoanE3bWxvdCJ9.96Kl63kGmTtmlsvTHKu6Ig#14.0/37.268600/-112.942500/0"

server = dash_app.server

def query_load_data(sql_command=None):
    conn = psycopg2.connect(
        host=db_config['host'],
        user=db_config['user'],
        password='',
        dbname=db_config['dbname']
    )
    
    datos = pd.read_sql(sql_command, conn)
    datos.sort_index(inplace=True)
    conn.close()
    return datos


cols = [
    'date',
    'snow_water_equivalent_in_start_of_day_values',
    'precipitation_accumulation_in_start_of_day_values',
    'air_temperature_maximum_degf',
    'air_temperature_minimum_degf',
    'air_temperature_average_degf',
    'precipitation_increment_in',
    'site_name',
    'state'
]

# ------------ #
# Query States #
# ------------ #

query_state = '''SELECT state FROM snotel '''
estados = query_load_data(
    query_state
)['state'].unique().tolist()


# --------------------------- #
# Query Single State and Site #
# --------------------------- #

state = 'ID'
site = 'Bogus Basin'

sql_command = f'''SELECT {', '.join([str(col) for col
in [*cols]])} FROM snotel WHERE state='{state}'  AND site_name='{site}' '''

datos = query_load_data(sql_command).sort_values(by='date')
datos['year'] = datos.date.map(lambda x: int(x.strftime('%Y')))
YEARS = list(datos['year'].unique())

# --------------- #
# Query Locations #
# --------------- #
cols_locs = [
    'ntwk', 'state', 'site_name',
    'ts', 'start', 'lat',
    'lon', 'elev', 'county', 'huc'
]

sql_command = f'''SELECT {', '.join([str(col) for col
in [*cols_locs]])} FROM snotel_locs WHERE state='{state}' '''

datos_locs = query_load_data(sql_command)

dash_app.layout = html.Div(
    id="root",
    children=[
        # ------------------ #
        # Title of Dashboard #
        # ------------------ #        
        html.Div(
            id="header",
            children=[
                html.Img(
                    id="logo",
                    src=dash_app.get_asset_url(
                        "eri_2018_logo_stacked_medium_white.png"
                    ),
                    style = dict(
                        height='16%',
                        width='16%'
                    )
                    # width=200,
                    # height=200,
                ),
                html.Img(
                    id="bsulogo",
                    src=dash_app.get_asset_url("bsulogo_allwhite.png"),
                    style = dict(
                        height='6%',
                        width='6%'
                    )
                    # width=200,
                    # height=200,
                ),
                html.H4(children="NRCS Snotel: Snow Accumulation Graphs"),
                html.P(
                    id="description",
                    children="Snotel Meteorlogical Station Application",
                ),
            ],
        ),
        # ---------- #
        # Container  #
        # ---------- #
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            # ------------- #
                            # State Selector #
                            # ------------- #                            
                            id='state-container',
                            children=[
                                html.P(
                                    id='state-container-title',
                                    children=[
                                        html.P(
                                            "Select the State:",
                                        ),
                                    ],
                                ),
                                dcc.Dropdown(
                                    id="state-dropdown",                                    
                                    options=[
                                        {'label': i, 'value': i}
                                        for i in estados
                                    ],
                                    value='ID'
                                ),
                            ],style = {
                                "border-style": "solid",
                                "height": "10%",
                                "width": "100%",
                            },
                        ),
                        html.Div(
                            id="heatmap-container",
                            children=[
                                html.P(
                                    'Map of Snotel Locations',
                                    id="heatmap-title",
                                ),
                                dcc.Graph(
                                    id="snotel_map",
                                    figure=dict(),
                                ),
                            ],style = {
                                "border-style": "solid",
                                "height": "70%",
                                "width": "100%",
                                "fontsize":16
                            },
                        ),
                    ],
                ),
                # ---------- #
                # SWE Curves #
                # ---------- #
                html.Div(
                    id="right_column",
                    children= [
                        # ------------- #
                        # Site Selector #
                        # ------------- #                        
                        html.Div(
                            id='site-container',
                            children=[
                                html.P(
                                    id='site-container-title',                                    
                                    children=[
                                        html.P("Select a Site:")
                                    ],
                                ),
                                dcc.Dropdown(
                                    id="site-dropdown",                                    
                                    options=[
                                        {'label': i, 'value': i}
                                        for i in datos.loc[
                                                datos['state'] == state
                                        ]['site_name'].sort_values().unique()
                                    ],
                                    value='Bogus Basin'
                                ),
                            ],
                        ),
                        # ------------- #
                        # Year Selector #
                        # ------------- #                        
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                ),
                                dcc.RangeSlider(
                                    id="years-slider",
                                    min=min(YEARS),
                                    max=max(YEARS),
                                    value=[min(YEARS), max(YEARS)],
                                    marks={
                                        str(year): {
                                            "label": str(year),
                                            "style": {
                                                "color": "#7fafdf",
                                                "writing-mode": "vertical-rl"
                                            },
                                        }
                                        for year in YEARS                                        
                                    },
                                ),
                            ],
                            style={
                                'text-orientation': 'sideways', 
                                "border-style": "solid",
                            },
                        ),
                        
                        # ----------------- #
                        # Snotel Swe Curves #
                        # ----------------- #                        
                        html.Div(
                            children = [
                                html.H4('Measured SWE'),
                                dcc.Graph(
                                    id='example-graph',
                                    animate=True,
                                    figure=dict(
                                        data=[
                                            dict(
                                                x=datos['date'],
                                                y=datos['snow_water_equivalent_in_start_of_day_values'],
                                                type='scatter',
                                            )
                                        ],
                                        layout=go.Layout(
                                            # title = f'{datos["state"].unique()[0]}:' + \
                                            # f' {datos["site_name"].unique()[0]}',
                                        paper_bgcolor = 'rgba(0,0,0,0)',
                                            plot_bgcolor = 'rgba(0,0,0,0.1)',
                                            yaxis=dict(
                                                range=(
                                                    datos['snow_water_equivalent_in_start_of_day_values'].min(),
                                                    datos['snow_water_equivalent_in_start_of_day_values'].max(),
                                                ),
                                                title='Snow Water Equivalent (inches)',
                                                titlefont = dict(
                                                    color='lightgrey'
                                                ),
                                                tickfont = dict(
                                                    color='lightgrey'
                                                ),
                                            ),
                                            xaxis = dict(
                                                title = 'Dates',
                                                titlefont = dict(
                                                    color='lightgrey'
                                                ),
                                                tickfont = dict(
                                                    color='lightgrey'
                                                ),                                            
                                            ),
                                            scene=dict(
                                                xaxis=dict(
                                                    # backgroundcolor="rgb(200, 200, 230)",
                                                gridcolor="rgba(0,0,0, 0.1)",
                                                    showbackground=True,
                                                    zerolinecolor="rgba(0,0,0)",
                                                    tickwidth=1,
                                                    tickfont=dict(
                                                        color="white",
                                                    ),
                                                ),
                                                yaxis=dict(
                                                    # backgroundcolor="rgb(200, 200, 230)",
                                                gridcolor="rgba(0,0,0, 0.1)",
                                                    showbackground=False,
                                                    zerolinecolor="rgba(0,0,0,0.1)",
                                                    tickwidth=1,
                                                    tickfont=dict(
                                                        color="white",
                                                    ),
                                                    title='Snow Water Equivalent'
                                                ),                            
                                            ),
                                            margin={'t':0},
                                        ),
                                    ),
                                ),
                            ],
                        ),
                        # ----------------- #
                        # Snotel Swe Curves #
                        # ----------------- #                        
                        html.Div(
                            children=[
                                html.H4('Prophet Forecast'),
                                dcc.Graph(
                                    id='forecast-graph',
                                    animate=True,
                                    figure=dict(
                                        data=[
                                            dict(
                                                x=datos['date'],
                                                y=datos['snow_water_equivalent_in_start_of_day_values'],
                                                type='scatter',
                                            )
                                        ],
                                        layout=go.Layout(
                                            # title = f'{datos["state"].unique()[0]}:' + \
                                            # f' {datos["site_name"].unique()[0]}',
                                        paper_bgcolor = 'rgba(0,0,0,0)',
                                            plot_bgcolor = 'rgba(0,0,0,0.1)',
                                            yaxis=dict(
                                                range=(
                                                    datos['snow_water_equivalent_in_start_of_day_values'].min(),
                                                    datos['snow_water_equivalent_in_start_of_day_values'].max(),
                                                ),
                                                title='Snow Water Equivalent (inches)',
                                                titlefont = dict(
                                                    color='lightgrey'
                                                ),
                                                tickfont = dict(
                                                    color='lightgrey'
                                                ),
                                            ),
                                            xaxis = dict(
                                                title = 'Dates',
                                                titlefont = dict(
                                                    color='lightgrey'
                                                ),
                                                tickfont = dict(
                                                    color='lightgrey'
                                                ),                                            
                                            ),
                                            scene=dict(
                                                xaxis=dict(
                                                    # backgroundcolor="rgb(200, 200, 230)",
                                                gridcolor="rgba(0,0,0, 0.1)",
                                                    showbackground=True,
                                                    zerolinecolor="rgba(0,0,0)",
                                                    tickwidth=1,
                                                    tickfont=dict(
                                                        color="white",
                                                    ),
                                                ),
                                                yaxis=dict(
                                                    # backgroundcolor="rgb(200, 200, 230)",
                                                gridcolor="rgba(0,0,0, 0.1)",
                                                    showbackground=False,
                                                    zerolinecolor="rgba(0,0,0,0.1)",
                                                    tickwidth=1,
                                                    tickfont=dict(
                                                        color="white",
                                                    ),
                                                    title='Snow Water Equivalent'
                                                ),                            
                                            ),
                                        ),
                                    ),
                                ),
                            ],style={
                                "border-style": "solid",
                                "width": "100%"
                            },
                        ),
                    ],style={
                        "border-style": "solid",
                        "width": "80%",
                        "height": "94%"
                    },
                ),
            ],
        ),
    ],
)

@dash_app.callback(
    Output("snotel_map", "figure"),
    [Input("state-dropdown", "value")]
)
def update_snotel_map(state_value):
    cols = [
        'ntwk', 'state', 'site_name',
        'ts', 'start', 'lat',
        'lon', 'elev', 'county', 'huc'
    ]

    sql_command = f'''SELECT {', '.join([str(col) for col
    in [*cols]])} FROM snotel_locs WHERE state='{state_value}' '''

    datos_locs = query_load_data(sql_command)

    data=[
        dict(
            lat=datos_locs["lat"],
            lon=datos_locs["lon"],
            text=datos_locs["site_name"],
            type="scattermapbox",
        )
    ]

    layout=go.Layout(
	paper_bgcolor = 'rgba(0,0,0,0)',
	plot_bgcolor = 'rgba(0,0,0,0)',
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            center=dict(
                lat=datos_locs["lat"].mean(),
                lon=datos_locs["lon"].mean()
            ),
            zoom=3.5,
        ),
        autosize=True,
        margin={'t':0, 'b':0, 'r':0, 'l':0}
    )

    figure = {
        'data': data,
        'layout': layout
    }
    
    return figure


@dash_app.callback(
    Output("site-dropdown", "options"),
    [Input("state-dropdown", "value")]
)
def update_site_dropdown(state):
    sql_command = f'''SELECT {', '.join([str(col) for col
    in [*cols]])} FROM snotel WHERE state='{state}' '''

    datos = query_load_data(sql_command).sort_values(by='date')
    datos['year'] = datos.date.map(lambda x: int(x.strftime('%Y')))

    return [
        {'label': i, 'value': i}
        for i in datos.loc[
                datos['state'] == state
        ]['site_name'].unique()
    ]



@dash_app.callback(
    Output("example-graph", "figure"),
    [
        Input("state-dropdown", "value"),
        Input("site-dropdown", "value"),        
        Input("years-slider", "value")
    ],
    # events=[Event('graph-update', 'interval')]
)
def update_graph_scatter(state_value, site_value, year):

    labels = ['date', 'snow_water_equivalent_in_start_of_day_values']

    data = []                   # setup data for callback


    sql_command = f'''SELECT {', '.join([str(col) for col
    in [*cols]])} FROM snotel WHERE state='{state_value}' AND site_name='{site_value}' '''

    datos = query_load_data(sql_command).sort_values(by='date')
    datos['year'] = datos.date.map(lambda x: int(x.strftime('%Y')))    

    state_data = datos.loc[datos['state'] == state_value]

    data = [
        dict(
            x=state_data['date'].loc[
                (state_data['year'] > year[0]) & (state_data['year'] < year[1])
            ],
            y=state_data['snow_water_equivalent_in_start_of_day_values'].loc[
                (state_data['year'] > year[0]) & (state_data['year'] < year[1])
            ],
            type='scatter',
            hoverinfo='x'+'y'
        )
    ]
    layout = go.Layout(
	title = f'{state_value}: {site_value}',
	paper_bgcolor = 'rgba(0,0,0,0)',
	plot_bgcolor = 'rgba(0,0,0,0)',
        scene=dict(
            xaxis=dict(
                backgroundcolor="rgb(200, 200, 230)",
                gridcolor="rgba(0,0,0)",
                showbackground=True,
                tickwidth=2,
                tickfont=dict(
                    color="white",
                ),
            ),
            yaxis=dict(
                backgroundcolor="rgb(200, 200, 230)",
                gridcolor="rgba(0,0,0)",
                showbackground=True,
                tickwidth=2,
                tickfont=dict(
                    color="white",
                ),
                title='SWE'
            ),                            
        ),            
    )

    figure = {
        'data': data,
        'layout': layout
    }

    return figure


if __name__ == "__main__":
    dash_app.run_server(debug=True, port=8000)
