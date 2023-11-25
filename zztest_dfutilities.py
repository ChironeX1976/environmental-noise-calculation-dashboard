import pandas as pd
import numpy as np
# def minidataset():
#     # define mini-dataset as an example
#     data = {'time': ['2020-01-01 12:00:00', '2020-01-01 12:00:01', '2020-01-01 12:00:02', '2020-01-01 12:00:03',
#                      '2020-01-01 12:00:04', '2020-01-01 12:00:05', '2020-01-01 12:00:06', '2020-01-01 12:00:07',
#                      '2020-01-01 12:00:08', '2020-01-01 12:00:09', '2020-01-01 12:00:10'],
#             'muziek': [1, np.nan, np.nan, 1, 1, np.nan, np.nan, 1, 1, 1, np.nan],
#             'exclude': [1, 1, 1, 1, 1, np.nan, 1, 1, 1, 1, np.nan]}
#     df = pd.DataFrame(data)
#     df['time'] = pd.to_datetime((df['time']))
#     return df
# def create_standarddf_of_events_all(df,events, strtime):
#     """
#     create a dataframe of ALL acoustic events in a time series of sound pressure levels
#     :param:
#         df dataframe with a time series, decibelvalues and one or more event columns
#         events: list of columnames (strings) with the eventnames
#         strtime: columnname (string) with the time notation
#         """
#     dflist=[]
#     for nr, e in enumerate(events):
#         # Create a grouper to mark the intervals of successive events
#         # -------------------------------------------------------------
#         # interval = no marker (gaps between the markers)
#         interval = df[e].isna()
#         # cumulatieve sum of intervals creates an increasing number that stays constant at each marker
#         # (the number is only incremented if an interval is reached)
#         interval_cumsum = interval.cumsum()
#         # mask those increasing numbers in case of overlap with the gaps (interval) and fill forward 1 NaN value
#         markergrouper = interval_cumsum.mask(interval).ffill(limit=1)
#         # group the time column by the grouper and agregate with first and last
#         df1 = df[strtime].groupby(markergrouper).agg(['first', 'last']).reset_index(drop=True)
#         # Create event id column with helper columns and drop helper columns again
#         df1['e'] = e
#         df1['i'] = df1.index+1
#         df1['i'] = df1['i'].astype(str)
#         df1['e_id'] = df1['e'] + df1['i']
#         df1.drop(columns=['e', 'i'], inplace=True)
#         # kolommen verwisselen van plaats
#         cols = list(df1.columns)
#         a, b, c = cols.index('first'), cols.index('last'), cols.index('e_id')
#         cols[a], cols[b], cols[c] = cols[c], cols[a], cols[b]
#         df1 = df1[cols]
#         # kolommen toevoegen en direct herindexeren
#         df1 = df1.reindex(columns=df1.columns.tolist() + ['L99', 'L95', 'L90', 'L50', 'L10', 'L05', 'L01'])
#         dflist.append(df1)
#     dftot = pd.concat(dflist,axis=0)
#     return dftot



# print(create_standarddf_of_event(minidataset(),['muziek','exclude'],'time'))
