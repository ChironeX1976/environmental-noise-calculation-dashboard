import os
import numpy as np
import pandas as pd
from definitions import standard_column_names, standardfile_prefix, lst_standard_spectrumcolumn_names, \
    lst_standard_statscolumn_names
import io
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
def data_prep(slmtype:str, decoded:str, filename:str, dir_audio:str):
    #if slmtype == "Bruel and Kjaer-2250":
    #    lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo = b_en_k_dataprep(decoded, filename)
    if slmtype == "standard pcm file":
        lst_flds_a, lst_flds_st, lst_flds_m_used, begintime, df, lstsound, spectralinfo = standard_dataprep(decoded, filename, dir_audio)
    else:
        print(slmtype, ", not programmed yet")
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
    lst_standardstats = lst_standard_statscolumn_names()
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
    lst_standardspecs = lst_standard_spectrumcolumn_names()
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
def col_lst_always(str_c_time, str_c_laeq1s):
    """Put the columnames that are always interesting into list"""
    lst = [str_c_time, str_c_laeq1s]
    return lst

def lst_to_dict(lst):
    """turn list into a dictionary, label and value are the same
    for dcc components
    eg: list [l1,l2,l3...]
        {'label': 'l1', 'value': 'l1'},
        {'label': 'l2', 'value': 'l2'}]"""
    res_dct = {lst[i]: lst[i] for i in range(0, len(lst))}
    return res_dct

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
    df = pd.DataFrame(dct_df)
    df[str_c_time] = pd.to_datetime(df[str_c_time], format='ISO8601')
    # dictionaries 'forget' the column order, apply a list with certain order before saving
    lst = columnsalways + columnsmarkers
    for k in kolomvolgorde:
        if k not in lst:
            lst.append(k)
    df = df[lst]
    df.to_csv(filename, sep="\t", index=False)
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
