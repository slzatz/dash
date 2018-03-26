'''
phrases are a list of tuples like [('{}', 'forecast: '), ('{red}', '113.8M')]

7=artist image
8=lyrics
9=track_info broadcast by sonos_track_info.py
10=sonos status (PLAYING, TRANSITIONING, STOPPED
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
from flask_mqtt import Mqtt
from random import choice
from io import BytesIO
import wand.image
import requests
import base64

ARTIST_IMAGE=7
LYRICS=8
TRACK_INFO=9
SONOS_STATUS=10

# LAYOUT consists of rows and within rows columns that are tuples of (info_source, # of columns)
LAYOUT = [
          [(ARTIST_IMAGE, 'six'), (LYRICS, 'six')],
          [(TRACK_INFO, 'three'), (SONOS_STATUS, 'three')]
         ]

ROW_HEIGHT = ['800px', '250px']

#COLORS = [(backgroundcolor, textcolor)...]
COLORS = [('cyan','black'),('lavender','black'),('lightcoral','white'),('white','black'),('dimgray','white'),('teal','black'),('lightsalmon', 'black'),('lightskyblue', 'black'), ('plum','black')]

app = dash.Dash(__name__)

####### code below is for using a local css file placed in the assets folder #################
app = dash.Dash(__name__, static_folder='assets')
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

    text_style = {'fontSize': '18px', 'color':textcolor} 


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

def generate_image(n):
    #data_n = data.get(n)
    x = data.get(n)['uri']
    print(x)
    try:
        response = requests.get(x, timeout=5.0)
    except Exception as e:
        print("response = requests.get(url) generated exception: ", e)
        # in some future better world may indicate that the image was bad

        return
    else:     
        try:
            img = wand.image.Image(file=BytesIO(response.content))
        except Exception as e:
            print("img = wand.image.Image(file=BytesIO(response.content)) generated exception from url:", x, "Exception:", e)
            # in some future better world may indicate that the image was bad

            return

    try:
        ww = img.width
        hh = img.height
        sq = ww if ww <= hh else hh
        t = ((ww-sq)//2,(hh-sq)//2,(ww+sq)//2,(hh+sq)//2) 
        img.crop(*t)
        # resize should take the image and enlarge it without cropping so will fill vertical but leave space for lyrics
        #img.resize(screen_height,screen_height)
        img.resize(400,400)
        conv_img = img.convert('png')
        img.close()
    except Exception as e:
        print("img.transfrom or img.convert error:", e)
        # in some future better world may indicate that the image was bad

        return

    f = BytesIO()
    try:
        conv_img.save(f)
        conv_img.close()
    except wand.exceptions.OptionError as e:
        print("Problem saving image:",e)
        # in some future better world may indicate that the image was bad

        return

    f.seek(0)
    #img = pygame.image.load(f, 'bmp').convert()
    #f.close()
    #img_rect = img.get_rect()

    #print("img_rect =", img_rect)

    #foo = pygame.Surface((400,400)) # (800,800) someday will make this something that you pass with the image
    #foo.fill((0,0,0))
    #foo.set_alpha(175) #125
    
    #foo.blit(img, (0,0))      
    #encoded_image = base64.b64encode(open(f, 'rb').read())
    encoded_image = base64.b64encode(f.read())
    f.close()
    return html.Div([
                    html.Img(src='data:image/png;base64,{}'.format(encoded_image.decode()))
                    ])
    return foo

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp_tft')
    mqtt.subscribe('images')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    payload = json.loads(message.payload.decode())
    #data[payload['pos']] = payload   
    if payload['pos'] not in (7,8,9,10):
        return
    if message.topic == 'imagesdddddddddddddd':
        data[payload['pos']] = "url: "+payload['uri']
    else:
        data[payload['pos']] = payload   
        
    
    print(payload['pos'],data[payload['pos']])

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

def create_callback_image(n):
    def callback(input_value): # input_value is n_intervals
        return generate_image(n)
    return callback

for n,row in enumerate(LAYOUT):
    for col in row:
        if col[0] == ARTIST_IMAGE:
            f = create_callback_image(col[0])
            app.callback(Output(f'live-update-text-{col[0]}', 'children'), [Input('interval-component', 'n_intervals')])(f)
        else:
            colors = choice(COLORS)
            f = create_callback(col[0], colors[0], colors[1], ROW_HEIGHT[n])
            app.callback(Output(f'live-update-text-{col[0]}', 'children'), [Input('interval-component', 'n_intervals')])(f)

if __name__ == '__main__':
    app.run_server(debug=True)
