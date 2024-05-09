import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.graph_objects as go
import requests
import base64
from datetime import datetime, timedelta
import polars as pl
from io import StringIO
import warnings
warnings.filterwarnings('ignore')

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server
# Define layout
app.layout = html.Div(style={'margin': '50px 150px'}, children=[
    html.Link(
        rel='stylesheet',
        href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css'
    ),
    
    # Logo row
    html.Div([
        html.Div([
            html.Img(src='/assets/logo.png', style={'height': '55px', 'width': '275px'})
        ], style={'width': '30%', 'display': 'inline-block'}),
    ]),
    
    # Dropdown and Stats row
    html.Div([
        # Dropdown column
        html.Div([
            dcc.Dropdown(
                id='timeframe-dropdown',
                options=[
                    {'label': 'Last 7 Days', 'value': 7},
                    {'label': 'Last 30 Days', 'value': 30},
                    {'label': 'Last 90 Days', 'value': 90}
                ],
                value=7,
                style={'fontFamily': 'Roboto', "margin-left": "2px", "margin-right":"2px"}
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        # Stats column
        html.Div([
            html.Div(id='stat1', className='stats', style={'display': 'inline-block', 'margin-right': '50px'}),
            html.Div(id='stat2', className='stats', style={'display': 'inline-block', 'margin-right': '50px'}),
            html.Div(id='stat3', className='stats', style={'display': 'inline-block'})
        ], className='container1')
    ], style={"margin": "20px 0px"}),
    
    # Inputs and Charts row
    html.Div([
        # Inputs column
        html.Div([
            html.Div([
                html.H3("Inputs", style={"margin-left": "40px", "margin-top": "30px"}),  # Title
                html.Hr(style={'margin-left': '40px', "margin-right": "38px", "margin-top": "10px", 'border-top': '1px solid black'}),  # Line below the title
                dcc.DatePickerSingle(id='fromdate', placeholder='From Date', style={'margin-left': '40px', "margin-top": "20px", 'display': 'inline-block'}),
                html.I(className="fas fa-sliders-h", style={'margin-left': '10px', 'display': 'inline-block'}),  # Time icon
                dcc.DatePickerSingle(id='todate', placeholder='To Date', style={'margin-left': '10px', "margin-top": "20px", 'display': 'inline-block'}),
                dcc.Input(id='market', type='text', placeholder='Market', style={'text-align': 'center' ,"justifyContent":'center','background-color': 'transparent', 'border-radius':"5px",'border': 'none', 'box-shadow': '0px 2px 3px rgba(0, 0, 0, 0.2)', "font-size": "15px", 'font-family': 'Roboto', "margin-top": "20px", 'margin-left': '40px', 'display': 'inline-block', 'width': '74px', 'height': '35px'}),
                dcc.Input(id='model', type='text', placeholder='Model', style={'text-align': 'center' ,"justifyContent":'center','background-color': 'transparent', 'border-radius':"5px",'border': 'none', 'box-shadow': '0px 2px 3px rgba(0, 0, 0, 0.2)', "font-size": "15px", 'font-family': 'Roboto', 'margin-left': '18px', 'display': 'inline-block', 'width': '74px', 'height': '35px'}),
                dcc.Input(id='node', type='text', placeholder='Node', style={'text-align': 'center' ,"justifyContent":'center','background-color': 'transparent', 'border-radius':"5px",'border': 'none', 'box-shadow': '0px 2px 3px rgba(0, 0, 0, 0.2)', "font-size": "15px", 'font-family': 'Roboto', 'margin-left': '18px', 'display': 'inline-block', 'width': '74px', 'height': '35px'}), 
                html.Div([
                    html.Div([
                    html.Button(
                        id='upload-data',
                        children=html.A(children=[
                            html.Span(className='icon', children=[html.I(className='fas fa-check', style={'color': 'white'})]),
                            'Submit'
                        ], className='btn'), style={"border": "0px", "width":"250px"}
                    )
                ], style={'display': 'inline-block'}),
                ], className='container', style={"margin-left": "40px","margin-right": "50px", "margin-bottom": "20px"})
            ], style={'background': 'white', 'margin-left': '1%', 'border-radius': '7px', 'border': '1px solid rgba(233, 233, 233)'}),
            
            html.Div([html.Div(id='status_message', className='stats', style={'display': 'inline-block', 'margin-right': '00px',"color": "#8B8B8B", "font-size": "15px"})],
                      style={'margin-top': '10px', 'text-align': 'center'})
        ], style={'width': '30%', 'display': 'inline-block'}),
        
        # Charts column
        html.Div([
            html.Div([
                dcc.Graph(id='chart1')
            ], style={'margin-top': '2px', 'margin-left': '5px', 'margin-right': '20px', 'width': '95%'}),
            
            html.Div([
                dcc.Graph(id='chart2')
            ], style={'margin-top': '20px', 'margin-left': '5px', 'margin-right': '20px', 'width': '95%'})
        ], style={"background": "white", 'margin-left': '1%', 'border-radius': '7px', 'border': '1px solid rgba(233, 233, 233)', 'width': '69%', 'display': 'inline-block', 'verticalAlign': 'top'})
    ], style={"margin": "20px 0px"})
])





def excel_to_date(serial_date):
    start_date = datetime(1899, 12, 30)
    delta_days = timedelta(days=serial_date)
    converted_date = start_date + delta_days
    return converted_date

# Load CSV data and update charts
@app.callback(
    [Output('chart1', 'figure'),
     Output('chart2', 'figure'),
     Output('stat1', 'children'),
     Output('stat2', 'children'),
     Output('stat3', 'children'),Output('status_message', 'children')],
    [Input('timeframe-dropdown', 'value'),
     Input('upload-data', 'n_clicks')],
    [dash.dependencies.State('upload-data', 'filename'),
     dash.dependencies.State('fromdate', 'date'),
     dash.dependencies.State('todate', 'date'),
     dash.dependencies.State('market', 'value'),
     dash.dependencies.State('model', 'value'),
     dash.dependencies.State('node', 'value')]
)
def update_charts(selected_timeframe, n_clicks, filename, fromdate, todate, market, model, node):

    if n_clicks is None:
        # Return default values or empty figures
        return {}, {}, [], [], [], []

    url = "https://quantum-zero-bayfm.ondigitalocean.app/report"
    data = {
        "from_date": fromdate,
        "to_date": todate,
        "market": market,
        "model": model,
        "node": node
    }

    for i,v in {"Start Date":fromdate, "End Date":todate, "Market":market, "Model":model, "Node":node}.items():
        if v is None or v =="":
            return {}, {}, [], [], [], "Missing parameter - {}".format(i)

    response = requests.post(url, data=data)

    if response.status_code != 200:
        error_message = response.text

        return {}, {}, [], [], [], error_message
    else:
        error_message = "Status: Success!"
    
    dfx = pl.read_json(StringIO(response.text))

    df = dfx.to_pandas()

    filtered_df = df.tail(selected_timeframe)

    filtered_df['cumulative_profit'] = filtered_df['profit_total'].cumsum()

    filtered_df["Smooth_profit"] = filtered_df['cumulative_profit'].rolling(window=3, min_periods=1).mean()

    max_value = max(filtered_df["cumulative_profit"])
    min_value = min(filtered_df["cumulative_profit"])
    if min_value >0:
        min_value = min_value *0.8
    else: 
        min_value = min_value *1.2
    if max_value >0:
        max_value = max_value *1.2
    else:
        max_value = max_value *0.8

    tick_interval = (max_value - min_value)/ 5
    rounded_tick_interval = round(tick_interval / 10) * 10

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['cumulative_profit'], mode='lines', name='Cumulative PnL', line=dict(color="rgba(44, 44, 61,1)", width=2)))
    fig1.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['Smooth_profit'], mode='lines', name='Trend', line=dict(color="rgba(250, 152, 0 ,1)", width=2)))
    fig1.update_layout(
        title='PnL Explain',
        title_x=0.5,
        xaxis_title='Date',
        yaxis_title='Cumulative PnL',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(0, 0, 0,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(0, 0, 0,0.1)'),
        shapes=[dict(type="line", x0=filtered_df['date'].iloc[0], y0=0, x1=filtered_df['date'].iloc[-1], y1=0, line=dict(color="black", width=1))],
        hovermode='x',
        font=dict(family='Roboto')
    )
    fig1.update_yaxes(showline=True, linewidth=1, linecolor='rgba(0, 0, 0,0.7)', ticksuffix = "  ", range=[min_value, max_value], dtick=int(rounded_tick_interval))
    #fig1.update_xaxes(nticks=7)

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['win_count'], mode='lines', name='Win Count', line=dict(color="rgba(15, 183, 25 ,1)", width=2)))
    fig2.add_trace(go.Scatter(x=filtered_df['date'], y=filtered_df['loss_count'], mode='lines', name='Loss Count', line=dict(color="rgba(183, 15, 15,1)", width=2)))
    fig2.update_layout(
        title='# Won Trades',
        title_x=0.5,
        xaxis_title='Date',
        yaxis_title='Win Count',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='lightgrey'),
        yaxis=dict(showgrid=True, gridcolor='lightgrey'),
        shapes=[dict(type="line", x0=filtered_df['date'].iloc[0], y0=0, x1=filtered_df['date'].iloc[-1], y1=0, line=dict(color="black", width=1))],
        hovermode='x',
        font=dict(family='Roboto'),
    )

    fig2.update_yaxes(showline=True, linewidth=1, linecolor='rgba(0, 0, 0,0.7)', ticksuffix = "  ")

    stat1 = filtered_df['cumulative_profit'].iloc[-1]
    stat2 = filtered_df['win_count'].sum()+filtered_df['loss_count'].sum()
    stat3 = filtered_df['win_count'].sum()/stat2#filtered_df['column2'].mean()  # Change 'column2' to the appropriate column name

    stat1_html = html.Span([html.B("PnL: "), f"{stat1:.2f}"])
    stat2_html = html.Span([html.B("Trades: "), f"{stat2:.0f}"])
    stat3_html = html.Span([html.B("Percentage Wins: "), f"{stat3*100:.0f}%"])

    return fig1, fig2, stat1_html, stat2_html, stat3_html, error_message

# Run the app
if __name__ == '__main__':
    app.run_server(debug=False)
