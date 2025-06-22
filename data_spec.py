import numpy as np
import pandas as pd
from data import logmean_of_column, lst_tertsbandweging
from definitions import standard_column_names, lst_standard_spectrumcolumn_names
def data_spec_leq_or_ln(dct_df, m, parameter):
    """calculate spectrum in leq or statistical ln
    :param
        dataframe of the time series, containing spectrum columns
    :returns
        dataframe with spectrum"""
    str_c_laeq1s, str_c_time, lst_c_percentiles, lst_c_summary, str_c_soundpath, str_c_exclude = standard_column_names()
    lst_spec_cols = lst_standard_spectrumcolumn_names()
    df = pd.DataFrame(dct_df)
    # apply marker selection
    df = df.loc[df[m] == 1 & (df[str_c_exclude].isnull())]
    # iterate through spectrum-columns and summarize
    lst_specval = []
    if parameter == "Leq":
        for sp in lst_spec_cols:
            lst_specval.append((logmean_of_column(df,sp)))
    else:
        for sp in lst_spec_cols:
            lst_specval.append((round(np.percentile(df[sp], 5),1)))

    # list of a-weightings
    lst_aweight = lst_tertsbandweging('A')

    # make a spectrum data dictionary and create a dataframe
    dct_spec_data = {'hz': lst_spec_cols, 'zlevel_t': lst_specval, 'aweight': lst_aweight }
    df_spectrum = pd.DataFrame(data = dct_spec_data)
    df_spectrum['alevel_t']= df_spectrum['zlevel_t']+df_spectrum['aweight']
    # calculate the corresponding broadband parameter of Leq or Ln
    # (for debugging purposes: this broadband should  be equal to calculated broadband of all the tertsbands
    if parameter == "Leq":
        broadband = logmean_of_column(df,str_c_laeq1s)
        broadbandfromspec = round(10 * np.log10((10 ** ((df_spectrum['alevel_t']) / 10)).sum()),1)
    else:
        broadband = round(np.percentile(df[str_c_laeq1s], 5), 1)
        broadbandfromspec = round(10 * np.log10((10 ** ((df_spectrum['alevel_t']) / 10)).sum()), 1)

    print("broadband - broadbandfromspec:", round(broadband - broadbandfromspec,1))
    # add broadband tot spec making a tmp mini dataframe
    dct_tmp = {'hz': 'tot_A', 'zlevel_t':broadband, 'aweight':0, 'laeq_t':0}
    df_tmp = pd.DataFrame([dct_tmp])
    df_spectrum = pd.concat([df_spectrum, df_tmp], ignore_index=True)
    return df_spectrum

# def data_spec_ln(dct_df, m):
#     """calculate statistical parameter la95 of spectrum
#     :param
#         dataframe of the time series, containing spectrum columns
#     :returns
#         dataframe with spectrum"""
#     df = pd.DataFrame(dct_df)
#     # apply marker selection
#     df = df.loc[df[m] == 1 & (df['exclude'].isnull())]
#     la95broadband = round(np.percentile(df['laeq1s'], 5), 1)
#     lst_spec_cols = lst_standard_spectrumcolumn_names()
#     lst_l95=[]
#     for sp in lst_spec_cols:
#         lst_l95.append((round(np.percentile(df[sp], 5),1)))
#
#     # list of a-weightings
#     lst_aweight = lst_tertsbandweging('A')
#     # make a spectrum data dictionary and create a dataframe
#     dct_spec_data = {'hz': lst_spec_cols, 'lz95_t': lst_l95, 'aweight': lst_aweight }
#     df_spectrum = pd.DataFrame(data = dct_spec_data)
#     # calculate the la95-value of all the tertsbands, this should be equal to la95broadband
#     # but unfortunately it is NOT
#     df_spectrum['la95_t']= df_spectrum['lz95_t']+df_spectrum['aweight']
#     la95fromspec = round(10 * np.log10((10 ** ((df_spectrum['la95_t']) / 10)).sum()),1)
#     difference = la95broadband - la95fromspec
#     #print ('difference broadband and spectrum l95:', round(difference,1))
#     # do something with that difference
#     # --> this is rubbish but i 'm doing it anyway
#     df_spectrum['la95_t'] = df_spectrum['la95_t']+difference
#     la95fromspec = round(10 * np.log10((10 ** ((df_spectrum['la95_t']) / 10)).sum()), 1)
#     # add la95 from spectrum to spectrum dataframe by making a tmp mini dataframe with one record
#     df_tmp = {'hz': 'LA95', 'lz95_t':la95fromspec}
#     df_spectrum = df_spectrum.append(df_tmp, ignore_index = True)
#     return df_spectrum