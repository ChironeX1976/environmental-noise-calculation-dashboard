import os
from collections import Counter
import numpy as np
import pandas as pd
from definitions import standard_column_names, folder_and_file_paths, standardize, standardfile_prefix, lstlaeqspellings
import io
import base64
import ntpath
import chardet
import csv
def get_fileproperties(decoded, filename):
    keys = ['filename', 'encoding', 'invalid', 'slmtype', 'delim', 'skiprows']
    # read the encoding
    enc = get_encoding(decoded[:1024])
    # make a small sample of the data
    sample = make_datasample(decoded,enc)
    # get type of sound level meter (slm)
    invalid, slmtype = get_slmtype(sample)
    # detect the delimiters in the sample
    delim = get_delimiter(sample)
    # get rows to skip in the dataset
    skiprows=get_rowstoskip(slmtype)
    values =[filename, enc, invalid, slmtype, delim, skiprows]
    properties=dict(zip(keys,values))
    return properties
def make_datasample(decoded, enc):
    # try to make a sample string
    try:
        sample_lines = decoded.decode(enc).splitlines()
        sample = '\n'.join(sample_lines[:30])  # or however many lines you want
    except UnicodeDecodeError:
        sample = decoded.decode('utf-8', errors='ignore')
    return sample
def get_encoding(bytessample):
    result = chardet.detect(bytessample)
    enc = result['encoding'] or 'utf-8'
    print('encoding:', enc)
    return enc
def get_delimiter(sample_text):
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample_text)
        delim = dialect.delimiter
        msg = "TAB" if delim == '\t' else delim
        print('delimiter:', msg)
        return delim
    except Exception as e:
        print(f"[DEBUG] Fout bij detecteren delimiter: {e}")
        return ',', 'fallback (default ,)'
def get_slmtype(sample_text):
    """
    Evaluates the first line of the sample text of a dataset.
    Returns:
        invalid:default = True
        skiprows (int): 1 if 'fusion' is in the first line,
                        0 if 'Project Name' is in the first line,
                        defaults to 0 otherwise.
        slmtype =  string with name of source
    """
    invalid = True
    first_line = sample_text.splitlines()[0].lower()
    if 'isodatetime' in first_line:
        invalid = False
        slmtype = 'standard pcm file'
    elif 'project name' in first_line:
        invalid = True
        if 'laeq' in first_line:
            slmtype = 'benk_bb -> put in standardization tool'
        if 'lzeq 500hz' in first_line:
            slmtype = 'benk_spectra -> put in standardization tool'
    elif 'fusion' in first_line:
        slmtype = 'fusion -> put in standardization tool'
    else:
        slmtype = "unknown slm file"
    return invalid, slmtype
def get_rowstoskip(slmtype):
    if slmtype == 'fusion':
        skiprows = 1
    else:
        skiprows = 0
    return skiprows
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
    if df.columns[0] == "Project Name" and df.columns[4] in lstlaeqspellings():     # bruel and kjaer - 2250
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
def data_prep(slmtype:str, decoded:str, filename:str, dir_audio:str):
    #if slmtype == "Bruel and Kjaer-2250":
    #    lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo = b_en_k_dataprep(decoded, filename)
    if slmtype == "standard pcm file":
        lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo = standard_dataprep(decoded, filename, dir_audio)
    else:
        print(slmtype, ", not programmed yet")
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo

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
    spectralinfo='no spectral info in file'
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
    df.reset_index(inplace=True, drop=True)
    # selection  interesting fields
    lst_interesting = lst_flds_a + lst_flds_m_used + [str_c_soundpath] + lst_flds_st
    df = df[lst_interesting]
    print('check if spectrum data are available, if so: add spectrum columns')
    # get spectrum filepath
    spectrumfilepath = correspondingspectrumfilepath(f, dir_data)
    # if file exists, then read loggedSpectra and merge with df
    if os.path.exists(spectrumfilepath):
        df_time_spec = pd.read_csv(spectrumfilepath, delimiter="\t", skiprows=0,
                                   engine="python", decimal=',')
        df_time_spec = standardize_spectrumdata(df_time_spec)
        df_time_spec[str_c_time] = pd.to_datetime(df_time_spec[str_c_time], format='%d/%m/%Y %H:%M:%S')
        df = pd.merge_ordered(df, df_time_spec, on=str_c_time, fill_method='ffil')
        lst_interesting = lst_interesting + lst_standard_spectrumcolumn_names()
        df = df[lst_interesting]
        df.reset_index(inplace=True, drop=True)
        spectralinfo = "Select marker, parameter and plot"
    print('selecting datafields: ', lst_interesting)
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo

