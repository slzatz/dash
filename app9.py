'''If you change this to a function, then a new datetime will get computed everytime you refresh the page. Give it a try:'''

import dash
import dash_html_components as html
import datetime

app = dash.Dash()

def serve_layout():
    return html.H1('The time is: ' + str(datetime.datetime.now()))

app.layout = serve_layout

if __name__ == '__main__':
    app.run_server()
