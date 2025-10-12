import numpy as np
import pandas as pd
from data import logmean_of_column
from definitions import standard_column_names, lst_standard_spectrumcolumn_names, lst_tertsbandweging
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
            # selected parameter ='L1, L5, L10
            # L95 ==> n = 100 - 95 reversed percentiles in acoustics
            n = 100 - (int(parameter[1:]))
            lst_specval.append((round(np.percentile(df[sp], n),1)))
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
        broadband = round(np.percentile(df[str_c_laeq1s], n), 1)
        broadbandfromspec = round(10 * np.log10((10 ** ((df_spectrum['alevel_t']) / 10)).sum()), 1)
    inconsistentie = round(broadband - broadbandfromspec,1)
    print("broadband - broadbandfromspec:", inconsistentie)
    df_spectrum = pas_dataframe_aan(df_spectrum, inconsistentie)
    # add broadband tot spec making a tmp mini dataframe
    dct_tmp = {'hz': 'tot_A', 'zlevel_t':broadband, 'aweight':0, 'laeq_t':0}
    df_tmp = pd.DataFrame([dct_tmp])
    df_spectrum = pd.concat([df_spectrum, df_tmp], ignore_index=True)
    return df_spectrum


def pas_dataframe_aan(df, inconsistentie):
    """
    Past het DataFrame aan door:
    - inconsistentie te verrekenen van elke waarde in 'zlevel_t'
    - 'alevel_t' opnieuw te berekenen als 'zlevel_t' + 'aweight'

    Parameters:
        df (pd.DataFrame): DataFrame met kolommen 'zlevel_t' en 'aweight'

    Returns:
        pd.DataFrame: Aangepast DataFrame
    """
    df = df.copy()  # om het origineel niet te overschrijven
    df['zlevel_t'] = df['zlevel_t'] + inconsistentie
    df['alevel_t'] = df['zlevel_t'] + df['aweight']
    return df