# # VERSION 04 ###
# #################
import base64
import datetime
import json
import dash_bootstrap_components as dbc
from dash import dash, html, Patch, dcc
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

from layout import c_total_layout

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
@app.callback(
    Output('cl_debug_dcc_filled', 'children'),
    Input('cl_allowed_audiofiles_store', 'data'),
    prevent_initial_call=True
)
def update_output(data):
    return "er zijn audiolijst-gegevens ingeladen"

@app.callback(
    [Output("cl_audio_loudness", "disabled"),
     Output("cl_loudness_locked_msg", "children")],
    Input("cl_audio_loudness", "value"),
    State("cl_allowed_audiofiles_store", "data"),
    prevent_initial_call=True
)
def lock_loudness_dropdown(value, store_data):
    if store_data and isinstance(store_data, list) and len(store_data) > 0:
        return True, f"Loudness locked. Reload  page to change."
    return False, ""

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
@app.callback(Output("cl_download_component", 'data'),
              Input('cl_btn_download', 'n_clicks'),
              State("cl_store_df", 'data'),
              State('cl_store_c_always', 'data'),
              State('cl_store_c_markers', 'data'),
              State('cl_hlp_columnorder', 'children'),
              prevent_initial_call=True)
def save(n_clicks, dct_df, col_always, col_markers, col_order):
    datastring, filename = saveas_standard_csv_in_data_dir(dct_df, col_always, col_markers, col_order)
    return dcc.send_string(datastring, filename)
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
    Output("cl_allowed_audiofiles_store", "data"),
    Output("cl_spectstatus", "children"),
    Output("cl_hlp_columnorder", "children"),
    Input('cl_upload01', 'contents'),
    State('cl_upload01', 'filename'),
    #State('cl_audiofolder','value'),
    prevent_initial_call=True
)
def load_data_into_layout(strcontent, f):#, audiofolder):
    # initialize empty dictionaries,  lists and dummies
    dfdict, dfsummarydict, fig = dict(), dict(), dict()
    lst_flds_a, lst_flds_m_used, lstsound, kolomvolgorde = [], [], [], []
    figurestatus = "figure not loaded yet"
    begintime = datetime.datetime.strptime("1976-07-02 23:30:00", '%Y-%m-%d %H:%M:%S')  # my dummy birthday
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
            data_prep(slmtype=status, decoded=decoded, filename=f)
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
# #######################################################################################
# #########          CALLBACKS client-side (audio annotation on figure)         #########
# #######################################################################################
# ==== 1. Audiofolder selection on the client ====
app.clientside_callback(
    """
    // open a folder with audiofiles on the client
    // make a list of audiofiles in the folder
    // check if the audiofiles in the folder are the same as in the toegestaneBestanden
    // if so, push the list to a dash core component  
    async function(n_clicks, toegestaneBestanden) {
        if (!n_clicks) return [[], ""];
        try {
            const dirHandle = await window.showDirectoryPicker();
            const toegestaneMap = new Map(toegestaneBestanden.map(item => [item.value, item.label]));
            const audioFiles = [];
            for await (const entry of dirHandle.values()) {
                if (
                    entry.kind === 'file' &&
                    /\.(mp3|wav)$/i.test(entry.name) &&
                    toegestaneMap.has(entry.name)
                ) {
                    const file = await entry.getFile();
                    const url = URL.createObjectURL(file);
                    audioFiles.push({ label: toegestaneMap.get(entry.name), value: url });
                }
            }
            if (audioFiles.length === 0) {
                return [[], "⚠️ Geen toegestane audio-bestanden gevonden"];
            }
            // Sorteer op datum/tijd in label
            audioFiles.sort((a, b) => new Date(a.label) - new Date(b.label));
            // console.log(audioFiles.value)
            return [audioFiles, ""];  // dropdown options, audio src, error msg, label
        } catch (err) {
            console.error("Folder selection cancelled or failed:", err);
            return [[], "⚠️ Folder selection was cancelled or failed."];
        }
    }
    """,
    [Output("cl_drp_audiofilelist", "options"),
     Output("cl_audio_errormessage", "children")],
    [Input("cl_btn_select_audiofolder", "n_clicks"),
     State('cl_allowed_audiofiles_store', 'data')])

