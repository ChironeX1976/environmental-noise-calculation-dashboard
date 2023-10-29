import os
from collections import Counter
import numpy as np
import pandas as pd
from definitions import standard_column_names, folder_and_file_paths, standardize, standardfile_prefix
import io
import base64
# def decode_and_code_to_iostring(content_string):
#     """decodes string from from a dash core component - upload to iostring (readable for pandas)"""
#     strdecoded = base64.b64decode(content_string)
#     iostring = io.StringIO(strdecoded.decode('utf-8'))
#     return iostring
def categorize_inputdata(decoded):
    """Categorise type of sound level meter (slm),
       by reading the first 5 lines of the raw dataset (string),
    At the moment only the data from a slm called Bruel and Kjaer-2250 is programmed
     :param
        iostring: string from from a dash core component - upload
    :returns
        invalid: True when the data source is unknown
        slm: (abbrev, sound level meter) string with the name of the data source or unkown when it is invalid
     """
    lst_slmtypes =["Bruel and Kjaer-2250", "standardized", "01dB-duo"]
    # read first 5 lines of dataset. the \t is tricky. sometimes it crashes. errorhandling should be programmed later
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')), delimiter="\t", engine="python", decimal=',')
    # categorize through some standard column-names
    if df.columns[0] == "Project Name":     # bruel and kjaer - 2250
        slmtype = lst_slmtypes[0]
        invalid = False
    elif df.columns[0] == 'time':           # a file created with this dashboard (based on any type of slm)
        slmtype = lst_slmtypes[1]
        invalid = False
    elif df.columns[0] == "Period Start":   # 01dB
        slmtype= lst_slmtypes[2]
        invalid = False
    # elif                                  # other types of sound level meter, svantek, cirrus, norsonic...
        #...
    else:                                   # unknown
        slmtype="unknown file"
        invalid = True
    return invalid, slmtype
def data_prep(slmtype:str, decoded:str, filename:str):
    if slmtype == "Bruel and Kjaer-2250":
        lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound = b_en_k_dataprep(decoded, filename)
    elif slmtype == "standardized":
        lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound = standard_dataprep(decoded, filename)
    else:
        print(slmtype, ", not programmed yet")
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound

def b_en_k_dataprep(decodeddata:str,f:str):
    """ Read BRUEL AND KJAER TXT file and prepare data.
    :param
        strdecoded: a raw string from a dash core component Upload containing the data of a measurement
        f: the filename
    :return
        lst_flds_a: list of fields that are always needed to plot: a timestamp and a noise level
        lst_flds_st: list of fields with statistics data (not yet used, to be programmed later for really detailed statistics)
        lst_flds_m_used: list of fields with markers of events during measurement
        begintime: timestamp of the very first moment of the data
        df: dataframe
        dfsummary: dataframe with summary of statistics of marker (events)"""

    # get standard columnames and filepaths
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    dir_root, dir_data, dir_audio, f= folder_and_file_paths(f)
    # read into pandas dataframe
    df = pd.read_csv(io.StringIO(decodeddata.decode('utf-8')), delimiter="\t", skiprows=0, engine="python", decimal=',')
    # standardize a few essential column-names of the dataframe
    standardize(df, str_c_soundpath, str_c_exclude, str_c_time, str_c_laeq1s)
    #get interesting fields
    lst_flds_a = col_lst_always(str_c_time,str_c_laeq1s)
    lst_flds_st = b_en_k_fldslst_stats()
    lst_flds_m_all = b_en_k_fldslst_marker_all(df) # not used in this program
    lst_flds_m_unused = b_en_kfldlst_marker_unused(df,lst_flds_m_all) # not used in this program
    lst_flds_m_used = b_enkfldlst_marker_used(lst_flds_m_all,lst_flds_m_unused)
    #create time object
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='%d/%m/%Y %H:%M:%S')
    begintime = df[str_c_time].min()
    # replace 0 by np.nan
    df.replace(0, np.nan, inplace=True)
    # Make a small list and dataframe of the paths with soundfiles and update the main dataframe
    lstsound, dfsoundpaths = b_en_k_soundpaths(dir_audio, df, lst_flds_a[0], str_c_soundpath)
    # change the soundpaths in the original dataframe
    df = df.merge(dfsoundpaths, on=['time'], how='left', suffixes=('_x', '_y'))
    df.drop(columns=[str_c_soundpath + '_x'], inplace=True)
    df.rename(columns={str_c_soundpath + '_y': str_c_soundpath}, inplace=True)
    df = df.reset_index(drop=True)
    # selection  interesting fields
    lst_interesting = lst_flds_a + lst_flds_m_used + [str_c_soundpath] + lst_flds_st
    print('selecting datafields: ', lst_interesting)
    df = df[lst_interesting]
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound

