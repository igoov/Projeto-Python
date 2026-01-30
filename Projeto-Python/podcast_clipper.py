import google.generativeai as genai
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import cv2
import numpy as np
import os
import time
import json
import argparse
import whisper
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
# Substitua pela sua chave real do Google AI Studio
genai.configure(api_key="AIzaSyClzaj37XPckPwTYfHEG-rNJRjN-3clsHI")

class VideoClipper:
    def __init__(self):
        # Carrega o detector de rostos do OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def processar_com_ia(self, lista_palavras):
        """Traduz do inglês ou revisa o português usando Gemini."""
        if not lista_palavras:
            return [], "MOMENTO ÉPICO! 🔥", "#podcast"
            
        texto_unido = " ".join(lista_palavras)
        
        prompt = f"""
        Atue como um editor de vídeos viral. 
        TAREFA:
        1. Se o texto estiver em Inglês, TRADUZA para Português Brasileiro natural.
        2. Se estiver em Português, revise a gramática.
        3. Mantenha a ordem exata das palavras.
        4. Gere um TÍTULO CLICKBAIT e 6 HASHTAGS.
        
        Texto: {texto_unido}
        
        Responda APENAS o JSON:
        {{
            "conteudo": ["palavra1", "palavra2", ...],
            "titulo": "Seu Titulo Viral",
            "tags": "#tag1 #tag2"
        }}
        """
        try:
            time.sleep(6)  # Blindagem API Free
            response = self.model.generate_content(prompt)
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)
            return data.get("conteudo", []), data.get("titulo", "MOMENTO ÉPICO! 🔥"), data.get("tags", "#viral")
        except Exception as e:
            print(f"⚠️ Erro na IA: {e}")
            return lista_palavras, "CONFIRA ISSO! 🔥", "#podcast #cortes"

    def get_active_face_x(self, frame):
        """Detecção de rosto para centralizar o corte vertical (9:16)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        # Filtra detecções muito baixas (mesa)
        valid_faces = [x + w/2 for (x, y, w, h) in faces if y < (frame.shape[0] * 0.45)]
        return valid_faces[0] if valid_faces else None

    def create_subtitle(self, word, start, duration):
        """Cria legendas amarelas que quebram linha (evita cortes)."""
        return TextClip(
            text=word.upper(), 
            font_size=70, 
            color='yellow', 
            stroke_color='black', 
            stroke_width=2, 
            method='caption', # Garante que o texto não saia da tela
            size=(850, None), 
            text_align='center',
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        ).with_position(('center', 1400)).with_start(start).with_duration(duration)

    def create_all_clips(self, video_path, transcription, moments, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        video = VideoFileClip(video_path)
        
        for i, m in enumerate(moments, 1):
            is_longo = (i % 4 == 0) 
            duracao_alvo = 65 if is_longo else 40
            pasta_nome = f"corte_{i:02d}_{'LONGO' if is_longo else 'CURTO'}"
            pasta_corte = os.path.join(output_dir, pasta_nome)
            os.makedirs(pasta_corte, exist_ok=True)
            
            print(f"\n🎬 PROCESSANDO CORTE {i}/{len(moments)}")
            
            start_t = max(0, m['timestamp'] - 2)
            end_t = min(start_t + duracao_alvo, video.duration)
            sub = video.subclipped(start_t, end_t)
            
            # --- CÂMERA DINÂMICA ---
            segments = []
            last_x = sub.w / 2
            for t in np.arange(0, sub.duration, 1.0):
                frame = sub.get_frame(t)
                new_x = self.get_active_face_x(frame)
                if new_x: last_x = new_x
                
                target_w = int(sub.h * (9/16))
                x1 = int(max(0, min(last_x - target_w/2, sub.w - target_w)))
                seg = sub.subclipped(t, min(t + 1.0, sub.duration)).cropped(x1=x1, x2=x1+target_w, y1=0, y2=sub.h)
                segments.append(seg.resized(width=1080, height=1920))

            sub_v = concatenate_videoclips(segments)
            
            # --- IA E TRADUÇÃO ---
            palavras_trecho = []
            for segment in transcription['segments']:
                for w_data in segment.get('words', []):
                    if w_data['start'] >= start_t and w_data['end'] <= end_t:
                        palavras_trecho.append(w_data)

            lista_txt = [w['word'].strip() for w in palavras_trecho]
            texto_br, titulo_ia, tags_ia = self.processar_com_ia(lista_txt)
            
            if len(texto_br) != len(palavras_trecho): texto_br = lista_txt

            subs_clips = [self.create_subtitle(texto_br[idx], w['start']-start_t, w['end']-w['start']) 
                          for idx, w in enumerate(palavras_trecho) if (w['end']-w['start']) > 0]
            
            # --- RENDERIZAÇÃO ---
            final = CompositeVideoClip([sub_v] + subs_clips)
            final.write_videofile(os.path.join(pasta_corte, f"video_{i:02d}.mp4"), codec='libx264', audio_codec='aac', threads=4)
            
            with open(os.path.join(pasta_corte, "postagem.txt"), "w") as f:
                f.write(f"TITULO: {titulo_ia}\nTAGS: {tags_ia}")

        video.close()

# --- BLOCO PRINCIPAL (ENTRY POINT) ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Caminho do vídeo")
    parser.add_argument("--max", type=int, default=11)
    parser.add_argument("--model", default="small")
    args = parser.parse_args()

    if os.path.exists(args.video):
        print(f"🚀 Iniciando Processamento de 15 min: {args.video}")
        clipper = VideoClipper()
        
        print(f"🎙️ Carregando Whisper... (Modo Verbose Ativado)")
        model = whisper.load_model(args.model)
        # O verbose=True faz você ver o texto aparecendo no terminal!
        result = model.transcribe(args.video, word_timestamps=True, verbose=True)
        
        v_meta = VideoFileClip(args.video)
        total = v_meta.duration
        v_meta.close()
        
        intervalo = total / (args.max + 1)
        pontos = [{"timestamp": i * intervalo} for i in range(1, args.max + 1)]
        
        clipper.create_all_clips(args.video, result, pontos, "output")
        print("\n✅ TUDO PRONTO!")