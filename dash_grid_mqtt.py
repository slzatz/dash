'''
    ## <span style="color: #ff0000">January 30, 2011</span>
    ## html.Span("hello", style={'color':'red'})
    ## phrases are a list of tuples like [('{}', 'forecast: '), ('{red}', '113.8M')]
# to do: if payload hasn't changed no need to write to screen
'''

import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import datetime
import json
import re
import plotly
from config import aws_mqtt_uri
print("aws_mqtt_uri =", aws_mqtt_uri)

#######################################################################
from flask_mqtt import Mqtt

app = dash.Dash(__name__)

app.config['MQTT_BROKER_URL'] = aws_mqtt_uri 
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_KEEPALIVE'] = 60  # set the time interval for sending a ping to the broker to 60 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

data={}

# line => "forecast: {red} 114.2M {}"
#phrases = [('{}', 'forecast: '), ('{red}', '114.2M')]
def get_phrases(line, start='{}'):
    if line.find('{') == -1:
        print("phrases =", [(start, line)])
        return [(start, line)]

    if line[0]!='{':
        line = start+line

    line = line+'{}'

    z = re.finditer(r'{(.*?)}', line)
    s = [[m.group(), m.span()] for m in z]
    #print(s)
    if not s:
        return [('{}', line)]
    phrases = []
    for j in range(len(s)-1):
        phrases.append((s[j][0],line[s[j][1][1]:s[j+1][1][0]]))
    print("phrases =", phrases)
    return phrases

def generate_html(n):
    data_n = data.get(n)
    if not data_n:
        return [html.H3("No data")]

    text = data_n.get('text', "Somehow no text key")
    header = data_n.get('header', "Somehow no header key")
    new_text = [html.H3(header)]
    for line in text:
        phrases = get_phrases(line)
        new_line=[]
        for phrase in phrases:
            color = phrase[0][1:-1] 
            new_line.append(html.Span(phrase[1], style={'color':color}) if color else phrase[1])
        new_text.extend(new_line)
        new_text.append(html.Br())
    print("5: ", new_text)
    #style = {'padding': '5px', 'fontSize': '16px'}
    style = {'fontSize': '16px', 'backgroundColor':'yellow'}
    return [html.Span(new_text, style=style)]

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp_tft')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    payload = json.loads(message.payload.decode())
    data[payload['pos']] = payload   

app.layout = html.Div([

#######################################################
    dcc.Interval(
        id='interval-component',
        interval=1*1000, # in milliseconds
        n_intervals=0),
#######################################################

    html.Div(
    [
        html.Div([
            html.Div(id='live-update-text-0'),
        ], className="six columns"),

        html.Div([
            html.Div(id='live-update-text-5'),
        ], className="six columns")
    ],
    className="row"),

    html.Div(
    [
        html.Div([
            html.Div(id='live-update-text-1'),
        ], className="six columns"),

        html.Div([
            html.Div(id='live-update-text-6'),
        ], className="six columns")
    ],
    className="row"),

    html.Div([
        html.Div([
            html.H3('Row 3 Column 1'),
            dcc.Graph(id='g31', figure={'data': [{'y': [1, 2, 3]}]})
        ], className="six columns"),

        html.Div([
            html.H3('Row 3 Column 2'),
            dcc.Graph(id='g32', figure={'data': [{'y': [1, 2, 3]}]})
        ], className="six columns")
    ],
    className="row")
])

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
#######################################################################

@app.callback(Output('live-update-text-0', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_0(n):
    return generate_html(0)

@app.callback(Output('live-update-text-5', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_5(n):
    return generate_html(5)

@app.callback(Output('live-update-text-1', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_1(n):
    return generate_html(1)

@app.callback(Output('live-update-text-6', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_6(n):
    return generate_html(6)

if __name__ == '__main__':
    app.run_server(debug=True)