def standard_dataprep(decodeddata:str,f:str):
    """Read STANDARD TXT file and prepare data. This STANDARD is created by another session of this program and saved
    :param
        strdecoded: a raw string from a dash core component Upload containing the data of a measurement
        f: the filename
    :return
        lst_flds_a: list of fields that are always needed to plot: a timestamp and a noise level
        lst_flds_st: list of fields with statistics data (not yet used, to be programmed later for really detailed statistics)
        lst_flds_m_used: list of fields with markers of events during measurement
        begintime: timestamp of the very first moment of the data
        df: dataframe
        dfsummary: dataframe with summary of statistics of marker (events)"""
    # get standard columnames and filepaths
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    dir_root, dir_data, dir_audio, f = folder_and_file_paths(f)
    # read into pandas dataframe
    df = pd.read_csv(io.StringIO(decodeddata.decode('utf-8')), delimiter="\t", skiprows=0, engine="python", decimal=',')
    # standardize a few essential column-names of the dataframe
    standardize(df, str_c_soundpath, str_c_exclude, str_c_time, str_c_laeq1s)
    # get interesting fields
    lst_flds_a = col_lst_always(str_c_time, str_c_laeq1s)
    lst_flds_st = b_en_k_fldslst_stats()
    lst_flds_m_used = std_fldslst_marker_all(df)
    # create time object
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='%Y-%m-%d %H:%M:%S')
    begintime = df[str_c_time].min()
    # replace 0 by np.nan
    df.replace(0, np.nan, inplace=True)
    # Make a small list and dataframe of the paths with soundfiles and update the main dataframe
    lstsound, dfsoundpaths = std_soundpaths(dir_audio, df, lst_flds_a[0], str_c_soundpath)
    # selection  interesting fields
    lst_interesting = lst_flds_a + lst_flds_m_used + [str_c_soundpath] + lst_flds_st
    print('selecting datafields: ', lst_interesting)
    df = df[lst_interesting]
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound


def std_fldslst_marker_all(df):
    """get all fields whith marker data in list
    marker data-value is always 0 or 1 and nothing else
    """
    lst = []
    for c in df.columns.tolist():
        if df[c].isin([np.nan, 1]).all():
             lst.append(c)
    return lst

def b_en_k_fldslst_marker_all(df):
    """get all fields whith marker data in list
    marker data-value is always 0 or 1 and nothing else
    """
    lst = []
    for c in df.columns.tolist():
        if df[c].isin([0, 1]).all():
             lst.append(c)
    return lst
def b_en_kfldlst_marker_unused(df,lst):
    """from a list of markerfields -> get those who are unused
    (where all values in the column are equal to 0)
    exception: exclude marker field must always be kept
    """
    lst_unused = []
    for l in lst:
        if df[l].isin([0]).all():
            if l not in ["Exclude", 'exclude']: # exclude must always be "useable" -  even if it is not yet used
                lst_unused.append(l)
    return lst_unused
def b_enkfldlst_marker_used(lstall, lstunused):
    """ substract two lists of strings:
    all markers minus the unused markers equals the used markers
    """
    c1 = Counter(lstall)
    c2 = Counter(lstunused)
    diff = c1 - c2
    return list(diff.elements())
def col_lst_always(str_c_time, str_c_laeq1s):
    """Put the columnames that are always interesting into list"""
    lst = [str_c_time, str_c_laeq1s]
    return lst
def b_en_k_fldslst_stats():
    """Put statistical fields, that are always interesting, into list"""
    lst = ['LAF1,0', 'LAF5,0', 'LAF10,0', 'LAF50,0', 'LAF90,0', 'LAF95,0', 'LAF99,0']
    return lst
def lst_to_dict(lst):
    """turn list into a dictionary, label and value are the same
    for dcc components
    eg: list [l1,l2,l3...]
        {'label': 'l1', 'value': 'l1'},
        {'label': 'l2', 'value': 'l2'}]"""
    res_dct = {lst[i]: lst[i] for i in range(0, len(lst))}
    return res_dct

