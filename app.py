import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objects as plt
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
# from alpha_vantage.timeseries import TimeSeries
import csv
import base64
import numpy as np
import warnings
import os
from datetime import datetime

warnings.filterwarnings("ignore")

reader = pd.read_csv('OutputFile.csv')

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([

    html.H1('F/O STOCK DATA', style={'color': 'blue', 'fontSize': 50, 'textAlign': 'center'}),

    html.Label('SELECT SYMBOL', style={'color': 'blue', 'fontSize': 30, }),

    dcc.Dropdown(id='dropdown',
                 options=[{'label': x, 'value': x} for x in reader['SYMBOL'].unique()],
                 value='NIFTY'
                 ),

   html.A(id='BhavcopyLink',children="Get Today's Bhavcopy", target="_self"),

    dcc.Graph(id='fig1'),
    dcc.Graph(id='fig2'),
    dcc.Graph(id='fig3'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=False
    ),
    html.Div(id='output-data-upload',
    	style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        })
])


def parse_contents(content, filename, date):
    if filename != None:
        df = pd.read_csv(filename)
        print("if statement",sep='\n')
        cond1=df['OPTION_TYP']=='XX'
        future_len=cond1
        future_index=df[cond1]
        #future_index = df.loc[cond1]
        data = []
        symbols_repeat = set()
        counter = -1
        for symbol in future_index.SYMBOL:
            counter += 1
            if ((symbol in symbols_repeat)):
                data[-1]['COI'] += future_index['OPEN_INT'][counter]
            else:
                symbols_repeat.add(symbol)
                index = list(future_index.SYMBOL).index(symbol)
                data.append({'TIMESTAMP': future_index['TIMESTAMP'][index],
                             'INSTRUMENT': future_index['INSTRUMENT'][index],
                             'SYMBOL': future_index['SYMBOL'][index],
                             'OPEN': future_index['OPEN'][index],
                             'HIGH': future_index['HIGH'][index],
                             'LOW': future_index['LOW'][index],
                             'CLOSE': future_index['CLOSE'][index],
                             'COI': future_index['OPEN_INT'][index],
                             'PCR': 0.00})
        output_file = pd.DataFrame(data)
        for symbol in output_file['SYMBOL']:
            index = list(output_file['SYMBOL']).index(symbol)
            if (output_file['INSTRUMENT'][index] == 'FUTIDX'):
                target = 'OPTIDX'
            else:
                target = 'OPTSTK'
            subsub_reader=df[df.SYMBOL==symbol]
            sub_reader=subsub_reader[subsub_reader.INSTRUMENT==target]
            if (sub_reader.empty):
                continue
            else:
                CE_reader = sub_reader[sub_reader['OPTION_TYP'] == 'CE']
                PE_reader = sub_reader[sub_reader['OPTION_TYP'] == 'PE']
                CE_sum = 1 + sum(list(CE_reader['OPEN_INT']))
                PE_sum = sum(list(PE_reader['OPEN_INT']))
                output_file['PCR'][index] = PE_sum / CE_sum

        filename1 = 'OutputFile.csv'
        file_exists = (os.path.isfile(filename1))

        with open('OutputFile.csv', 'a', newline='') as f:
            output_file.to_csv(f, header=not file_exists)
        return html.Div([
            ('File Processed-'+filename),
        ])
    else:
        print("else statement")
        return html.Div([
            ''
        ])


@app.callback([Output('fig1', 'figure'), Output('fig2', 'figure'), Output('fig3', 'figure'),
               Output('output-data-upload', 'children'),Output('BhavcopyLink','href')],
              [Input('dropdown', 'value'), Input('upload-data', 'contents')],
              [State('upload-data', 'filename'), State('upload-data', 'last_modified')])
def compute_value(value, content, filename, date):
    # print(value,filename,filename!=None,"-----")

    # ts = TimeSeries(key='DDTTBH29BT794YL9', output_format='csv')
    reader = pd.read_csv('OutputFile.csv')

    req_output = reader[reader.SYMBOL == value]

    for date in req_output['TIMESTAMP']:
        date = date[0:3]

    dates=[x[0:6] for x in req_output['TIMESTAMP']]

    fig1 = plt.Figure(data=[plt.Candlestick(x=dates,
                                            open=req_output['OPEN'],
                                            high=req_output['HIGH'],
                                            low=req_output['LOW'],
                                            close=req_output['CLOSE'])])
    fig1.update_layout(xaxis_rangeslider_visible=False)

    fig2 = px.bar(req_output, x='TIMESTAMP', y='COI', height=250)
    fig2.update_yaxes(automargin=False)

    fig3 = px.bar(req_output, x='TIMESTAMP', y='PCR', height=250)

    t = datetime.strptime('2020-05-08','%Y-%m-%d')
    d, m, y = '%02d' % t.day, '%02d' % t.month, '%02d' % t.year
    dmonth={'01':'JAN','02':'FEB','03':'MAR','04':'APR','05':'MAY','06':'JUN','07':'JUL','08':'AUG','09':'SEP','10':'OCT','11':'NOV','12':'DEC'}
    link="url='https://www1.nseindia.com/content/historical/DERIVATIVES/'+y+'/'+dmonth[m]+'/fo'+d+dmonth[m]+y+'bhav.csv.zip'"

    return fig1, fig2, fig3, parse_contents(content, filename, date),link


if __name__ == '__main__':
    app.run_server(debug=True)
