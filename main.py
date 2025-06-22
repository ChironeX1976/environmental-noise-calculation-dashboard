# # VERSION 04 ###
# #################
import base64
import datetime

import dash_bootstrap_components as dbc
from dash import dash, html, Patch
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

from data import get_fileproperties, data_prep, marker_apply, \
    saveas_standard_csv_in_data_dir, marker_rename, marker_add
from data_spec import data_spec_leq_or_ln
from data_stats import create_standarddf_of_markers_summary
from definitions import project_folder_and_path
from audio import update_audio_source
from plot import create_fig_time_vs_db, dct_timeannotationlayout, fig_add_annotation, \
    fig_patch_updated_marker, domain_get_start_end, fig_patch_renamed_marker, fig_patch_added_marker, \
    create_fig_spectrum

from components import c_total_layout

folder_root, folder_data = project_folder_and_path()

# ######################################################################################
# # #########                 BUILD DASHBOARD                                  #########
# ######################################################################################
app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = c_total_layout()
# ######################################################################################
# #########                CALLBACKS server-side                               #########
# ######################################################################################
# --------------------------------------------------------------------------------------
# ------------                TIME SERIES - audio                           ------------
# --------------------------------------------------------------------------------------
# audio file selection is pumped into the audioplayer
@app.callback(Output('cl_audiofile', 'children'), Output('cl_begintime', 'children'), Output('cl_audioplayer', 'src'),
              Input('cl_drop_audiotimeandfile', 'value'),
              State('cl_drop_audiotimeandfile', 'options'),
              State('cl_audiofolder','value'),
              prevent_initial_call=True)
def update_audiosource(dropdownval, dropdownoptions, audiofolder):
    dropdownval, o_datetime, s = update_audio_source(dropdownval, dropdownoptions, audiofolder)
    return dropdownval, o_datetime, s  # send the audio string to cl_audioplayer


# annotation of the actual audio-timestamp is patched on the graph
# allow duplicate is needed because figure is also updated from marker manipulations below
@app.callback(Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
              Input('cl_ann', 'children'),
              State('cl_hlp_figure', 'children'),
              prevent_initial_call=True)
def add_ann_to_fig(actualtimevalue, figurestatus):
    if figurestatus != "figure loaded":  # if the file/figure is not loaded yet, nothing can be patched
        raise PreventUpdate
    patched_figure = Patch()
    patched_figure["layout"]["annotations"].clear()
    patched_figure["layout"]["annotations"].extend([dct_timeannotationlayout(actualtimevalue)])
    return patched_figure
# --------------------------------------------------------------------------------------
# ------------           TIME SERIES - selection rectangle on fig           ------------
# --------------------------------------------------------------------------------------
@app.callback(
    Output('cl_selectbegin', 'children'), Output('cl_selectend', 'children'),
    Input('cl_fig_timeseries', 'relayoutData'),
    prevent_initial_call=True)
def selectiondomain(relayoutdata):
    begin, einde = domain_get_start_end(relayoutdata)
    return begin, einde  # json.dumps(relayoutData, indent=2)
# --------------------------------------------------------------------------------------
# ------------          TIME SERIES - marker manipulations                # ------------
# --------------------------------------------------------------------------------------
@app.callback(Output('cl_markererase', 'children'),
              Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
              Output('cl_store_df', 'data', allow_duplicate=True),
              Input('cl_marker_btnerase', 'n_clicks'),
              State('cl_store_df', 'data'),
              State('cl_fig_timeseries', 'figure'),
              State('cl_markers_used', 'value'),
              State('cl_selectbegin', 'children'),
              State('cl_selectend', 'children'),
              prevent_initial_call=True)
def markers_erase(n_clicks, dct_df, fig, marker, starttime, endtime):
    if marker is None:
        raise PreventUpdate
    else:
        # change data
        dct_df = marker_apply(dct_df, marker, starttime, endtime, 0)
        # patch new data into figure
        patched_figure = fig_patch_updated_marker(fig, marker, dct_df)
    return n_clicks, patched_figure, dct_df
@app.callback(Output('cl_markerdraw', 'children'),
              Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
              Output('cl_store_df', 'data', allow_duplicate=True),
              Input('cl_marker_btndraw', 'n_clicks'),
              State('cl_store_df', 'data'),
              State('cl_fig_timeseries', 'figure'),
              State('cl_markers_used', 'value'),
              State('cl_selectbegin', 'children'),
              State('cl_selectend', 'children'),
              prevent_initial_call=True)
def markers_draw(n_clicks, dct_df, fig, marker, starttime, endtime):
    if marker is None:
        raise PreventUpdate
    else:
        # change data
        dct_df = marker_apply(dct_df, marker, starttime, endtime, 1)
        # patch new data into figure
        patched_figure = fig_patch_updated_marker(fig, marker, dct_df)
    return n_clicks, patched_figure, dct_df


