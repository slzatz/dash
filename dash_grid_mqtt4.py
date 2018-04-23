#!bin/python
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
import dash_auth
import datetime
import json
import re
import plotly
from config import aws_mqtt_uri, user_list, host
from flask_mqtt import Mqtt
from random import choice

TEMP1=0
NEWS=1 #news feeds(WSJ, NYT, ArsTechnica, Reddit All, Twitter)
STOCK_QUOTE=2 #stock quote from whatever symbol chosen
TODOS=3 #todos taken from listmanager starred items from work
GOOGLE=4 #gmail alternating with google calendar
SALES_FORECAST=5 #esp_tft_mqtt_sf2.py
OUTLOOK=6 
ARTIST_IMAGE=7
LYRICS=8
TRACK_INFO=9
SONOS_STATUS=10
TOP_SALES=11
REMINDERS=12
TICKLERS=13
FACTS=14
WEATHER=15 #also does tides
INDUSTRY=16
TEMP2=17 #another temp sensor slot

# LAYOUT consists of rows and within rows columns that are tuples of (info_source, # of columns)
LAYOUT = [
          [(OUTLOOK, 'four'), (GOOGLE, 'four'), (NEWS, 'four')],
          [(SALES_FORECAST, 'three'), (WEATHER, 'three'), (STOCK_QUOTE, 'three'), (TEMP1, 'three')],
          [(TODOS, 'four'), (TOP_SALES, 'five'), (INDUSTRY, 'three')]
         ]

ROW_HEIGHT = ['500px', '250px', '800px']

#COLORS = [(backgroundcolor, textcolor)...]
COLORS = [('cyan','black'),('lavender','black'),('lightcoral','white'),('white','black'),('dimgray','white'),('teal','black'),('lightsalmon', 'black'),('lightskyblue', 'black'), ('plum','black')]

####### code below is for using a local css file placed in the assets folder #################
app = dash.Dash(__name__, static_folder='assets')
auth = dash_auth.BasicAuth(app, user_list)
app.scripts.config.serve_locally=True
app.css.config.serve_locally=True

app.config['MQTT_BROKER_URL'] = aws_mqtt_uri 
app.config['MQTT_BROKER_PORT'] = 1883  # default port for non-tls connection
app.config['MQTT_KEEPALIVE'] = 60  # set the time interval for sending a ping to the broker to 60 seconds
app.config['MQTT_TLS_ENABLED'] = False  # set TLS to disabled for testing purposes

mqtt = Mqtt(app)

data={} #data coming back from mqtt

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

def generate_html(n, backgroundcolor='yellow', textcolor='black', row_height='500px'): 
    data_n = data.get(n)
    if not data_n:
        return [html.H3("No data")]

    text = data_n.get('text', "Somehow no text key")
    header = data_n.get('header', "Somehow no header key")
    new_text = []
    for line in text:
        phrases = get_phrases(line)
        new_line=[]
        for phrase in phrases:
            color = phrase[0][1:-1] 
            new_line.append(html.Span(phrase[1], style={'color':color}) if color else phrase[1])
        new_text.extend(new_line)
        new_text.append(html.Br())

    text_style = {'fontSize': '24px', 'color':textcolor} 


    div_style = {
                 'backgroundColor':backgroundcolor,
                 'borderWidth':'medium',
                 'borderColor':'black',
                 'borderStyle':'solid',
                 'display':'block',
                 'padding':'10px',
                 'height':row_height
                 }

    # complete kluge to present table (infobox=11) with monospaced font
    if n!=11:
        return [html.Div([html.H3(header), html.Span(new_text, style=text_style)], style=div_style)]

    return [html.Div([html.H3(header), html.Pre(new_text, style=text_style)], style=div_style)]

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp_tft')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    payload = json.loads(message.payload.decode())
    data[payload['pos']] = payload   
    
def create_layout():

    layout = []
    s = 'live-update-text-'
    for row in LAYOUT:
        row_elements = []
        for col in row:
            row_elements.append(html.Div([html.Div(id='{}{}'.format(s, col[0]))],
                                         className='{} columns'.format(col[1]), style={'margin':1})) 

        layout.append(html.Div(row_elements, className='row'))

    return layout

layout = [
        # uncomment next line (and a few lines at beginning of script if using local css file
        html.Link(href='/assets/bWLwgP.css', rel='stylesheet'), 
        dcc.Interval(
        id='interval-component',
        interval=5000, # in milliseconds
        n_intervals=0)
         ]

layout.extend(create_layout())
app.layout = html.Div(layout)

#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

# code below enables generating callbacks programatically v. having to write each one out
def create_callback(n, bcolor, tcolor, row_height):
    def callback(input_value): # input_value is n_intervals
        return generate_html(n, bcolor, tcolor, row_height)
    return callback

for n,row in enumerate(LAYOUT):
    for col in row:
        colors = choice(COLORS)
        f = create_callback(col[0], colors[0], colors[1], ROW_HEIGHT[n])
        app.callback(Output(f'live-update-text-{col[0]}', 'children'), [Input('interval-component', 'n_intervals')])(f)

if __name__ == '__main__':
    app.run_server(debug=True, host=host)
