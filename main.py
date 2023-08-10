from pytube import YouTube
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

# URL do vídeo do YouTube
video_url = 'https://www.youtube.com/watch?v=6veQB79A0T8'

# Tempo de início e fim para cortar (em segundos)
start_time = 120
end_time = 180

# Baixar o vídeo do YouTube
yt = YouTube(video_url)
stream = yt.streams.get_highest_resolution()
video_path = stream.download()

# Nome do arquivo de saída
output_file = 'cortado.mp4'

# Usar o MoviePy para cortar o vídeo
video = VideoFileClip(video_path)
subclip = video.subclip(start_time, end_time)
subclip.write_videofile(output_file, codec='libx264')

# Excluir o vídeo original baixado
video.close()
subclip.reader.close()
del video
del subclip