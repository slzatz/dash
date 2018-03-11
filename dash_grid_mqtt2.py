'''
phrases are a list of tuples like [('{}', 'forecast: '), ('{red}', '113.8M')]

*0=temp sensors (CT, NYC): 4 wide
*1=news feeds (WSJ, NYT, ArsTechnica, Reddit All, Twitter): 8 wide
*2=stock quote: 4 wide
*3=ToDos: 8 wide
*4=google: 8 wide plus ?sonos status (PLAYING, TRANSITIONING, STOPPED) broadcast by sonos_track_info on topic esp_tft and also on sonos/{loc}/status for esp_tft_mqtt_photos(and lyrics) 
*5=sales forecast: 4 wide
*6=outlook_schedule: 8 wide
7=artist image
8=lyrics
9=track_info broadcast by sonos_track_info.py
10=sonos status (PLAYING, TRANSITIONING, STOPPED
*11=sales top opportunities: 8 wide and need to change font
12=Reminders (alarms) 
13=Ticklers
14=Facts
*15=weather/tides: 4 wide
*16=Industry: 8 wide
17=temp sensor to do: if payload hasn't changed no need to write to screen
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

def generate_html(n, backgroundcolor='yellow'):
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

    span_style = {'fontSize': '16px'}

    div_style = {'fontSize': '16px',
                 'backgroundColor':backgroundcolor,
                 'borderWidth':'medium',
                 'borderColor':'black',
                 'borderStyle':'solid'}

    return [html.Div([html.Span(new_text, style=span_style)], style=div_style)]

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp_tft')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    payload = json.loads(message.payload.decode())
    data[payload['pos']] = payload   
    
def create_layout():
    #0 temp sensor:four
    #1 news feed: eight
    #2 stock quote: four
    #3 ToDos:six
    #4 google: eight
    #5 sales forecast:four
    #6 outlook: eight
    #11 top sales opportunities: eight
    #15 weather/tides: four
    #16 Industry: six
    lst = [[(6,0), ("eight", "four")],
           [(2,1), ("four", "eight")],
           [(4,5), ("eight", "four")],
           [(15,11), ("four", "eight")],
           [(3,16), ("six", "six")],
          ]

    layout = []
    for item in lst:
        id0 = 'live-update-text-'+str(item[0][0])
        id1 = 'live-update-text-'+str(item[0][1])
        class_name0 = "{} columns".format(item[1][0])
        class_name1 = "{} columns".format(item[1][1])

        layout.append(
                     html.Div(
                             [
                                html.Div([
                                    html.Div(id=id0),
                                ], className=class_name0),

                                html.Div([
                                    html.Div(id=id1),
                                ], className=class_name1)
                                                     ],
                            className="row")
                     )
    return layout

layout = [

#######################################################
    dcc.Interval(
        id='interval-component',
        interval=5000, # in milliseconds
        n_intervals=0)
#######################################################
         ]

layout.extend(create_layout())
app.layout = html.Div(layout)

app.css.append_css({
    'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'
})
#######################################################################

@app.callback(Output('live-update-text-0', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_0(n):
    return generate_html(0)

@app.callback(Output('live-update-text-1', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_1(n):
    return generate_html(1, 'lavender')

@app.callback(Output('live-update-text-2', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_2(n):
    return generate_html(2, 'blue')

@app.callback(Output('live-update-text-3', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_3(n):
    return generate_html(3, 'teal')

@app.callback(Output('live-update-text-4', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_4(n):
    return generate_html(4, 'pink')

@app.callback(Output('live-update-text-5', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_5(n):
    return generate_html(5, 'coral')

@app.callback(Output('live-update-text-6', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_6(n):
    return generate_html(6, 'lightblue')

@app.callback(Output('live-update-text-11', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_11(n):
    return generate_html(11, 'silver')

@app.callback(Output('live-update-text-15', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_15(n):
    return generate_html(15)

@app.callback(Output('live-update-text-16', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info_16(n):
    return generate_html(16, 'red')

if __name__ == '__main__':
    app.run_server(debug=True)
