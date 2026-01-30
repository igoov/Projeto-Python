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
# Substitua pela sua chave real
genai.configure(api_key="SUA_CHAVE_GEMINI_AQUI")

class VideoClipper:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        # Configurações de enquadramento baseadas na análise do manus
        self.target_width = 1080
        self.target_height = 1920

    def processar_com_ia(self, lista_palavras):
        """Traduz do inglês ou Revisa o português usando Gemini."""
        if not lista_palavras:
            return [], "MOMENTO ÉPICO! 🔥", "#podcast"
            
        texto_bruto = " ".join(lista_palavras)
        
        prompt = f"""
        Atue como um editor de vídeo viral.
        TAREFA: 
        1. Se o texto abaixo estiver em Inglês, TRADUZA para Português Brasileiro coloquial.
        2. Se estiver em Português, apenas revise.
        3. Mantenha o mesmo número de palavras.
        4. Crie um TÍTULO IMPACTANTE e 6 TAGS.

        TEXTO: {texto_bruto}
        
        Responda APENAS em JSON:
        {{
            "conteudo": ["palavra1", "palavra2"],
            "titulo": "Titulo Aqui",
            "tags": "#tag1 #tag2"
        }}
        """
        try:
            time.sleep(4) 
            response = self.model.generate_content(prompt)
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            data = json.loads(res_text)
            return data.get("conteudo", []), data.get("titulo", "MOMENTO ÉPICO!"), data.get("tags", "#viral")
        except Exception as e:
            print(f"⚠️ Falha na IA: {e}")
            return lista_palavras, "CONFIRA ISSO! 🔥", "#podcast"

    def get_active_face_x(self, frame):
        """Detecta rosto e ignora a parte inferior (mesa)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        valid_faces = [x + w/2 for (x, y, w, h) in faces if y < (frame.shape[0] * 0.45)]
        return valid_faces[0] if valid_faces else None

    def create_subtitle(self, word, start, duration):
        """
        Cria legendas inteligentes:
        1. Usa 'caption' para quebra de linha.
        2. Adiciona 'margin' para não cortar o contorno (Stroke).
        3. Verifica largura e encolhe se necessário (Lógica Manus).
        """
        txt_clip = TextClip(
            text=word.upper(), 
            font_size=75, 
            color='yellow', 
            stroke_color='black', 
            stroke_width=3, # Aumentado para melhor leitura
            method='caption',
            size=(850, None), # Largura máxima permitida
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            text_align='center',
            margin=(20, 20) # Margem de segurança para o contorno
        )

        # Lógica de proteção: se mesmo com caption a palavra for gigante, redimensiona
        if txt_clip.w > 900:
            txt_clip = txt_clip.resized(width=900)

        return txt_clip.with_position(('center', 1450)).with_start(start).with_duration(duration)

    def create_all_clips(self, video_path, transcription, moments, output_dir):
        video = VideoFileClip(video_path)
        
        # Barra de progresso para os cortes (Tqdm)
        for i, m in enumerate(tqdm(moments, desc="Cortando momentos"), 1):
            is_longo = (i % 4 == 0)
            duracao = 65 if is_longo else 40
            pasta_nome = f"corte_{i:02d}_{'LONGO' if is_longo else 'CURTO'}"
            pasta_corte = os.path.join(output_dir, pasta_nome)
            os.makedirs(pasta_corte, exist_ok=True)
            
            print(f"\n🚀 PROCESSANDO CORTE {i}/{len(moments)}")
            
            start_t = max(0, m['timestamp'] - 2)
            end_t = min(start_t + duracao, video.duration)
            sub = video.subclipped(start_t, end_t)
            
            # --- CÂMERA DINÂMICA ---
            segments = []
            last_x = sub.w / 2
            for t in np.arange(0, sub.duration, 1.0):
                frame = sub.get_frame(t)
                new_x = self.get_active_face_x(frame)
                if new_x: last_x = new_x
                
                target_w = int(sub.h * 9/16)
                x1 = int(max(0, min(last_x - target_w/2, sub.w - target_w)))
                seg = sub.subclipped(t, min(t + 1.0, sub.duration)).cropped(x1=x1, x2=x1+target_w, y1=0, y2=sub.h)
                segments.append(seg.resized(width=1080, height=1920))

            sub_v = concatenate_videoclips(segments)
            
            # --- TRADUÇÃO E LEGENDAS ---
            palavras_originais = []
            for segment in transcription['segments']:
                for w in segment.get('words', []):
                    if w['start'] >= start_t and w['end'] <= end_t:
                        palavras_originais.append(w)

            lista_txt = [w['word'].strip() for w in palavras_originais]
            texto_br, titulo_ia, tags_ia = self.processar_com_ia(lista_txt)
            
            if len(texto_br) != len(palavras_originais): texto_br = lista_txt

            subs_clips = []
            for idx, w in enumerate(palavras_originais):
                s = w['start'] - start_t
                d = w['end'] - w['start']
                if d > 0:
                    subs_clips.append(self.create_subtitle(texto_br[idx], s, d))
            
            # --- RENDERIZAÇÃO ---
            final = CompositeVideoClip([sub_v] + subs_clips)
            output_file = os.path.join(pasta_corte, f"video_final_{i:02d}.mp4")
            final.write_videofile(output_file, codec='libx264', audio_codec='aac', fps=24, threads=4, logger='bar')
            
            with open(os.path.join(pasta_corte, "postagem.txt"), "w", encoding="utf-8") as f:
                f.write(f"TÍTULO: {titulo_ia}\nTAGS: {tags_ia}")

        video.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video")
    parser.add_argument("--max", type=int, default=11)
    parser.add_argument("--model", default="small")
    args = parser.parse_args()

    if os.path.exists(args.video):
        clipper = VideoClipper()
        print(f"🚀 Iniciando Processamento...")
        
        # 1. Whisper com VERBOSE para você ver o processo
        print(f"🎙️ Transcrevendo {args.video}...")
        m_whisper = whisper.load_model(args.model)
        result = m_whisper.transcribe(args.video, word_timestamps=True, verbose=True)
        
        # 2. Divisão automática
        v_meta = VideoFileClip(args.video)
        total = v_meta.duration
        v_meta.close()
        
        intervalo = total / (args.max + 1)
        pontos = [{"timestamp": i * intervalo} for i in range(1, args.max + 1)]
        
        clipper.create_all_clips(args.video, result, pontos, "output")