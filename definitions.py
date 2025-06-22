import os
from pathlib import Path
import platform
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
    lst_c_percentiles= [lst_standard_statscolumn_names(), lst_standard_statscolumn_values()]
    lst_c_summary = ['marker', 'laeq']              #used in the tab statistics
    lst_c_summary.extend(lst_standard_statscolumn_alias())      #used in the tab statistics
    return str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath,str_c_exclude
def standardfile_prefix():
    prefix = "std_"
    return prefix
def get_std_audio_path():
    system = platform.system()
    if system == "Windows":
        return Path("C:/py/audio/01db")
    else:
        # Op Linux/macOS wordt de map in de thuismap gezet
        return Path.home() / "audio/"
def get_std_file_path():
    system = platform.system()
    if system == "Windows":
        return Path("C:/tmp/file.txt")
    else:
        # Op Linux/macOS wordt de map in de thuismap gezet
        return Path.home() / "tmp/file.txt"
def lst_standard_spectrumcolumn_names():
    lst=['lzeq25hz', 'lzeq31.5hz', 'lzeq40hz', 'lzeq50hz', 'lzeq63hz', 'lzeq80hz', 'lzeq100hz',
                 'lzeq125hz', 'lzeq160hz', 'lzeq200hz', 'lzeq250hz', 'lzeq315hz', 'lzeq400hz', 'lzeq500hz',
                 'lzeq630hz', 'lzeq800hz', 'lzeq1khz', 'lzeq1.25khz', 'lzeq1.6khz', 'lzeq2khz', 'lzeq2.5khz',
                 'lzeq3.15khz', 'lzeq4khz', 'lzeq5khz', 'lzeq6.3khz', 'lzeq8khz', 'lzeq10khz', 'lzeq12.5khz',
                 'lzeq16khz', 'lzeq20khz']
    return lst
def lst_standard_spectrumcolumn_labels():
    lst=['25', '31.5', '40', '50', '63', '80', '100',
                 '125', '160', '200', '250', '315', '400', '500',
                 '630', '800', '1k', '1.25k', '1.6k', '2k', '2.5k',
                 '3.15k', '4k', '5k', '6.3k', '8k', '10k', '12.5k',
                 '16k', '20k']
    return lst
def lst_standard_statscolumn_names():
    """Put statistical fields, that are always interesting, into list"""
    lst = ["laf1", "laf5", "laf10", "laf50", "laf90", "laf95", "laf99"]
    return lst
def lst_standard_statscolumn_values():
    lst =[1,5,10,50,90,95,99]
    return lst
def lst_standard_statscolumn_alias():
    lst =["la1", "la5", "la10", "la50", "la90", "la95", "la99"]
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
