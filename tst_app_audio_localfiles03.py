import dash
from dash import html, dcc, Output, Input
import json

app = dash.Dash(__name__)

app.layout = html.Div([
    dcc.Store(id='cl_allowed_audiofiles_store', data=''),
    html.Button(id='cl_btn_loaddata_into_dccstore', children='Load Data', n_clicks=0),
    html.Button(id='cl_btn_select_audiofolder', children="Kies map", n_clicks=0),
    html.Select(id="cl_drp_audiofilelist", disabled=True),
    html.Audio(id="cl_audioplayer", controls=True),
    html.P(id="cl_audio_errormessage", style={"color": "red"}),
    html.Div(id="js_trigger_audiofiles_are_in_store", **{"data-files": ""}),
    html.Div(id="cl_begintime", children="here i want the timestamp of the selected value"),
    # dcc.Store(id="cl_begintime", data=''),
    html.Div(id="cl_ann", children='no audiofile loaded')
])


@app.callback(
    Output('cl_allowed_audiofiles_store', 'data'),
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
    Output("js_trigger_audiofiles_are_in_store", "data-files"),
    Input("cl_allowed_audiofiles_store", "data")
)
def inject_audiodata(lst_audiofiles):
    print ("injected", lst_audiofiles)
    return json.dumps(lst_audiofiles)

if __name__ == "__main__":
    app.run(debug=True)