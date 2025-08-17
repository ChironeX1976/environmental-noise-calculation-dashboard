import dash
from dash import html, dcc, Output, Input
import json

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Store(id='allowed-files-store', data=''),
    html.Button(id='cl_btn_loaddata_into_dccstore', children='Load Data', n_clicks=0),
    html.Button(id='select-folder', children="Kies map", n_clicks=0),
    html.Select(id="file-list", disabled=True),
    html.Audio(id="audio-player", controls=True),
    html.P(id="error-message", style={"color": "red"}),
    html.Div(id="js-trigger", **{"data-files": ""})  # custom data attribuut
])

@app.callback(
    Output('allowed-files-store', 'data'),
    Input('cl_btn_loaddata_into_dccstore', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    mijn_bestanden = [
        {'label': '2025-05-26 09:30:21', 'value': '093021_093029.mp3'},
        {'label': '2025-05-26 09:35:08', 'value': '093508_093604.mp3'},
        {'label': '2025-05-26 09:39:46', 'value': '093946_100946.mp3'}
    ]
    return mijn_bestanden

@app.callback(
    Output("js-trigger", "data-files"),
    Input("allowed-files-store", "data")
)
def inject_data(data):
    return json.dumps(data)

if __name__ == "__main__":
    app.run(debug=True)
