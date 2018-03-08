# to do: if payload hasn't changed no need to write to screen
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import datetime
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

@mqtt.on_connect()
def handle_connect(client, userdata, flags, rc):
    mqtt.subscribe('esp_tft')

@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    global data
    data = dict(
        topic=message.topic,
        payload=message.payload.decode()
    )
#######################################################################

app.layout = html.Div(
    html.Div([
        html.H4('Info Dashboard'),
        html.Div(id='live-update-text'),
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0 # not clear what n_intervals is used for
        )
    ])
)

@app.callback(Output('live-update-text', 'children'),
              [Input('interval-component', 'n_intervals')])
def update_info(n):
    text = data.get('payload', "No Data")
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span(text, style=style),
    ]


# Multiple components can update everytime interval gets fired.
#@app.callback(Output('live-update-graph', 'figure'),
              #[Input('interval-component', 'n_intervals')])
#def update_graph_live(n):
#    satellite = Orbital('TERRA')
#    data = {
#        'time': [],
#        'Latitude': [],
#        'Longitude': [],
#        'Altitude': []
#    }
#
#    # Collect some data
#    for i in range(180):
#        time = datetime.datetime.now() - datetime.timedelta(seconds=i*20)
#        lon, lat, alt = satellite.get_lonlatalt(
#            time
#        )
#        data['Longitude'].append(lon)
#        data['Latitude'].append(lat)
#        data['Altitude'].append(alt)
#        data['time'].append(time)
#
#    # Create the graph with subplots
#    fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
#    fig['layout']['margin'] = {
#        'l': 30, 'r': 10, 'b': 30, 't': 10
#    }
#    fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}
#    
#
#    fig.append_trace({
#        'x': data['time'],
#        'y': data['Altitude'],
#        'name': 'Altitude',
#        'mode': 'lines+markers',
#        'type': 'scatter'
#    }, 1, 1)
#    fig.append_trace({
#        'x': data['Longitude'],
#        'y': data['Latitude'],
#        'text': data['time'],
#        'name': 'Longitude vs Latitude',
#        'mode': 'lines+markers',
#        'type': 'scatter'
#    }, 2, 1)
#
#    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