def b_en_k_soundpaths(dir_audio, df, fld_time:str,fld_soundpath: str):
    """make a list of time(string) and corresponding filepaths(string) of the sound files.
    original filepaths are changed to new, Targetfilepaths,
    based on the file number and standard annotation folders and separators
    :param
    dir_audio : directory where audio files are available (local)
    df: dataframe with lots of data
    fld_time: a string, columname, where the timestamp is in the df
    fld_soundpath: a string, columname, where the original soundpath is (that is altered in this def)
    :return
    a list in a typical format for a dcc.dropdown component"""
    # get interesting fields for this purpose: time and field with original path
    dfsoundpaths = df[[fld_time,fld_soundpath]]
    # drop the empty rows
    dfsoundpaths = dfsoundpaths[~dfsoundpaths[fld_soundpath].isna()]
    if len(dfsoundpaths) == 0:
        print ('no audio data available')
    else:
        # create tmp field with target path
        dfsoundpaths.loc[:,'tmp_targetpath'] = dir_audio
        # create tmp field with audiofilename:  get sound - file name from original path
        dfsoundpaths.loc[:,'tmp_filename'] = dfsoundpaths[fld_soundpath].apply(os.path.basename)
        # join target filepath and the filename
        dfsoundpaths[fld_soundpath]= dfsoundpaths['tmp_targetpath'].str.cat(dfsoundpaths['tmp_filename'], sep = os.sep)
        # drop tmp fields
        dfsoundpaths = dfsoundpaths[[fld_time, fld_soundpath]]
        #reindex
        dfsoundpaths = dfsoundpaths.reset_index(drop=True)

    # dataframe of soundpaths to list in format of dcc component
    lst = reform_df_to_dccdropdownlist(dfsoundpaths, fld_time,fld_soundpath)
    return lst, dfsoundpaths

def std_soundpaths(dir_audio, df, fld_time:str,fld_soundpath: str):
    """make a list of time(string) and corresponding filepaths(string) of the sound files.
    based on the file number and standard annotation folders and separators
    :param
    dir_audio : directory where audio files are available (local)
    df: dataframe with lots of data
    fld_time: a string, columname, where the timestamp is in the df
    fld_soundpath: a string, columname, where the original soundpath is (that is altered in this def)
    :return
    a list in a typical format for a dcc.dropdown component"""
    # get interesting fields for this purpose: time and field with original path
    dfsoundpaths = df[[fld_time,fld_soundpath]]
    # drop the empty rows
    dfsoundpaths = dfsoundpaths[~dfsoundpaths[fld_soundpath].isna()]
    # dataframe of soundpaths to list in format of dcc component
    lst = reform_df_to_dccdropdownlist(dfsoundpaths, fld_time,fld_soundpath)
    return lst, dfsoundpaths

def reform_df_to_dccdropdownlist(df, fld_label:str, fld_value:str):
    """reform a given dataframe to
    label, value as stated by the dcc dropdown component from dash"""
    # objects are not allowed, so change everything to string (i.c. timestamp)
    df=df.astype(str)
    dct = df.to_dict('records')
    lst = [{'label': d[fld_label], 'value': d[fld_value]} for d in dct]
    return lst

def df_get_index_in_df (df, strtimecolumn, strtimestart, strtimestop):
    i_start = int(df.loc[df[strtimecolumn] == strtimestart].index[0])
    i_stop = int(df.loc[df[strtimecolumn] == strtimestop].index[0])
    return i_start, i_stop
def df_marker_edit (dct_df, strmarkercolumn, strtimestart, strtimestop, val):
    """change a marker in a dataframe between two time values
    :param:
    dct_df: a dictionary of a dataframe (from a dcc.store component)
    strtimecolumn = string of the time columnname in the dataframe
    strmarkercolumn: string of the marker column in the dataframe
    strtimestart, stop = string of the selected time value eg 2023 02 01 14:15:00
    val = 0 or 1"""
    # get standard columnames and filepaths
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    if val == 0:
        val = np.nan
    #error handling of the selected time
    if ((strtimestart != -1) and (strtimestop != -1)):
        # make dataframe of dictionary
        df= pd.DataFrame(dct_df)
        # i do not understand, but the datetime is not a date-time column anymore, so first apply datetime
        df[str_c_time] = pd.to_datetime(df[str_c_time], format='%Y-%m-%d %H:%M:%S')
        # get index in the dataframe of the start and stop marker
        start, stop = df_get_index_in_df(df, str_c_time, strtimestart, strtimestop)
        # apply the value for the selected marker
        df.loc[start:stop, strmarkercolumn] = val
        # turn dataframe into dictionary again
        dct_df = df.to_dict("records")
    return dct_df
def df_marker_rename_valid(oldname, newname,dct_markers):
    valid = True
    if oldname =='exclude':
        print('exclude can not be changed')
        valid = False
    elif newname in dct_markers:
        print('no duplicate markers allowed')
        valid = False
    elif oldname is None:
        valid = False
    elif newname is None:
        valid = False
    return valid

