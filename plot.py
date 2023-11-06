import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Patch
import datetime
import pandas as pd
import numpy as np

def lst_seriekleuren():
    # lst_kleuren = ['blue', 'orange', 'red', 'pink', 'green', 'purple']
    lst_kleuren = ['black', 'red', 'brown', 'magenta', 'black', 'green', 'purple']
    return lst_kleuren


def lst_markerkleuren():
    lst_kleuren = ['red', 'blue', 'yellow', 'pink', 'purple', 'brown', 'salmon']
    return lst_kleuren

def create_fig_time_vs_db(df,
                          lst_fld_always,
                          lst_fld_mark):
    """
    Creates a Plotly line chart figure with:
     - a time series of decibels
     - markers on top
    :param
        df: dataframe
        lst_fld_always: list of 2 fields(strings) that are always necessary. The first field is always time (x-axis)
        lst_fld_mark: list of fields(strings) with markers. Special marker is Exclude
    :return: figure with time series
    """
    # https://plotly.com/python/subplots/
    # from plotly.subplots import make_subplots
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[10, 100], vertical_spacing=0.01,
                        specs=[[dict()],  # specs upper graph default
                               [dict(type='xy', secondary_y=True)]]
                        )
   # Main time series
    fig.add_scattergl(x=df[lst_fld_always[0]], y=df[lst_fld_always[1]],
                      mode='markers+lines', name='LAeq,1s',
                      line=dict(width=1, color='black'),
                      marker=dict(color='rgba(0,0,0,0)'),  # opacity =0
                      row=2, col=1)

    # markers
    for i in range(0, len(lst_fld_mark)):
        fig.add_trace(go.Scattergl(x=df[lst_fld_always[0]],
                                   y=df[lst_fld_mark[i]] * (i+1),
                                   mode='lines', name=str(lst_fld_mark[i]),
                                   line=dict(width=3, color=lst_markerkleuren()[i])),
                      row=1, col=1)
    # layout

    # Lower Axis
    # # # # # # # # #
    fig.update_xaxes(title="tijd", zeroline=False, showgrid=True,
                     gridwidth=1, gridcolor='gray', tickangle=0,
                     row=2, col=1)
    # Y1 (primary)
    fig.update_yaxes(title_text="db(A)", zeroline=False, showgrid=True,
                     gridwidth=1, gridcolor='gray', tickangle=0,
                     row=2, col=1, secondary_y=False)

    # Y2 (secundary)
    fig.update_yaxes(title_text='', zeroline=False, showgrid=False,
                     gridwidth=1, gridcolor=None, tickangle=0,
                     row=2, col=1, secondary_y=True)
    # ticks - hide all
    fig.update_yaxes(showticklabels=False)
    #       - show only bottom Y-ticks, except the secondary y-axis ticks
    fig.update_yaxes(showticklabels=True, row=2, col=1, secondary_y=False)
    fig.update_layout(showlegend=True, legend=dict(orientation='h'), plot_bgcolor="white")

    fig.update_layout(height=700, uirevision=1) # uirevision gelijk welke, vaste waarde.
                                                # zorgt ervoor dat de zoom niet verandert bij updaten
    return fig

def dct_timeannotationlayout(time):
    """create a dictionary containing the layout-properties of a specific time-annotation
    :param:
    time: time object like datetime.datetime(2021, 11, 16, 9, 0, 0)
    :return: dictionary
    """
    txt = str(time)
    dct= dict(
        x=time,
        y=0.9,  # de pijl beslaat 90 procent van de hoogte  van de grafiek
        xref='x',
        yref='paper',
        xshift=0,
        text=txt,  # annotatie is datumobject, omgezet naar text
        showarrow=True,
        arrowhead=0,  # geen kop op de pijl
        ax=0,  #
        ay=500,  # een pijl van 500 pixels lang boven het label
        font=dict(family="Courier New, monospace", size=14, color="#ffffff"),
        align="center",
        arrowcolor = "rebeccapurple",
        bgcolor="rebeccapurple")
    return dct