def standard_dataprep(decodeddata:str,f:str, dir_audio):
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
        """
    # get standard columnames and filepaths
    spectralinfo = "no spectral info in file"
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    #dir_root, dir_data, dir_audio, f = folder_and_file_paths(f)
    # read into pandas dataframe
    df = pd.read_csv(io.StringIO(decodeddata.decode('utf-8')), delimiter="\t", skiprows=0, engine="python", decimal=',')
    # standardize a few essential column-names of the dataframe
    #standardize(df, str_c_soundpath, str_c_exclude, str_c_time, str_c_laeq1s)
    # get interesting fields
    lst_flds_a = col_lst_always(str_c_time, str_c_laeq1s)
    # get other interesting columns that are not mandatory
    # statistics columns
    lst_standardstats = ["laf1", "laf5", "laf10", "laf50", "laf90", "laf95", "laf99"]
    lst_flds_st = []  # no stat fields, empty list
    all_present = all(col in df.columns for col in lst_standardstats)
    if all_present: lst_flds_st = lst_standardstats  # statfields in a list
    # min max  columns
    lst_flds_minmax = []  # no minmax fields
    lst_standardsminmax = ['lafmin','lafmax']
    all_present = all(col in df.columns for col in lst_standardsminmax)
    if all_present: lst_flds_minmax = lst_standardsminmax  # minmax
    lst_flds_m_used = std_fldslst_marker_all(df, str_c_soundpath)
    # create time object
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='%Y-%m-%d %H:%M:%S')
    begintime = df[str_c_time].min()
    # replace 0 by np.nan
    #df.replace(0, np.nan, inplace=True)
    # Make a small list and dataframe of the paths with soundfiles and update the main dataframe
    lstsound, dfsoundpaths = std_soundpaths(dir_audio, df, lst_flds_a[0], str_c_soundpath)
    # selection  interesting fields

    # check if spectrum columns are in dataframe, if there are more interesting fields
    lst_standardspecs = ['lzeq25hz', 'lzeq31.5hz', 'lzeq40hz', 'lzeq50hz', 'lzeq63hz', 'lzeq80hz', 'lzeq100hz',
                 'lzeq125hz', 'lzeq160hz', 'lzeq200hz', 'lzeq250hz', 'lzeq315hz', 'lzeq400hz', 'lzeq500hz',
                 'lzeq630hz', 'lzeq800hz', 'lzeq1khz', 'lzeq1.25khz', 'lzeq1.6khz', 'lzeq2khz', 'lzeq2.5khz',
                 'lzeq3.15khz', 'lzeq4khz', 'lzeq5khz', 'lzeq6.3khz', 'lzeq8khz', 'lzeq10khz', 'lzeq12.5khz',
                 'lzeq16khz', 'lzeq20khz']
    lst_flds_specs = []
    all_present = all(col in df.columns for col in lst_standardspecs)
    if all_present:
        lst_flds_specs = lst_standardspecs  # statfields in a list
        spectralinfo = "Select marker, parameter and plot"
    lst_interesting = lst_flds_a + lst_flds_m_used + [str_c_soundpath] + lst_flds_st + lst_flds_minmax + lst_flds_specs
    # if set(lst_standard_spectrumcolumn_names()).issubset(set(df.columns)):
    #     lst_interesting = lst_interesting + lst_standard_spectrumcolumn_names()
    #     df = df[lst_interesting]
    #     spectralinfo = "Select marker, parameter and plot"
    # else:
    #     df = df[lst_interesting]
    print('selecting datafields: ', lst_interesting)
    return lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo


def std_fldslst_marker_all(df, str_c_soundpath):
    """get all fields whith marker data in list
    marker data-value is always np.nan or 1 and nothing else
    :exception soundpath this is a columname that can be completely empty but it is not a marker
    """
    lst = []
    for c in df.columns.tolist():
        #if c is not str_c_soundpath:
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
        # in LINUX machines ntpath is used in other cases: os.path is used
        dfsoundpaths.loc[:,'tmp_filename'] = dfsoundpaths[fld_soundpath].apply(ntpath.basename)
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

def get_index_in_df (df, strtimecolumn, strtimestart, strtimestop):
    """get the indexes of a selected domain between strtimestart and strtimestop
    if the passed strtimestart or strtimestop is out of the boundaries of the dataframe, then the index does not exist.
    this results in an error.
    Therefore, in that case, the begin- and/or the end-index of the dataframe is returned.
    :param:
        dataframe
        timecolumn in the dataframe
        timestart string with timestamp
        timestop string with timestamp
    :return: indexes within dataframe"""
    if df.loc[df[strtimecolumn] == strtimestart].size == 0:
        i_start = df.index[0]
    else:
        i_start = int(df.loc[df[strtimecolumn] == strtimestart].index[0])
    if df.loc[df[strtimecolumn] == strtimestop].size == 0:
        i_stop = df.index[-1]
    else:
        i_stop = int(df.loc[df[strtimecolumn] == strtimestop].index[0])
    return i_start, i_stop
def marker_apply (dct_df, strmarkercolumn, strtimestart, strtimestop, val):
    """apply a marker in a dataframe between two time values
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
        df[str_c_time] = pd.to_datetime(df[str_c_time],
                                        # format='%Y-%m-%d %H:%M:%S'    # does not work on a linuxmachine
                                        # format="ISO8601")             # dos not work on a windows computer
                                        format='%Y-%m-%dT%H:%M:%S')
        # get index in the dataframe of the start and stop marker
        start, stop = get_index_in_df(df, str_c_time, strtimestart, strtimestop)
        # apply the value for the selected marker
        df.loc[start:stop, strmarkercolumn] = val
        # turn dataframe into dictionary again
        dct_df = df.to_dict("records")
    return dct_df