def df_marker_add_valid(newname,dct_markers):
    valid = True
    if newname in dct_markers:
        print('no duplicate markers allowed')
        valid = False
    elif newname is None:
        valid = False
    return valid
def df_marker_rename(dct_df, oldname, newname, dct_markers):
    """rename the markers: exclude cannot be renamed, also no duplicate names are allowed
    these exceptions are captured before getting further with this function"""
    valid = df_marker_rename_valid(oldname, newname, dct_markers)
    if valid:
        # rename column in the df
        df = pd.DataFrame(dct_df)
        df.rename(columns={oldname:newname}, inplace=True)
        # rename the marker name in the dct_markers
        i=dct_markers.index(oldname)
        dct_markers.remove(oldname)
        dct_markers.insert(i, newname)
        # turn df into dict again
        dct_df = df.to_dict("records")
    return valid, dct_df, dct_markers

def df_marker_add(dct_df, newname, dct_markers):
    """add a marker: duplicate names are not allowed
    these exceptions are captured before getting further with this function"""
    valid = df_marker_add_valid(newname, dct_markers)
    if valid:
        # rename column in the df
        df = pd.DataFrame(dct_df)
        df[newname] = np.nan
        # append the marker name in the dct_markers
        dct_markers.append(newname)
        # turn df into dict again
        dct_df = df.to_dict("records")
    return valid, dct_df, dct_markers

def saveas_standard_csv_in_data_dir(dct_df,dir_data, filename):
    prefix = standardfile_prefix()
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath,str_c_exclude = standard_column_names()
    if filename[0:4] == prefix:
        prefix = ''
    filename = prefix + filename
    df = pd.DataFrame(dct_df)
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='%Y-%m-%d %H:%M:%S')
    df.to_csv(os.path.join(dir_data,filename), sep="\t", index=False)
    return

def logmean_of_column(df_in, str_col):
    """calculate logarithmic mean of a column in a dataframe
    :param:
        dataframe
        column
    """
    if len(df_in)==0: #errorhandling
        logmean = np.nan
    else:
        logmean = 10 * np.log10((10 ** ((df_in[str_col]) / 10)).mean())
    return round(logmean,1)

def Ln_of_column(df_in, str_col, lst_Ln):
    """calculate percentiles of a column in a dataframe
        :param:
            dataframe
            column
        """
    lst_rslt_Ln = []
    if len(df_in)<10: #errorhandling
        lst_rslt_Ln =[np.nan,]*7
    else:
        for n in lst_Ln[1]:
            n = 100 - n  # percentielen in akoestiek zijn omgekeerd vb: L95 = L5
            Ln = round(np.percentile(df_in[str_col], n),1)
            lst_rslt_Ln.append(Ln)
    return lst_rslt_Ln

def create_standarddf_of_markers_summary (dct_df, dct_markers):
    """ calculate a standard dataframe of the markers (summary)
    :param
        dct_df: dictionary of a dataframe with timeseries of decibels from a dash core component - store
        dct_markers: dictionary of markers in the dataframe
    :return
        dct_dfsummary: a dictionary of a dataframe with a summary of the statistics of the dataframe
            typical:  marker stats1 stats2  stats3
        """
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    df = pd.DataFrame(dct_df)
    lst_rslt=[]
    for m in dct_markers:
        lst_mvalues=[m]
        df_m = df.loc[df[m] == 1 & (df['exclude'].isnull())]
        laeq = logmean_of_column(df_m,str_c_laeq1s)
        lst_mvalues.append(laeq)
        lst_Ln = Ln_of_column(df_m, str_c_laeq1s,lst_c_percentiles)
        lst_mvalues.extend(lst_Ln)
        lst_rslt.append(lst_mvalues)
    dfsummary = pd.DataFrame(lst_rslt, columns=lst_c_summary, dtype='int8')
    dct_dfsummary = dfsummary.to_dict('records')
    return dct_dfsummary


# #
# str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude, str_c_time = definitions.standard_column_names()
# # #
# lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound= b_en_k_dataprep ("GL 22  007_LoggedBB.txt", str_c_soundpath, str_c_exclude, str_c_time)
# # # # print(df[['Start Time','Sound']])
# # # #
# # df_marker_del(df,"Start Time", "Sound", "2021-11-16 08:56:07", "2021-11-16 08:56:10")
# # print (df[['Start Time','Sound']])
#
# create_standarddf_of_events_summary(df,lst_flds_m_used, str_c_laeq1s)
#
