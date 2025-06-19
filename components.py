import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from definitions import get_std_audio_path
""" 
The components of the dash web-page are created here, web page looks like this:
--------------------------------------
|lefties| tabstogether                |
|       |    time, stats, spect       |
|       |                             |
|       |                             |
|       |                             |
--------------------------------------|
| helpfields                          |
--------------------------------------|
"""

def c_lefties():
    """make html-components left on the webpage"""
    c = html.Div([html.Img(src="assets/logo.png", width=120),
                  html.Div('Load data:'),
                  dcc.Upload(id='cl_upload01',
                             children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
                             style={'borderStyle': 'solid', 'borderColor': 'black', 'backgroundColor': 'white'}),
                  html.Div(id='cl_filestatus', children='...'),
                  dbc.Button(id="cl_btn_save", children="save", color="success", size="m")],
                   className="bg-primary h-100 border border-5")
    return c
def c_tab_time():
    """make html - components related to the time series of sound pressure levels"""
    c = html.Div([
    # dbc.Row([table], className="border border-5 bg-secondary"),
    dcc.Interval(id="cl_interval", interval=1000),  # every 1000 milliseconds a refresh
    dbc.Row(
        [
            html.Div(dcc.Input(id="cl_audiofolder", type="text",
                      value=str(get_std_audio_path()),
                      className="custom-audiopath")),
            html.Div(dcc.Dropdown(id='cl_drop_audiotimeandfile', placeholder="Select audiofile",
                              #options=lstsound,
                              #value=lstsound[0]['value'],
                              clearable=False,
                    style={'width':'100%','height': '33px', 'display': 'inline-block'}),
                 style={"width": "15%", "height":"33px", 'display': 'inline-block'}),

        html.Audio(id='cl_audioplayer', src='',
            controls=True, autoPlay=False, style={'display': 'inline-block', "width": "85%", "height":"33px"})
        ],
        className="border border-5 bg-secondary"),
    dbc.Row(
        [
            html.Div("Use box-select-tool from the figure to draw or erase marker"),
            dbc.Button(id="cl_marker_btndraw", children="draw", color="primary", size="sm",
                       style={"verticalAlign": "top",'display': 'inline-block', 'height': '33px', 'width':'auto'}),
            dbc.Button(id="cl_marker_btnerase", children="erase", color="danger", size="sm",
                       style={"verticalAlign": "top",'display': 'inline-block', 'height': '33px','width':'auto'}),
            html.Div(dcc.Dropdown(id='cl_markers_used', placeholder = "Select marker",
                                  # options=lst_m_us,
                                  # value=lst_m_us[0],
                                  clearable=False,
                                  style={'width': '100%', 'height': '33px', 'display': 'inline-block'}),
                 style={"width": "15%", "height":"33px",'display': 'inline-block'}),
           dbc.Button(id="cl_marker_btnedit", children="edit", color="warning", size="sm",
                       style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px', 'width': 'auto'}),
            html.Div(id="cl_div_addandrenamesection",
                     children=
            [

                dcc.Input(id="cl_inp_marker_add_or_rename", placeholder="enter marker name",
                      style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px'}),
                dbc.Button(id="cl_marker_btnrename", children="rename", color="warning", size="sm",
                           style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px'}),
                dbc.Button(id="cl_marker_btnadd", children="add", color="warning", size="sm",
                           style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px'}),
                dbc.Button(id="cl_marker_btncancel", children="cancel", color="info", size="sm",
                           style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px'})
            ],
                     style={"verticalAlign": "top", 'display': 'inline-block', 'height': '33px', 'width': '50%'},
                hidden = True),
        ],
        className="border border-5 bg-secondary"),

    dbc.Row([dcc.Graph(id='cl_fig_timeseries', config={"modeBarButtonsToRemove": ['lasso2d']})],
        className="border border-5 bg-secondary"),
    ])
    return c
def c_tab_stats():
    c = html.Div(dbc.Row([html.Div(
        [
        html.Div("Statistical parameters of markers, refresh to calculate"),
        dbc.Button(id="cl_btnstatrefresh", children="refresh", color="primary", size="sm",
                       style={"verticalAlign": "top"}),
        dash_table.DataTable(id ="cl_tbl_markersummary",
            #data=dfsummary.to_dict('records'),
            #columns=[{'id': c, 'name': c} for c in dfsummary.columns],
            #fixed_rows={'headers': True},
            #style_table={'height': 500},  # defaults to 500
            # style_cell = {'minWidth': 10, 'maxWidth': 20, 'width': 10}
            ),
        ])], className="border border-5 bg-secondary vh-100"))
    return c
def c_tab_spect():
    c = html.Div([
        dbc.Row([html.Div(id='cl_spectstatus',
                          children="If there is spectral information: select marker and acoustic parameter..."),
                 html.Div(children=
                 [html.Div(dcc.Dropdown(id='cl_drp_markers_spec', placeholder="Select marker",
                              # options=lst_m_us,
                              # value=lst_m_us[0],
                              clearable=False,
                              style={'width': '100%', 'height': '33px', 'display': 'inline-block'}
                               ),style={'width': '10%', 'height': '33px', 'display': 'inline-block'}),
                  html.Div(dcc.Dropdown(id='cl_drp_LnLeq_spec', placeholder="Select parameter",
                                        options=['Leq', 'L95'],
                                        value='Leq',
                                        clearable=False,
                                        style={'width': '100%', 'height': '33px', 'display': 'inline-block'}
                                        ), style={'width': '10%', 'height': '33px', 'display': 'inline-block'}),
                  dbc.Button(id="cl_btn_plotspec", children="(re)plot", color="primary", size="sm",
                             style={'width': 'auto', "verticalAlign": "top", 'display': 'inline-block', 'height': '33px'}
                             )
                  ],style={"width": "100%", "height": "33px", 'display': 'inline-block'})],
                className="border border-5 bg-secondary"),
        dbc.Row(children=[dcc.Graph(id='cl_fig_spect', config={"modeBarButtonsToRemove": ['lasso2d']})],
                className="border border-5 bg-secondary")
        ])
    return c
def c_tabs_together():
    """3 tabs together: time, stat and spect"""
    c = html.Div([
        dbc.Tabs([
            dbc.Tab(children=c_tab_time(), label="Time", tab_id="tab_timeseries"),
            dbc.Tab(children=c_tab_stats(), label="Stats", tab_id="tab_stats"),
            dbc.Tab(children=c_tab_spect(), label="Spect", tab_id="tab_spect")],
            id="tabstotal",
            active_tab="tab_timeseries")])
    return c
def c_divhelpfields():
    """ help fields that could be hidden"""
    c = html.Div([
        html.P(children="helpfields"),
        html.Div(id="cl_begintime",
                 #children=begintime,
                 style={'display': 'inline-block'}),
        html.Div(id="cl_ann", children='no audiofile loaded',
                 style={'margin-left': '10px', 'display': 'inline-block'}),
        html.Div(id="cl_selectbegin", children='no domain selection begin', style={'display': 'inline-block'}),
        html.Div(id="cl_selectend", children='no domain selection end',
                 style={'margin-left': '10px', 'display': 'inline-block'}),
        html.Div(id="cl_audiofile", children='no audiofile loaded', hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_markererase", children="marker delete not yet used", hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_markerdraw", children="marker add not yet used", hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_statsrefresh", children="stats refresh not yet used", hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_hlp_filename", children="filename not yet known", hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_hlp_save", children="button save not yet used", hidden=False,
                 style={'margin-left': '10px', 'display': 'inline-block', 'width': '100%'}),
        html.Div(id="cl_hlp_figure", children="figure not loaded yet", hidden = False),
        html.Div(id="cl_hlp_columnorder", children="Columns are ordered like this: ..."),
        html.Div(dcc.Store(id='cl_store_df', data=dict())),
        html.Div(dcc.Store(id='cl_store_c_always', data=dict())),
        html.Div(dcc.Store(id='cl_store_c_markers', data=dict()))
    ], hidden=True)
    return c
def c_total_layout():
    c = dbc.Container([
        dbc.Row([
            dbc.Col([c_lefties()], width=1),
            dbc.Col([c_tabs_together()], width=11)]),
        dbc.Row(dbc.Col([c_divhelpfields()], width=12))], fluid=True)
    return c
