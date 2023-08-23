from pytube import YouTube
from moviepy.editor import *
import soundfile as sf, librosa, requests, json, base64, youtube, glob, os, proglog, spotify, argparse

def _identify_song(fileName, rawFilePath, api_key):
    with open(rawFilePath, 'rb') as binary_file:
        binary_file_data = binary_file.read()
        base64_encoded_data = base64.b64encode(binary_file_data)
        base64_message = base64_encoded_data.decode('utf-8')
    payload = base64_message
    url = "https://shazam.p.rapidapi.com/songs/detect"
    headers = {
        "content-type": "text/plain",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "shazam.p.rapidapi.com"
    }
    response = requests.request("POST", url, data=payload, headers=headers)
    song_result = json.loads(response.text)
    if "track" in song_result:
        if song_result["track"] != []:
            print(f'[*] Found title of: {fileName} -> {song_result["track"]["title"]}')
            return song_result["track"]["title"]
        else:
            return None
    else:
        print(f'[-] No title found for: {fileName}')

def convert_to_wav(file):
        print("\t[->] Converting to wav")
        out = f'{file[:-4]}.wav'
        sound = AudioFileClip(file)
        sound.write_audiofile(out, 44100, 2, 2000,"pcm_s32le", logger=proglog.TqdmProgressBarLogger(print_messages=False))
        os.remove(file)

def _download_vid(video_link, destination, i, total):
    try:
        yt = YouTube(video_link)
        stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
        stream.download(destination)
        print(f'[{i}/{total}] Downloaded: {video_link} -> {stream.default_filename}')
        downloaded_path = f'{destination}{stream.default_filename}'
        convert_to_wav(downloaded_path)   
        return None
    except Exception as e:
        print(f'[X] Download failed: {video_link}')
        return video_link

def download(video_links):
    i=0
    total = len(video_links)
    for videoLink in video_links:
        i+=1
        download = _download_vid(videoLink, download_destination, i, total)
    return None

def locate_song(wavPath, sound, sr, i): 
    wavName = os.path.basename(os.path.normpath(wavPath))
    print(f"wav Name -> {wavName}")
    out_destination = wavPath.replace(f"{wavName}.wav", "")
    frameLength = 2048
    hopLength = 512
    numSecondsOfSlice = 5
    clip_rms = librosa.feature.rms(y=sound, frame_length=frameLength, hop_length=hopLength)
    clip_rms = clip_rms.squeeze()
    peak_rms_index = clip_rms.argmax()
    if peak_rms_index == 0: return None
    peak_index = peak_rms_index * hopLength + int(frameLength/2)
    half_slice_width = int(numSecondsOfSlice * sr / 2)
    left_index = max(0, peak_index - half_slice_width)
    right_index = peak_index + half_slice_width
    sound_slice = sound[left_index:right_index]
    filename = f'Part-{i}_{wavName}'
    print(f"[*] Writing {filename}.raw")
    sf.write(f'{out_destination}{filename}.raw', sound_slice, sr, 'PCM_16')
    sf.write(f'{out_destination}{filename}.wav', sound_slice, sr, 'PCM_24') #WAV Outpui
    return sound[right_index:]

def identify_tracks(wavFilePath):
    sound, sr = librosa.load(wavFilePath, sr=None)
    i=0
    while type(sound) != type(None):
        i+=1
        sound = locate_song(wavFilePath, sound, sr, i)

parser = argparse.ArgumentParser(description='Just a simple program to automate stuff :3')
parser.add_argument('-c', '--channel', help='Target YouTube Channel URL', required=False, type=str)
parser.add_argument('-y', '--youtube-api-key', help='Youtube Api Key', required=False, type=str)
parser.add_argument('-l', '--load-path', help='Load already downloaded wavs', required=False, type=str)
parser.add_argument('-d', '--save-dir', help='Location to write files', required=False, type=str)
parser.add_argument('-sh', '--shazam-api-key', help='Shazam API Key', required=False, type=str)
parser.add_argument('-sp', '--spotify-access-token', help='Spotify Access Token', required=False, type=str)
parser.add_argument('-p', '--spotify-playlist', help='Spotify Playlist Name', required=False, type=str)
args = parser.parse_args()

channel_url = args.channel
download_destination = args.save_dir
shazam_api_key = args.shazam_api_key
spotify_api_key = args.spotify_access_token
spotify_playlist_name = args.spotify_playlist
load_path = args.load_path
youtube_api_key = args.youtube_api_key

if youtube_api_key is None:
    print("[X] YouTube API Key is not set!")
    quit()

if shazam_api_key is None:
    print("[X] Shazam API Key is not set!")
    quit()

if download_destination is not None:
    if not os.path.exists(download_destination): os.makedirs(args.save_dir)

if load_path is None:
    if download_destination is None:
        print("[X] Download path is not set!")
        quit()
    if channel_url is not None and download_destination is not None:
        videoLinks = list(set(youtube.get_links_from_channel(youtube_api_key, channel_url)))
        download(videoLinks)
else:
    print("[*] Skipping download")
    if not os.path.exists(load_path):
        print("[X] Direcotry to load, does not exist!")
        quit()
    download_destination = load_path

wav_files = glob.glob(f'{download_destination}*.wav')
print(f"[*] Loaded {len(wav_files)} wav files.")

if len(wav_files) <= 0: 
    print("[X] No wav files found to be loaded!")
    quit()

print("[*] Finding music parts:")
tracks = []
for wav_file in wav_files:
    identify_tracks(wav_file)
    os.remove(wav_file)

raw_files = glob.glob(f'{download_destination}*.raw')
track_titles = []
for raw_file in raw_files:
    rawFilename = raw_file.split("\\")[-1][:-4]
    track_title = _identify_song(rawFilename, f'{download_destination}{rawFilename}.raw', shazam_api_key)
    if track_title != None:
        track_titles.append(track_title)
    os.remove(f'{download_destination}{rawFilename}.raw')
track_titles = list(dict.fromkeys(track_titles)) #Clear dublicates    

if spotify_api_key is not None and spotify_playlist_name is not None:
    spotify.add_to_spotify_playlist(spotify_api_key, track_titles, spotify_playlist_name)
elif spotify_api_key is None:
    print("[X] Spotify Access Token is not set!")
    quit()
elif spotify_playlist_name is None:
    print("[X] Spotify Playlist Name is not set!")
    quit()
else:
    print("[*] Skipping Addition to Spotify")