def fig_add_annotation(fig, time):
    """
    add an annotation on an actual moment (time) of interest
    in a figure with a time series
    :param
        fig: Plotly line chart figure
        time: time object -> datetime.datetime(2021, 11, 16, 9, 0, 0)
    :return: figure with time series and annotation
    """
    # delete the previous annotation
    fig.layout.annotations = None
    # add the new annotation
    fig.add_annotation(dct_timeannotationlayout(time))
    return fig

def fig_patch_updated_marker(fig,str_marker,dct_df):
    """"
    make a figure patch
    :param:
        fig: Plotly chart figure with multiple traces
        str_marker: the name of the trace that is to be patched (tracename = markername)
        df: pandas dataframe containing the data of the marker (columname = markername)
    :return:
    patch of a figure
    """
    df = pd.DataFrame(dct_df)
    patched_figure = Patch()
    # get the index of the trace in the figure to be updated
    for i, trace in enumerate(fig['data']):
        if trace['name'] == str_marker:
            marker_i = i
    patched_figure["data"][marker_i]["y"] = df[str_marker].values * (marker_i)
    return patched_figure

def fig_patch_renamed_marker(fig,newname, oldname):
    """"
    make a figure patch
    :param:
        fig: Plotly chart figure with multiple traces
        str_marker: the name of the trace that is to be patched (tracename = markername)
        df: pandas dataframe containing the data of the marker (columname = markername)
    :return:
    patch of a figure
    """
    patched_figure = Patch()
    # get the index of the trace in the figure to be updated
    for i, trace in enumerate(fig['data']):
        if trace['name'] == oldname:
            marker_i = i
    patched_figure["data"][marker_i]['name']=newname
    return patched_figure

def fig_patch_added_marker(fig,newname):
    """"
    make a figure patch
    :param:
        fig: Plotly chart figure with multiple traces
        newname: the name of the extra, new trace (tracename = markername)
    :return:
    patch of a figure
    """
    patched_figure = Patch()
    # get the index of the next trace (aka marker) that is being added
    i = len(fig['data'])
    # get the number of datarows in the figure
    d_i = len(fig['data'][0]['x'])
    patched_figure['data'].append(go.Scattergl({'line': {'color': lst_markerkleuren()[i], 'width': 3},
                                                      'mode': 'lines',
                                                      'name': newname,
                                                      'x': fig['data'][0]['x'],
                                                      'y':[np.nan, ]* d_i,
                                                      'type': 'scattergl', 'xaxis': 'x', 'yaxis': 'y'}))

    return patched_figure

def domain_get_start_end(dct_relayoutdata):
    isselected = dct_relayoutdata.get("selections", -1)  # -1 will be returned if key is not found
    begin = -1
    einde = -1
    if isselected != -1:
        try:
            begin = isselected[0]["x0"][0:19]  # timestamp is 19 charachters long
            einde = isselected[0]["x1"][0:19]
        except IndexError:
            pass
    return begin, einde
def create_fig_spectrum(df, str_grafiektitel):
    # input: xwaarden, ywaarden as dataframe
    # example call function as: plotspectrum(df2['terts'], df2['dBA'])

    fig = go.Figure()
    kleuren = ['grey', ] * 31  # 30 keer dezelfde kleur
    kleuren[30] = 'black'  # alleen de laatste is magenta
    fig.add_trace(go.Bar(x=df['hz'], y=df['lzeq_t']))

    fig.update_traces(marker_color=kleuren)

    fig.update_layout(title=str_grafiektitel,
                      xaxis=dict(title='herz', zeroline=False, showgrid=False, tickangle=270),
                      yaxis=dict(title='dBZ', zeroline=False, showgrid=True, gridwidth=1, gridcolor='grey'))
    fig.update_layout(title=str_grafiektitel, title_x=0.5, plot_bgcolor="white")
    return fig
# def create_fig_spect():
#     fig_spect = go
#     return fig_spect

#print(dct_timeannotationlayout(datetime.datetime(2021, 11, 16, 9, 0, 0)))
