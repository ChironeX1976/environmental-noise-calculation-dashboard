import os
from pathlib import Path
import platform
def folder_and_file_paths(f):
    """returns standard filepaths based on a selected file
    :param
        f: source data in a txt file with at least a timestamp, dbA, and markers"""
    sep = "_"
    dir_root, dir_data = project_folder_and_path()         # data folder & project root
    filepath = os.path.join(dir_data, f)                   # complete path of the source data
    fileid = os.path.basename(f).split(sep)[0]              # file id of the source data
    dir_audio = os.path.join(dir_data, fileid + " Annotations") # audio folder at Bruel&Kjaer is named after file id and 'annotations'
    return dir_root, dir_data, dir_audio, filepath
def project_folder_and_path():
    dir_root = os.path.dirname(os.path.abspath(__file__))  # Project Root
    dir_data = os.path.join(dir_root, "data")  # data folder in de project root
    return dir_root, dir_data
def standard_column_names():
    """returns standard column names"""
    str_c_laeq1s ="laeq1s" #column name with laeq1s
    str_c_time = "isodatetime" # column name with time stamp
    str_c_soundpath = "soundpath"
    str_c_exclude = "exclude"
    lst_c_percentiles = [["LA1", "LA5", "LA10", "LA50", "LA90", "LA95", "LA99"],[1, 5, 10, 50, 90, 95, 99]]
    lst_c_summary = ['marker', 'laeq']              #used in the tab statistics
    lst_c_summary.extend(lst_c_percentiles[0])      #used in the tab statistics
    return str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath,str_c_exclude
def lstlaeqspellings():
    lst = ['LAeq', 'lAeq', 'LAEQ1S', 'LAeq1s', 'laeq1s']
    return lst
def standardize(df, str_c_soundpath, str_c_exclude, str_c_time,str_c_laeq1s):
    """Although the same instrument, sometimes different column names are used in exportdata from the device.
    Here, standards are introduced as the file is read.
    :parameter
        df: dataframe
        str_c_soundpath: string in which the sound path is stored"""
    for c in df.columns.tolist():
        if c in lstlaeqspellings():
            df.rename(columns={c:str_c_laeq1s}, inplace=True)
        if c in ['Start Time', 'starttime', 'Start time', 'start Time']:
            df.rename(columns={c:str_c_time}, inplace=True)
        if c in ['Sound Path', 'sound Path', 'soundpath', 'SoundPath', 'sound path']:
            df.rename(columns={c:str_c_soundpath}, inplace=True)
        if c in ['Exclude', 'exclude', 'exc']:
            df.rename(columns={c: str_c_exclude}, inplace=True)

    return df #with the standard columnames

def standardfile_prefix():
    prefix = "std_"
    return prefix

def file_is_from_invalid_folder(f, dir_data):
    """ checks if a file is listed in the project data folder.
    If the file is there, it is valid
    :param:
        f: file name without path
        dir_data: folder in which is searched"""
    list_of_files = os.listdir(dir_data)
    invalid = True
    msg = "only files from datafolder are allowed, copy the file to the datafolder"
    if f in list_of_files:
        invalid = False
        msg=""
    return invalid, msg
def get_std_audio_path():
    system = platform.system()
    if system == "Windows":
        return Path("C:/py/audio/01db")
    else:
        # Op Linux/macOS wordt de map in de thuismap gezet
        return Path.home() / "audio/"