import os
import time
import json
import argparse
import cv2
import numpy as np
import whisper
from groq import Groq
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from tqdm import tqdm

# --- CONFIGURAÇÃO ---
# Substitua pela sua chave real do Groq Cloud
GROQ_API_KEY = "."

class VideoClipper:
    def __init__(self):
        # Carrega o detector de rostos do OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Inicializa o cliente Groq
        self.client = Groq(api_key=GROQ_API_KEY)
        
        # --- AJUSTES PARA SUAVIZAÇÃO EXTREMA ---
        self.smoothing_factor = 0.05  
        self.inertia_threshold = 80   

    def processar_com_ia(self, lista_palavras):
        """Força a tradução para português usando Groq (Llama 3)."""
        if not lista_palavras:
            return [], "MOMENTO ÉPICO! 🔥", "#podcast"
            
        texto_unido = " ".join(lista_palavras)
        
        prompt = f"""
        VOCÊ É UM TRADUTOR OBRIGATÓRIO.
        
        TAREFA:
        1. TRADUZA o texto abaixo para PORTUGUÊS BRASILEIRO.
        2. É PROIBIDO manter o texto em inglês.
        3. Mantenha EXATAMENTE {len(lista_palavras)} palavras na lista 'conteudo'.
        4. Se não conseguir traduzir perfeitamente, adapte, mas ENTREGUE EM PORTUGUÊS.

        Texto Original: {texto_unido}
        
        Responda APENAS em JSON:
        {{
            "conteudo": ["palavra1", "palavra2", ...],
            "titulo": "Título Viral em Português",
            "tags": "#viral #cortes"
        }}
        """
        try:
            time.sleep(0.5) 
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você é um assistente de tradução que só fala Português Brasileiro e responde em JSON."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )
            res_text = chat_completion.choices[0].message.content
            data = json.loads(res_text)
            
            conteudo = data.get("conteudo", [])
            titulo = data.get("titulo", "MOMENTO ÉPICO! 🔥")
            tags = data.get("tags", "#viral #cortes")
            
            while len(conteudo) < len(lista_palavras):
                conteudo.append("...")
                
            return conteudo, titulo, tags
        except Exception as e:
            print(f"⚠️ Erro na IA (Groq): {e}")
            return ["ERRO"], "ERRO", "#erro"

    def get_active_face_x(self, frame):
        """Detecção de rosto para centralizar o corte vertical (9:16)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) > 0:
            best_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = best_face
            if y < (frame.shape[0] * 0.45):
                return x + w/2
        return None

    def create_subtitle(self, word, start, duration):
        txt_clip = TextClip(
            text=f" {word.upper()} ",
            font_size=75, 
            color='yellow', 
            stroke_color='black', 
            stroke_width=3, 
            method='label',
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            text_align='center',
            margin=(25, 25)
        )
        if txt_clip.w > 950:
            txt_clip = txt_clip.resized(width=950)
        return txt_clip.with_position(('center', 1450)).with_start(start).with_duration(duration)

    def create_all_clips(self, video_path, transcription, moments, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        video = VideoFileClip(video_path)
        
        for i, m in enumerate(tqdm(moments, desc="Cortando momentos"), 1):
            is_longo = (i % 4 == 0) 
            duracao_alvo = 65 if is_longo else 40
            pasta_nome = f"corte_{i:02d}_{'LONGO' if is_longo else 'CURTO'}"
            pasta_corte = os.path.join(output_dir, pasta_nome)
            os.makedirs(pasta_corte, exist_ok=True)
            
            start_t = max(0, m['timestamp'] - 2)
            end_t = min(start_t + duracao_alvo, video.duration)
            sub = video.subclipped(start_t, end_t)
            
            # --- CÂMERA ULTRA-SUAVE COM BARRA DE PROGRESSO ---
            segments = []
            current_x = sub.w / 2
            step = 0.5 
            
            time_steps = np.arange(0, sub.duration, step)
            for t in tqdm(time_steps, desc=f"  ↳ Câmera dinâmica (Corte {i})", leave=False):
                frame = sub.get_frame(t)
                new_x = self.get_active_face_x(frame)
                
                if new_x:
                    if abs(new_x - current_x) > self.inertia_threshold:
                        current_x = (current_x * (1 - self.smoothing_factor)) + (new_x * self.smoothing_factor)
                
                target_w = int(sub.h * (9/16))
                x1 = int(max(0, min(current_x - target_w/2, sub.w - target_w)))
                
                seg = sub.subclipped(t, min(t + step, sub.duration)).cropped(x1=x1, x2=x1+target_w, y1=0, y2=sub.h)
                segments.append(seg.resized(width=1080, height=1920))

            sub_v = concatenate_videoclips(segments)
            
            # --- TRANSCRIÇÃO E TRADUÇÃO FORÇADA ---
            palavras_trecho = []
            for segment in transcription['segments']:
                for w_data in segment.get('words', []):
                    if w_data['start'] >= start_t and w_data['end'] <= end_t:
                        palavras_trecho.append(w_data)

            lista_txt = [w['word'].strip() for w in palavras_trecho]
            texto_final, titulo_ia, tags_ia = self.processar_com_ia(lista_txt)

            subs_clips = []
            for idx, w in enumerate(palavras_trecho):
                if idx >= len(texto_final): break
                s, d = w['start'] - start_t, w['end'] - w['start']
                if d > 0: 
                    subs_clips.append(self.create_subtitle(texto_final[idx], s, d))
            
            final = CompositeVideoClip([sub_v] + subs_clips)
            final.write_videofile(os.path.join(pasta_corte, f"video_{i:02d}.mp4"), codec='libx264', audio_codec='aac', threads=4)
            
            with open(os.path.join(pasta_corte, "postagem.txt"), "w", encoding="utf-8") as f:
                f.write(f"TITULO: {titulo_ia}\nTAGS: {tags_ia}")

        video.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Caminho do vídeo")
    parser.add_argument("--max", type=int, default=11)
    parser.add_argument("--model", default="small")
    args = parser.parse_args()

    if os.path.exists(args.video):
        print(f"🚀 Iniciando Processamento: {args.video}")
        clipper = VideoClipper()
        
        print(f"🎙️ Carregando Whisper e Transcrevendo...")
        model_whisper = whisper.load_model(args.model)
        
        # RESTAURADO: verbose=True faz os blocos de texto aparecerem na tela durante a transcrição
        result = model_whisper.transcribe(args.video, word_timestamps=True, verbose=True)
        
        v_meta = VideoFileClip(args.video)
        total = v_meta.duration
        v_meta.close()
        
        intervalo = total / (args.max + 1)
        pontos = [{"timestamp": i * intervalo} for i in range(1, args.max + 1)]
        
        clipper.create_all_clips(args.video, result, pontos, "output")
        print("\n✅ TUDO PRONTO!")