@app.callback(Output('cl_div_addandrenamesection', 'hidden', allow_duplicate=True),
              Input('cl_marker_btnedit', 'n_clicks'),
              prevent_initial_call=True)
def marker_editsection_setvisible(n_clicks):
    return False


@app.callback(Output('cl_div_addandrenamesection', 'hidden', allow_duplicate=True),
              Input('cl_marker_btncancel', 'n_clicks'),
              prevent_initial_call=True)
def marker_editsection_setinvisible(n_clicks):
    return True


@app.callback(Output('cl_div_addandrenamesection', 'hidden', allow_duplicate=True),
              Output('cl_store_df', 'data', allow_duplicate=True),
              Output("cl_store_c_markers", 'data', allow_duplicate=True),
              # Output("cl_markers_used","options", allow_duplicate=True),
              Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
              State('cl_store_df', 'data'),
              State("cl_store_c_markers", 'data'),
              State('cl_markers_used', 'value'),
              State('cl_inp_marker_add_or_rename', 'value'),
              State('cl_fig_timeseries', 'figure'),
              Input('cl_marker_btnrename', 'n_clicks'),
              prevent_initial_call=True)
def marker_renaming(dct_df, dct_markers, oldmarkername, newmarkername, fig, n_clicks):
    # change data when valid
    valid, dct_df, dct_markers = marker_rename(dct_df, oldmarkername, newmarkername, dct_markers)
    if not valid:
        raise PreventUpdate
    else:
        # patch new data into figure
        patched_figure = fig_patch_renamed_marker(fig, newmarkername, oldmarkername)
    return True, dct_df, dct_markers, patched_figure
@app.callback(Output('cl_div_addandrenamesection', 'hidden', allow_duplicate=True),
              Output('cl_store_df', 'data', allow_duplicate=True),
              Output("cl_store_c_markers", 'data', allow_duplicate=True),
              # Output("cl_markers_used","options", allow_duplicate=True),
              Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
              State('cl_store_df', 'data'),
              State("cl_store_c_markers", 'data'),
              State('cl_inp_marker_add_or_rename', 'value'),
              State('cl_fig_timeseries', 'figure'),
              Input('cl_marker_btnadd', 'n_clicks'),
              prevent_initial_call=True)
def marker_adding(dct_df, dct_markers, newmarkername, fig, n_clicks):
    # change data when valid
    valid, dct_df, dct_markers = marker_add(dct_df, newmarkername, dct_markers)
    if not valid:
        raise PreventUpdate
    else:
        # patch new data into figure
        patched_figure = fig_patch_added_marker(fig, newmarkername)
    return True, dct_df, dct_markers, patched_figure
@app.callback(Output('cl_drp_markers_spec', 'options'),
              Output('cl_markers_used', 'options'),
              Input('cl_store_c_markers', 'data'),
              prevent_intial_call=True)
def refresh(dct_markers):
    return dct_markers, dct_markers
# --------------------------------------------------------------------------------------
# ------------                 STATISTICS refresh                           ------------
# --------------------------------------------------------------------------------------
@app.callback(Output('cl_statsrefresh', 'children'),
              Output("cl_tbl_markersummary", 'data'),
              Input('cl_btnstatrefresh', 'n_clicks'),
              State("cl_store_df", 'data'),
              State("cl_store_c_markers", 'data'),
              prevent_initial_call=True)
def refreshstatistics(n_clicks, dct_summary, dct_markers):
    # update data of the summary statistics dataframe
    dct_dfsummary = create_standarddf_of_markers_summary(dct_summary, dct_markers)
    return n_clicks, dct_dfsummary
# --------------------------------------------------------------------------------------
# ------------                 PLOT SPECTRUM                                ------------
# --------------------------------------------------------------------------------------
@app.callback(Output('cl_fig_spect', 'figure'),
              Input('cl_btn_plotspec', 'n_clicks'),
              State('cl_drp_markers_spec', 'value'),
              State('cl_drp_LnLeq_spec', 'value'),
              State("cl_store_df", 'data'),
              prevent_initial_call=True)
def plotspectrum(n_clicks, marker, parameter, dct_df):
    df = data_spec_leq_or_ln(dct_df, marker, parameter)
    titel = marker + ' ' + parameter
    fig = create_fig_spectrum(df, titel)
    return fig
# --------------------------------------------------------------------------------------
# ------------         SAVE DATA after editing                              ------------
# --------------------------------------------------------------------------------------
@app.callback(Output("cl_hlp_save", 'children'),
              Input('cl_btn_save', 'n_clicks'),
              State("cl_store_df", 'data'),
              State('cl_savefileas', 'value'),
              State('cl_store_c_always', 'data'),
              State('cl_store_c_markers', 'data'),
              State('cl_hlp_columnorder', 'children'),
              prevent_initial_call=True)