# ==== 2. Audiofile selection en set begintime of the audiofile ====
app.clientside_callback(
    """
    function(selectedAudioUrl, options) {
        if (!selectedAudioUrl || !options) {
            return ["", ""];
        }
        // Zoek het label dat hoort bij de geselecteerde blob-url
        const match = options.find(opt => opt.value === selectedAudioUrl);
        const label = match ? match.label : "";
        // label must be iso 8601 format
        let isotimelabel=label;
        if (label.includes(" ")){
        isotimelabel = label.replace(" ", "T");
        }
        return [selectedAudioUrl, isotimelabel];
    }
    """,
    [Output("cl_audioplayer", "src"),
     Output("cl_begintime", "children")],
    [Input("cl_drp_audiofilelist", "value"),
     State("cl_drp_audiofilelist", "options")]
)
# ==== 3. Time follower via dcc.interval ====
app.clientside_callback(
    """
    function TrackCurrentTime(jsbegintime, jsinterval) {
    // HELP-FUNCTIONS
    function addSeconds(date, seconds) {
        date.setSeconds(date.getSeconds() + seconds);
        return date;
    }
    function getLocalISOString(date) {
        const offset = date.getTimezoneOffset();
        const offsetAbs = Math.abs(offset);
        const isoString = new Date(date.getTime() - offset * 60 * 1000).toISOString();
        return `${isoString.slice(0, -1)}${offset > 0 ? '-' : '+'}${String(Math.floor(offsetAbs / 60)).padStart(2, '0')}:${String(offsetAbs % 60).padStart(2, '0')}`;
    }
    // MAIN FUNCTION
    const myaudio = document.getElementById("cl_audioplayer");
    const time_cur_s = Math.round(myaudio.currentTime);
    // Controleer of jsbegintime geldig is
    let begintijd = jsbegintime;
    if (!begintijd || begintijd.trim() === "") {
        // Standaardwaarde instellen (bijv. 1 januari 2000 om 00:00:00)
        begintijd = "2000-01-01T00:00:00";
    }
    const o_time_start = new Date(begintijd);
    const o_ann = addSeconds(o_time_start, time_cur_s);
    const txt_ann = getLocalISOString(o_ann).substring(0, 19);
    //console.log("Begintijd:", begintijd, "→ Huidige tijd:", txt_ann);
    return txt_ann;
}
    """,
    Output('cl_ann', 'children'),
    Input('cl_begintime', 'children'),
    Input('cl_interval', 'n_intervals'),  # every dcc.interval a new value is taken from audio component
)
# ==== 4. Audio player with loudness factor ====
app.clientside_callback(
    """
    function(selectedAudioUrl, loudnessFactor) {
        const audioElement = document.getElementById("cl_audioplayer");
        if (!audioElement || !selectedAudioUrl) return;
        // Initieer audio context en nodes éénmalig via window
        if (!window.audioCtx) {
            window.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            window.sourceNode = window.audioCtx.createMediaElementSource(audioElement);
            window.gainNode = window.audioCtx.createGain();
            window.gainNode.gain.value = parseFloat(loudnessFactor);
            window.sourceNode.connect(window.gainNode).connect(window.audioCtx.destination);
            window.isConnected = true;
        }
        // Stel nieuwe bron in en speel af
        audioElement.src = selectedAudioUrl;
        audioElement.play();
        return null;
    }
    """,
    Output("cl_debug_selected_label", "children"),  # Dummy output
    Input("cl_drp_audiofilelist", "value"),
    State("cl_audio_loudness", "value")
)
if __name__ == '__main__':
    app.run(debug=True)