def marker_rename_validation(oldname, newname, dct_markers):
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

def marker_add_validation(newname, dct_markers):
    valid = True
    if newname in dct_markers:
        print('no duplicate markers allowed')
        valid = False
    elif newname is None:
        valid = False
    return valid
def marker_rename(dct_df, oldname, newname, dct_markers):
    """rename the markers: exclude cannot be renamed, also no duplicate names are allowed
    these exceptions are captured before getting further with this function"""
    valid = marker_rename_validation(oldname, newname, dct_markers)
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

def marker_add(dct_df, newname, dct_markers):
    """add a marker: duplicate names are not allowed
    these exceptions are captured before getting further with this function"""
    valid = marker_add_validation(newname, dct_markers)
    if valid:
        # rename column in the df
        df = pd.DataFrame(dct_df)
        df[newname] = np.nan
        # append the marker name in the dct_markers
        dct_markers.append(newname)
        # turn df into dict again
        dct_df = df.to_dict("records")
    return valid, dct_df, dct_markers

def saveas_standard_csv_in_data_dir(dct_df,dir_data, filename, columnsalways, columnsmarkers, kolomvolgorde):
    prefix = standardfile_prefix() # std_
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath,str_c_exclude = standard_column_names()
    lst_filename = os.path.splitext(filename)[0].rsplit("_")
    # if the current filename has already a prefix, then remove the prefix before saving
    if len(lst_filename) == 2:
        if lst_filename[0]==prefix[0:3]:
            filename = filename
        else:
            filename = prefix + lst_filename[0] + '.txt'
    df = pd.DataFrame(dct_df)
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='%Y-%m-%d %H:%M:%S')
    # dictionaries 'forget' the column order, apply a list with certain order before saving
    lst = columnsalways + columnsmarkers
    for k in kolomvolgorde:
        if k not in lst:
            lst.append(k)
    df = df[lst]
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
            dataframe with time series
            column of which percentiles are calculated
            lst_Ln: list of percentiles to be calculated
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