def save(n_clicks, dct_df, filename, col_always, col_markers, col_order):
    saveas_standard_csv_in_data_dir(dct_df, folder_data, filename, col_always, col_markers, col_order)
    return n_clicks
# --------------------------------------------------------------------------------------
# ------------         INITIAL DATA LOAD into dash app                      ------------
# --------------------------------------------------------------------------------------
@app.callback(
    Output('cl_filestatus', 'children'),
    Output('cl_hlp_filename', 'children'),
    Output('cl_hlp_figure', 'children'),
    Output('cl_begintime', 'children', allow_duplicate=True),
    Output("cl_store_df", 'data'),
    Output("cl_store_c_always", 'data'),
    Output("cl_store_c_markers", 'data'),
    Output("cl_fig_timeseries", 'figure', allow_duplicate=True),
    Output("cl_drop_audiotimeandfile", "options"),
    Output("cl_spectstatus", "children"),
    Output("cl_hlp_columnorder", "children"),
    Input('cl_upload01', 'contents'),
    State('cl_upload01', 'filename'),
    State('cl_audiofolder','value'),
    prevent_initial_call=True
)
def load_data_into_layout(strcontent, f, audiofolder):
    # initialize empty dictionaries,  lists and dummies
    dfdict, dfsummarydict, fig = dict(), dict(), dict()
    lst_flds_a, lst_flds_m_used, lstsound, kolomvolgorde = [], [], [], []
    figurestatus = "figure not loaded yet"
    begintime = "1976-07-02 23:30:00"  # my dummy birthday
    spectralinfo = "there is no spectral info"
    # decode inputstring of dropped file
    content_type, content_string = strcontent.split(',')  # split content string from dcc
    decoded = base64.b64decode(content_string)
    properties = get_fileproperties(decoded, f)
    invalid = properties['invalid']
    status = properties['slmtype']
    # data preparation only if sonometer-type is known
    if not invalid:
        lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo = \
            data_prep(slmtype=status, decoded=decoded, filename=f, dir_audio=audiofolder)
        # store column-order for saving (dictionaries don't preserve this order)
        kolomvolgorde = df.columns.to_list()
        # put the dataframe in dcc store as a dict for later use
        dfdict = df.to_dict("records")
        fig = create_fig_time_vs_db(df, lst_flds_a, lst_flds_m_used)
        fig_add_annotation(fig, begintime)
        figurestatus = "figure loaded"
    return status, f, figurestatus, begintime, \
           dfdict, lst_flds_a, lst_flds_m_used, \
           fig, lstsound, spectralinfo, kolomvolgorde
# ######################################################################################
# #########          CALLBACK client-side (audio annotation on figure)         #########
# ######################################################################################
app.clientside_callback(
    """
    function TrackCurrentTime(jsbegintime, jsinterval)
    // Get the acutal time from cl_audioplayer based on :
    //          the begintime of the graph, 
    //          added with 
    //          the elapsed time of the audioplayer 
    // Parameters:
    //      jsbegintime: begintime from html component needed to calculate annotation position
    //      jsinterval: interval which states the update-speed (ms) of the new value of the audio element
    // Return: txt_ann: a textual annotation with the actual timestamp
    {
    // HELP-FUNCTIONS --->
    // Help-function to add seconds to a given date returning new date
    function addSeconds(date, seconds) {date.setSeconds(date.getSeconds() + seconds);return date;}
    // Help-function to get iso-string of the local - time object
    // (function "toISOString" gives string of time object at Greenwich, and here is not Greenwich)
    function getLocalISOString(date) {
    const offset = date.getTimezoneOffset()
    const offsetAbs = Math.abs(offset)
    const isoString = new Date(date.getTime() - offset * 60 * 1000).toISOString()
    return `${isoString.slice(0, -1)}${offset > 0 ? '-' : '+'}
    ${String(Math.floor(offsetAbs / 60)).padStart(2, '0')}:${String(offsetAbs % 60).padStart(2, '0')}`
    }
    // <--- HELP-FUNCTIONS
    // MAIN - FUNCTION --->
    // get value of audioplayer and calculate datetime-object
    const myaudio = document.getElementById("cl_audioplayer");
    const time_cur_s = Math.round(myaudio.currentTime);
    const o_time_start = new Date(jsbegintime);
    const o_ann = addSeconds(o_time_start, time_cur_s);
    const txt_ann = getLocalISOString(o_ann).substring(0, 19);
    // <--- MAIN - FUNCTION
    return txt_ann;
    }
    """,
    Output('cl_ann', 'children'),
    Input('cl_begintime', 'children'),
    Input('cl_interval', 'n_intervals'),  # every dcc.interval a new value is taken from audio component
)

if __name__ == '__main__':
    app.run(debug=True)