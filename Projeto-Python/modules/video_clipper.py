"""
Módulo VideoClipper V6: Foco Inteligente Anti-Mesa e Correção de Tempo
"""
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os
from pathlib import Path
import google.generativeai as genai
import cv2
import numpy as np
from tqdm import tqdm

class VideoClipper:
    def __init__(self, api_key=None):
        self.target_width = 1080
        self.target_height = 1920
        self.target_aspect = self.target_height / self.target_width
        
        # Chave configurada diretamente
        final_key = api_key if api_key else "AIzaSyCqfteZkSbcd6lO_ePiOq5RqXqiYzqzD-A"
        genai.configure(api_key=final_key)
        self.model = genai.GenerativeModel('gemini-pro')
            
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def generate_metadata_with_gemini(self, text):
        if not text or len(str(text).strip()) < 5:
            return "Corte de Podcast", "#viral #clips"
            
        prompt = f"""
        Crie um título viral e 5 hashtags para este clipe de podcast.
        Texto: "{text}"
        Responda apenas:
        Título: [Seu Título]
        Hashtags: [#tag1 #tag2...]
        """
        try:
            response = self.model.generate_content(prompt)
            res = response.text
            title, tags = "Corte de Podcast", "#viral #clips"
            for line in res.split('\n'):
                if "Título:" in line: title = line.split(":", 1)[1].strip()
                if "Hashtags:" in line: tags = line.split(":", 1)[1].strip()
            return title, tags
        except:
            return "Corte de Podcast", "#viral #clips"

    def detect_face_center(self, clip, num_samples=12):
        dur = clip.duration
        sample_times = np.linspace(0, dur, num_samples + 2)[1:-1]
        face_data = []
        for t in sample_times:
            frame = clip.get_frame(t)
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                face_data.append({'x': x + (w / 2), 'area': w * h})
                break 
        if face_data:
            total_area = sum(f['area'] for f in face_data)
            return sum(f['x'] * f['area'] for f in face_data) / total_area
        return None

    def convert_to_vertical(self, clip):
        w, h = clip.w, clip.h
        target_w = int(h / self.target_aspect)
        
        face_x = self.detect_face_center(clip)
        
        if face_x is not None:
            x_center = face_x
        else:
            # LÓGICA ANTI-MESA (FLOW): Se não achar rosto, foca no terço esquerdo (convidado)
            # Em vez de focar no centro (0.5), foca em 0.3 ou 0.7. Vamos usar 0.3 como padrão.
            x_center = w * 0.3 
            
        x1 = int(max(0, min(x_center - target_w / 2, w - target_w)))
        return clip.cropped(x1=x1, x2=x1 + target_w, y1=0, y2=h).resized((1080, 1920))
    
    def create_word_subtitle(self, word, start, duration):
        txt = TextClip(text=word.upper(), font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size=65, color='yellow', stroke_color='black', stroke_width=3, method='label', margin=(20, 20))
        if txt.w > 980: txt = txt.resized(width=980)
        return txt.with_position(('center', 1920 * 0.80)).with_start(start).with_duration(duration)
    
    def add_subtitles(self, video_clip, transcription, start_time, end_time, style='word'):
        segments = transcription.get('segments', [])
        clips = [video_clip]
        relevant = [s for s in segments if s['start'] < end_time and s['end'] > start_time]
        for seg in relevant:
            if style == 'word' and 'words' in seg:
                for w in seg['words']:
                    ws, we = w['start'] - start_time, w['end'] - start_time
                    if ws >= 0 and (we-ws) > 0:
                        clips.append(self.create_word_subtitle(w['word'], ws, we-ws))
        return CompositeVideoClip(clips)
    
    def create_clip(self, video_path, transcription, moment, output_path, subtitle_style='word', add_padding=2.0):
        try:
            video = VideoFileClip(video_path)
            # CORREÇÃO VÍDEO PRETO: Garante que o tempo não ultrapasse o vídeo
            start = max(0, moment['timestamp'] - add_padding)
            end = min(moment['timestamp'] + moment['duration'] + add_padding, video.duration - 0.1)
            
            if start >= end: return False

            clip = video.subclipped(start, end)
            clip = self.convert_to_vertical(clip)
            clip = self.add_subtitles(clip, transcription, start, end, subtitle_style)
            
            clip.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30, logger=None)
            clip.close()
            video.close()
            return True
        except Exception as e:
            print(f"Erro no clip: {e}")
            return False
    
    def create_all_clips(self, video_path, transcription, moments, output_dir, subtitle_style='word'):
        print(f"\nGerando {len(moments)} clips...")
        for i, moment in enumerate(tqdm(moments, desc="Progresso"), 1):
            folder = os.path.join(output_dir, f"video_{i}")
            # CORREÇÃO ERRO DIRETÓRIO: Cria a pasta antes de qualquer coisa
            os.makedirs(folder, exist_ok=True)
            
            out = os.path.join(folder, f"clip_{i:02d}.mp4")
            if self.create_clip(video_path, transcription, moment, out, subtitle_style):
                # Título real baseado no texto do momento
                moment_text = moment.get('text', "")
                title, tags = self.generate_metadata_with_gemini(moment_text)
                
                with open(os.path.join(folder, "info.txt"), "w", encoding="utf-8") as f:
                    f.write(f"Título: {title}\nHashtags: {tags}")
        return True
