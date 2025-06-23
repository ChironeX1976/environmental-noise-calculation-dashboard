from dash import html, Input, Output, Dash
import base64
from pydub import AudioSegment
import io
app = Dash(__name__)

# Normalize the audio
def normalize_base64_mp3(data_uri):
    # Extract base64 part
    base64_audio = data_uri.split(',')[1]

    # Decode base64 to bytes
    audio_bytes = base64.b64decode(base64_audio)

    # Load audio from bytes
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

    # Normalize to -20 dBFS
    normalized_audio = audio.apply_gain(-audio.max_dBFS - 1.0)

    # Export to bytes
    buffer = io.BytesIO()
    normalized_audio.export(buffer, format="wav")
    normalized_bytes = buffer.getvalue()

    # Encode back to base64
    normalized_base64 = base64.b64encode(normalized_bytes).decode()

    # Return new data URI
    return f"data:audio/mpeg;base64,{normalized_base64}"
def onveranderdefile(data_uri):
    return 'data:audio/mpeg;base64,{}'.format(encoded_sound.decode())
# ONVERANDERDE FILE
# # Encode the local sound file.
# sound_filename = 'SR0.wav'  # replace with your own .mp3 file
# encoded_sound = base64.b64encode(open(sound_filename, 'rb').read())
# s = 'data:audio/mpeg;base64,{}'.format(encoded_sound.decode())

# LUIDERE FILE
# Original base64-encoded MP3 string
sound_filename = 'SR0.wav'  # replace with your own .mp3 file

encoded_sound = base64.b64encode(open(sound_filename, "rb").read())
s = 'data:audio/mpeg;base64,{}'.format(encoded_sound.decode())
#Apply normalization
s = normalize_base64_mp3(s)


app.layout = html.Div(children=[
    html.H1(children='Demo for Audio with Dash'),

    html.Div(children='''
        Click the button to play your local .mp3 sounds.
    '''),


    html.Button(id="button1", children="Click me for sound"),
    html.Audio(id='audio-player', src= s ,
                          controls=True,
                          autoPlay=False,
                          ),
    html.Div(id="placeholder", style={"display": "none"})])

# app.clientside_callback(
#     """
#     function(n) {
#       var audio = document.querySelector('#audio-player');
#       if (!audio){
#         return -1;
#       }
#       audio.play();
#       return '';
#    }
#     """, Output('placeholder', 'children'), [Input('button1', 'n_clicks')],
#     prevent_initial_call=True
# )


if __name__ == '__main__':
    app.run(debug=True)
