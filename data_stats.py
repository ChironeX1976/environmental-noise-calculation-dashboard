import pandas as pd

from data import logmean_of_column, Ln_of_column
from definitions import standard_column_names


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
    dfsummary = pd.DataFrame(lst_rslt, columns=lst_c_summary)
    dct_dfsummary = dfsummary.to_dict('records')
    return dct_dfsummary