def correspondingspectrumfilepath(bbfile, dir_data):
    """ defines the standard name of the spectrumfile based on the broadband file
    :param  the name of the broadband file,
    :return:the name of the spectrumfilepath
    """

    spectrumfilepath = os.path.basename(bbfile)
    spectrumfilepath = spectrumfilepath.split(".")[0]
    spectrumfilepath = spectrumfilepath.split("_")[0]
    spectrumfilepath = spectrumfilepath + "_LoggedSpectra.txt"
    spectrumfilepath = os.path.join(dir_data,spectrumfilepath)
    return spectrumfilepath

def standardize_spectrumdata(df):
    """change the columnames in dataframe to a standard choice"""
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    lst_spctr_spellings = lst_spectra_spellings()                 # list of spectra-spellings eg. 50Hz = 50 hz = 50 Hz
    lst_stndrd_spectrcols= lst_standard_spectrumcolumn_names()  # list of the spectrum-spelling that i choose
    # loop through columns of df (spectrum data)
    for c in df.columns.tolist():
        # rename column time in standard columname
        if c in ['Start Time', 'starttime', 'Start time', 'start Time']:
            df.rename(columns={c: str_c_time}, inplace=True)
        # rename frequencies in standard columname
        for lst_sp in lst_spctr_spellings:
            if c in lst_sp:
                freqindx = (lst_sp.index(c)) # get index of columname that is found
                # rename with corresponding index from the standard column-names
                df.rename(columns={c: lst_stndrd_spectrcols[freqindx]}, inplace=True)
    lst_cols_keep = [str_c_time]
    lst_cols_keep.extend(lst_stndrd_spectrcols)
    return df[lst_cols_keep]
