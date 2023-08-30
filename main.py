import boto3
from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.editor import TextClip
from moviepy.config import change_settings
import requests
import getpass
import uuid
import time

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

change_settings({"IMAGEMAGICK_BINARY": "/usr/local/bin/convert"})

config_file="/Users/john/.aws/config"
credentials_file="/Users/john/.aws/credentials"

aws_access_key_id="AKIAZBULYIQUKPOLRKES"
aws_secret_access_key="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"
profile_name='default'
region_name='us-east-2'

session = boto3.Session(aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, profile_name=profile_name, region_name=region_name)
s3_client = session.client('s3')

try:
    response = s3_client.list_buckets()
    print('Lista de Buckets')
    print(response['Buckets'])
except Exception as e:
    if "Access Denied" in str(e) and "MultiFactorAuthentication" in str(e):
        mfa_code = getpass.getpass(prompt="Digite o código MFA")
        try:
            response = s3_client.list_buckets(MFA=mfa_code)
            print("Lista de buckets")
            print(response['Buckets'])

        except Exception as e:
            print("Erro ao autenticar com o código MFA", e)
    else:
        print("Erro:", e)

transcribe_client = boto3.client("transcribe", region_name=region_name);

# URL do vídeo do YouTube
video_url = input("Cole a URL do vídeo:")

# Tempo de início e fim para cortar (em segundos)
start_time = int(input("Digite o segundos inicial: "))
end_time = int(input("Digite o segundos final:"))

# Baixar o vídeo do YouTube
yt = YouTube(video_url)
stream = yt.streams.get_highest_resolution()
video_path = stream.download()

s3_video_key = 's3_video_bucket.mp4'

s3_client.upload_file(video_path, 'video-cut', s3_video_key)

s3_video_url = f"https://video-cut.s3.amazonaws.com/{s3_video_key}"

job_name = 'video-transcription' + str(uuid.uuid4())
media_format = 'mp4'
language_code = 'pt-PT'

response = transcribe_client.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': s3_video_url},
    MediaFormat=media_format,
    LanguageCode=language_code,
)

while True:
    response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
    job_status = response['TranscriptionJob']['TranscriptionJobStatus']

    if job_status in ['COMPLETED', 'FAILED']:
        break
    
    time.sleep(5)

response = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
transcription_result_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']


response = requests.get(transcription_result_uri)
transcription_result = response.json()

captions = transcription_result['results']['items']
subtitles = ""

for i, caption in enumerate(captions, start=1):
    if 'alternatives' in caption and caption['alternatives']:
      alternative = caption['alternatives'][0]
      if 'start_time' in alternative and 'end_time' in alternative and 'content' in alternative:
        start_time = float(alternative['start_time'].replace(',', '.'))
        end_time = float(alternative['end_time'].replace(',', '.'))
        content = alternative['content']

        subtitle = (
            f"{i}\n"
            f"{start_time:.3f} --> {end_time:.3f}\n"
            f"{content}\n\n"
        )

        subtitles += subtitle

subtitles_file = 'legendas.srt'
with open(subtitles_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(subtitles))

# Usar o MoviePy para cortar o vídeo
video = VideoFileClip(video_path)
subclip = video.subclip(start_time, end_time)

subtitles = TextClip(subtitles, color="white")
subtitles = subtitles.set_position(("center", "bottom")).set_duration(subclip.duration)
video_with_subtitles = CompositeVideoClip([subclip, subtitles])

output_file = 'video_com_legendas.mp4'
subclip.write_videofile(output_file, codec='libx264', audio_codec='aac')

# Excluir o vídeo original baixado
video.close()
subclip.reader.close()
del video
del subclip