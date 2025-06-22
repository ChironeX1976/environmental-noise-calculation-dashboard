import datetime
import base64
import os

def update_audio_source(value, options, audiofolder):
    """update the data in the audioplayer
        :param
            value: value selected in a dropdownlist, this is a path of the audiofile
            options: label of selected value in the dropdownlist, this is the start time of the audiofile
        :returns
            value: unchanged output for debugging purposes
            o_datetime: start time of the audiofile as an object
            s = raw data of audio, as a string, if no data is found: s is empty """
    # Loop through all options (labels) to get time label of the chosen dropdown-value,
    # this results in ONE value in a LIST lstdatetime.
    # Only one value in a list is weird, just give the value then i would say, but i can't change.
    lstdatetime = [o['label'] for o in options if o['value'] == value]
    # get the first and only item in the list and transform to a uniform datetime
    o_datetime = datetime.datetime.strptime(lstdatetime[0], '%Y-%m-%d %H:%M:%S')  # datetime-string to datetime-object
    # check if the value (path) exists and load in to a string
    value = os.path.join(audiofolder, value)
    if os.path.isfile(value):
        # load the audio data
        data_sound = base64.b64encode(open(value, 'rb').read())
        # make a string s from the audio data
        s = 'data:audio/mpeg;base64,{}'.format(data_sound.decode())
    else:
        s="0" # dummy value
    print(value)
    return value, o_datetime, s