def lst_spectra_spellings():
    """Even when the same brand of sound level meter is used, the column-names for terts-band frequencies
    that it spits out can differ.
    Here is a list of all the spellings that i found
    I am not interested in lower than 25 Hz and higher than 20 kHz"""
    lst = ['LZeq25Hz', 'LZeq31.5Hz', 'LZeq40Hz', 'LZeq50Hz', 'LZeq63Hz', 'LZeq80Hz', 'LZeq100Hz',
                 'LZeq125Hz', 'LZeq160Hz', 'LZeq200Hz', 'LZeq250Hz', 'LZeq315Hz', 'LZeq400Hz', 'LZeq500Hz',
                 'LZeq630Hz', 'LZeq800Hz', 'LZeq1kHz', 'LZeq1.25kHz', 'LZeq1.6kHz', 'LZeq2kHz', 'LZeq2.5kHz',
                 'LZeq3.15kHz', 'LZeq4kHz', 'LZeq5kHz', 'LZeq6.3kHz', 'LZeq8kHz', 'LZeq10kHz', 'LZeq12.5kHz',
                 'LZeq16kHz', 'LZeq20kHz'],\
          ['LZeq25Hz', 'LZeq31.5Hz', 'LZeq40Hz', 'LZeq50Hz', 'LZeq63Hz', 'LZeq80Hz', 'LZeq100Hz',
                 'LZeq125Hz', 'LZeq160Hz', 'LZeq200Hz', 'LZeq250Hz', 'LZeq315Hz', 'LZeq400Hz', 'LZeq500Hz',
                 'LZeq630Hz', 'LZeq800Hz', 'LZeq1000Hz', 'LZeq1250Hz', 'LZeq1600Hz', 'LZeq2000Hz', 'LZeq2500Hz',
                 'LZeq3150Hz', 'LZeq4000Hz', 'LZeq5000Hz', 'LZeq6300Hz', 'LZeq8000Hz', 'LZeq10000Hz', 'LZeq12500Hz',
                 'LZeq16000Hz', 'LZeq20000Hz'],\
          ['LZeq 25Hz', 'LZeq 31.5Hz', 'LZeq 40Hz', 'LZeq 50Hz', 'LZeq 63Hz', 'LZeq 80Hz', 'LZeq 100Hz',
                 'LZeq 125Hz', 'LZeq 160Hz', 'LZeq 200Hz', 'LZeq 250Hz', 'LZeq 315Hz', 'LZeq 400Hz', 'LZeq 500Hz',
                 'LZeq 630Hz', 'LZeq 800Hz', 'LZeq 1kHz', 'LZeq 1.25kHz', 'LZeq 1.6kHz', 'LZeq 2kHz', 'LZeq 2.5kHz',
                 'LZeq 3.15kHz', 'LZeq 4kHz', 'LZeq 5kHz', 'LZeq 6.3kHz', 'LZeq 8kHz', 'LZeq 10kHz', 'LZeq 12.5kHz',
                 'LZeq 16kHz', 'LZeq 20kHz'],\
          ['lzeq25hz', 'lzeq31.5hz', 'lzeq40hz', 'lzeq50hz', 'lzeq63hz', 'lzeq80hz', 'lzeq100hz',
                 'lzeq125hz', 'lzeq160hz', 'lzeq200hz', 'lzeq250hz', 'lzeq315hz', 'lzeq400hz', 'lzeq500hz',
                 'lzeq630hz', 'lzeq800hz', 'lzeq1khz', 'lzeq1.25khz', 'lzeq1.6khz', 'lzeq2khz', 'lzeq2.5khz',
                 'lzeq3.15khz', 'lzeq4khz', 'lzeq5khz', 'lzeq6.3khz', 'lzeq8khz', 'lzeq10khz', 'lzeq12.5khz',
                 'lzeq16khz', 'lzeq20khz'], \
          ['lzeq25', 'lzeq31.5', 'lzeq40', 'lzeq50', 'lzeq63', 'lzeq80', 'lzeq100',
           'lzeq125', 'lzeq160', 'lzeq200', 'lzeq250', 'lzeq315', 'lzeq400', 'lzeq500',
           'lzeq630', 'lzeq800', 'lzeq1000', 'lzeq1250', 'lzeq1600', 'lzeq2000', 'lzeq2500',
           'lzeq3150', 'lzeq4000', 'lzeq5000', 'lzeq6300', 'lzeq8000', 'lzeq10000', 'lzeq12500',
           'lzeq16000', 'lzeq20000'], \
          ['25', '31.5', '40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500',
           '630', '800', '1000', '1250', '1600', '2000', '2500', '3150', '4000', '5000', '6300', '8000', '10000', '12500',
           '16000', '20000'], \
          ['25', '31.5', '40', '50', '63', '80', '100', '125', '160', '200', '250', '315', '400', '500',
           '630', '800', '1k', '1.25k', '1.6k', '2k', '2.5k', '3.15k', '4k', '5k', '6.3k', '8k', '10k',
           '12.5k','16k', '20k'], \
          [25, 31.5, 40, 50, 63, 80, 100, 125, 160, 200, 250, 315, 400, 500,
           630, 800, 1000, 1250, 1600, 2000, 2500,3150, 4000,5000, 6300, 8000, 10000, 12500,
           16000, 20000]
    return lst

def lst_tertsbandweging(strtype):
    # 30 in total, start: 25Hz end: 20000Hz
    lst=[]
    if strtype == 'Z':
        lst = [0, ] * 30
    if strtype == 'A':
        lst = [-44.7, -39.5, -34.5, -30.3, -26.2, -22.4,
                  -19.1, -16.2, -13.2, -10.8, -8.7,
                  -6.6, -4.8, -3.2, -1.9, -0.8,
                  0, 0.6, 1, 1.2, 1.3,
                  1.2, 1, 0.5, -0.1, -1.1,
                  -2.5, -4.3, -6.7, -9.3]
    if strtype == 'C':
        print("to be added later")
    return lst

