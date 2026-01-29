"""
Módulo para corte de vídeos e adição de legendas automáticas
"""
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os
from pathlib import Path

class VideoClipper:
    def __init__(self):
        """
        Inicializa o clipper de vídeos
        """
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_height / self.target_width  # 16:9 vertical
    
    def convert_to_vertical(self, clip):
        """
        Converte vídeo para formato vertical (1080x1920)
        """
        original_width = clip.w
        original_height = clip.h
        original_aspect = original_height / original_width
        
        if original_aspect >= self.target_aspect:
            new_width = original_width
            new_height = int(original_width * self.target_aspect)
            y_center = original_height / 2
            y1 = int(y_center - new_height / 2)
            y2 = int(y_center + new_height / 2)
            clip = clip.cropped(y1=y1, y2=y2, x1=0, x2=original_width)
        else:
            new_height = original_height
            new_width = int(original_height / self.target_aspect)
            x_center = original_width / 2
            x1 = int(x_center - new_width / 2)
            x2 = int(x_center + new_width / 2)
            clip = clip.cropped(x1=x1, x2=x2, y1=0, y2=original_height)
        
        clip = clip.resized((self.target_width, self.target_height))
        return clip
    
    def get_words_for_segment(self, segment, start_time, end_time):
        words = []
        if 'words' in segment:
            for word_info in segment['words']:
                word_start = word_info['start']
                word_end = word_info['end']
                if word_start >= start_time and word_end <= end_time:
                    words.append({
                        'word': word_info['word'],
                        'start': word_start - start_time,
                        'end': word_end - start_time
                    })
        return words
    
    def create_word_subtitle(self, word, start, duration, video_size):
        font_size = 65  
        font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        color = 'yellow'
        stroke_color = 'black'
        stroke_width = 3
        
        txt_clip = TextClip(
            text=word.strip().upper(),
            font=font,
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method='label', # 'label' é mais preciso para palavras únicas
            margin=(20, 20)  # Adiciona respiro para não cortar o stroke
        )
        
        # Garante que não ultrapasse a largura da tela
        if txt_clip.w > (video_size[0] - 100):
            txt_clip = txt_clip.resized(width=video_size[0] - 100)
            
        txt_clip = txt_clip.with_position(('center', video_size[1] * 0.80))
        txt_clip = txt_clip.with_start(start)
        txt_clip = txt_clip.with_duration(duration)
        
        return txt_clip
    
    def create_phrase_subtitle(self, text, start, duration, video_size):
        font_size = 45
        font = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        color = 'white'
        stroke_color = 'black'
        stroke_width = 2
        
        txt_clip = TextClip(
            text=text.strip(),
            font=font,
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=stroke_width,
            method='caption',
            size=(video_size[0] - 200, None),
            text_align='center',
            margin=(15, 15) # Adiciona margem para as frases também
        )
        
        txt_clip = txt_clip.with_position(('center', video_size[1] * 0.85))
        txt_clip = txt_clip.with_start(start)
        txt_clip = txt_clip.with_duration(duration)
        
        return txt_clip
    
    def add_subtitles(self, video_clip, transcription, start_time, end_time, style='word'):
        segments = transcription['segments']
        subtitle_clips = []
        relevant_segments = [seg for seg in segments if seg['start'] < end_time and seg['end'] > start_time]
        
        if style == 'word':
            for segment in relevant_segments:
                words = self.get_words_for_segment(segment, start_time, end_time)
                for word_info in words:
                    duration = word_info['end'] - word_info['start']
                    if duration > 0:
                        txt_clip = self.create_word_subtitle(word_info['word'], word_info['start'], duration, (video_clip.w, video_clip.h))
                        subtitle_clips.append(txt_clip)
        else:
            for segment in relevant_segments:
                seg_start = max(0, segment['start'] - start_time)
                seg_end = min(end_time - start_time, segment['end'] - start_time)
                duration = seg_end - seg_start
                if duration > 0:
                    txt_clip = self.create_phrase_subtitle(segment['text'], seg_start, duration, (video_clip.w, video_clip.h))
                    subtitle_clips.append(txt_clip)
        
        return CompositeVideoClip([video_clip] + subtitle_clips) if subtitle_clips else video_clip
    
    def create_clip(self, video_path, transcription, moment, output_path, subtitle_style='word', add_padding=2.0):
        try:
            print(f"\nCriando clip: {output_path}")
            start_time = max(0, moment['timestamp'] - add_padding)
            video = VideoFileClip(video_path)
            end_time = min(moment['timestamp'] + moment['duration'] + add_padding, video.duration)
            
            print(f"Extraindo subclip ({start_time:.1f}s - {end_time:.1f}s)...")
            clip = video.subclipped(start_time, end_time)
            clip = self.convert_to_vertical(clip)
            
            print(f"Adicionando legendas (estilo: {subtitle_style})...")
            clip = self.add_subtitles(clip, transcription, start_time, end_time, subtitle_style)
            
            print("Exportando vídeo...")
            clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac', 
                temp_audiofile='temp-audio.m4a', 
                remove_temp=True,                
                fps=30, 
                preset='medium', 
                threads=4, 
                logger=None
            )
            
            clip.close()
            video.close()
            return True
        except Exception as e:
            print(f"✗ Erro ao criar clip: {e}")
            return False
    
    def create_all_clips(self, video_path, transcription, moments, output_dir, subtitle_style='word'):
        video_name = Path(video_path).stem
        created_clips = []
        for i, moment in enumerate(moments, 1):
            output_path = os.path.join(output_dir, f"{video_name}_clip_{i:02d}.mp4")
            if self.create_clip(video_path, transcription, moment, output_path, subtitle_style):
                created_clips.append(output_path)
        return created_clips