def lst_standard_spectrumcolumn_names():
    """Even when the same brand of sound level meter is used, the columnnames can differ.
    From the list of spellings, list number 6 is chosen as standard:
    no spaces, no capitals, no special charachters, so no troubles"""
    choice = 3
    lst = lst_spectra_spellings()[choice]
    return lst

def dataprep_laeq(dct_df, m):
    """calculate laeq of spectrum
    :param
        dataframe of the time series, containing spectrum columns
    :returns
        dataframe with spectrum"""
    # calculate the laeq of the broadband parameter
    # (for debugging purposes: this should be equal to calculated laeq of all the tertsbands
    # laeqbroadband = logmean_of_column(df,str_c_laeq1s)
    # calculate logmean for each tertsband-column and put in a list
    df = pd.DataFrame(dct_df)
    # apply marker selection
    df = df.loc[df[m] == 1 & (df['exclude'].isnull())]
    lst_spec_cols = lst_standard_spectrumcolumn_names()
    lst_logmean=[]
    for sp in lst_spec_cols:
        lst_logmean.append((logmean_of_column(df,sp)))
    # list of a-weightings
    lst_aweight = lst_tertsbandweging('A')
    # make a spectrum data dictionary and create a dataframe
    dct_spec_data = {'hz': lst_spec_cols, 'lzeq_t': lst_logmean, 'aweight': lst_aweight }
    df_spectrum = pd.DataFrame(data = dct_spec_data)
    # calculate the laeq-value of all the tertsbands, this should be equal to laeqbroadband
    df_spectrum['laeq_t']= df_spectrum['lzeq_t']+df_spectrum['aweight']
    laeqfromspec = round(10 * np.log10((10 ** ((df_spectrum['laeq_t']) / 10)).sum()),1)
    # add laeq from spectrum to spectrum dataframe by making a tmp mini dataframe
    df_tmp = {'hz': 'LAeq', 'lzeq_t':laeqfromspec}
    df_spectrum = df_spectrum.append(df_tmp, ignore_index = True)
    return df_spectrum

def dataprep_la95(dct_df, m):
    """calculate statistical parameter la95 of spectrum
    :param
        dataframe of the time series, containing spectrum columns
    :returns
        dataframe with spectrum"""
    df = pd.DataFrame(dct_df)
    # apply marker selection
    df = df.loc[df[m] == 1 & (df['exclude'].isnull())]
    la95broadband = round(np.percentile(df['laeq1s'], 5), 1)
    lst_spec_cols = lst_standard_spectrumcolumn_names()
    lst_l95=[]
    for sp in lst_spec_cols:
        lst_l95.append((round(np.percentile(df[sp], 5),1)))

    # list of a-weightings
    lst_aweight = lst_tertsbandweging('A')
    # make a spectrum data dictionary and create a dataframe
    dct_spec_data = {'hz': lst_spec_cols, 'lz95_t': lst_l95, 'aweight': lst_aweight }
    df_spectrum = pd.DataFrame(data = dct_spec_data)
    # calculate the la95-value of all the tertsbands, this should be equal to la95broadband
    # but unfortunately it is NOT
    df_spectrum['la95_t']= df_spectrum['lz95_t']+df_spectrum['aweight']
    la95fromspec = round(10 * np.log10((10 ** ((df_spectrum['la95_t']) / 10)).sum()),1)
    difference = la95broadband - la95fromspec
    #print ('difference broadband and spectrum l95:', round(difference,1))
    # do something with that difference
    # --> this is rubbish but i 'm doing it anyway
    df_spectrum['la95_t'] = df_spectrum['la95_t']+difference
    la95fromspec = round(10 * np.log10((10 ** ((df_spectrum['la95_t']) / 10)).sum()), 1)
    # add la95 from spectrum to spectrum dataframe by making a tmp mini dataframe with one record
    df_tmp = {'hz': 'LA95', 'lz95_t':la95fromspec}
    df_spectrum = df_spectrum.append(df_tmp, ignore_index = True)
    return df_spectrum
# # Ln =
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
