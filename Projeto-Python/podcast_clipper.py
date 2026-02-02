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
GROQ_API_KEY = ","

class VideoClipper:
    def __init__(self):
        # Carrega o detector de rostos do OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Inicializa o cliente Groq
        self.client = Groq(api_key=GROQ_API_KEY)

    def processar_com_ia(self, lista_palavras):
        """Traduz do inglês ou revisa o português usando Groq (Llama 3)."""
        if not lista_palavras:
            return [], "MOMENTO ÉPICO! 🔥", "#podcast"
            
        texto_unido = " ".join(lista_palavras)
        
        prompt = f"""
        Atue como um editor de vídeos viral e tradutor especializado. 
        TAREFA:
        1. Se o texto estiver em Inglês, TRADUZA para Português Brasileiro natural e coloquial.
        2. Se estiver em Português, revise a gramática e torne-o mais impactante.
        3. IMPORTANTE: Tente manter o mesmo número de elementos na lista 'conteudo' para manter a sincronia com o vídeo original.
        4. Gere um TÍTULO CLICKBAIT e 6 HASHTAGS virais.
        
        Texto Original: {texto_unido}
        
        Responda ESTRITAMENTE no formato JSON abaixo:
        {{
            "conteudo": ["palavra1", "palavra2", "palavra3", ...],
            "titulo": "Seu Titulo Viral Aqui",
            "tags": "#tag1 #tag2 #tag3 #tag4 #tag5 #tag6"
        }}
        """
        try:
            # Groq é ultra rápido, o sleep de 0.5s é apenas para segurança de rate limit
            time.sleep(0.5) 
            
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você é um assistente que traduz vídeos e responde apenas em JSON puro."},
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
            
            return conteudo, titulo, tags
        except Exception as e:
            print(f"⚠️ Erro na IA (Groq): {e}")
            return lista_palavras, "CONFIRA ISSO! 🔥", "#podcast #cortes"

    def get_active_face_x(self, frame):
        """Detecção de rosto para centralizar o corte vertical (9:16)."""
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        # Filtra detecções muito baixas (mesa)
        valid_faces = [x + w/2 for (x, y, w, h) in faces if y < (frame.shape[0] * 0.45)]
        return valid_faces[0] if valid_faces else None

    def create_subtitle(self, word, start, duration):
        """
        Cria legendas inteligentes:
        1. Usa 'label' para precisão máxima (evita cortes no topo/base).
        2. Adiciona espaços laterais para garantir que o contorno não suma.
        3. Mantém a margem de segurança.
        """
        txt_clip = TextClip(
            text=f" {word.upper()} ", # Espaços extras ajudam na renderização
            font_size=75, 
            color='yellow', 
            stroke_color='black', 
            stroke_width=3, 
            method='label', # MUDADO: 'label' é melhor que 'caption' para evitar cortes
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            text_align='center',
            margin=(25, 25) # Margem aumentada para garantir o respiro
        )

        # Se a palavra for muito longa para a tela vertical, redimensiona
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
            
            # --- IA E TRADUÇÃO VIA GROQ ---
            palavras_trecho = []
            for segment in transcription['segments']:
                for w_data in segment.get('words', []):
                    if w_data['start'] >= start_t and w_data['end'] <= end_t:
                        palavras_trecho.append(w_data)

            lista_txt = [w['word'].strip() for w in palavras_trecho]
            
            # Chama o Groq para traduzir e gerar metadados
            texto_traduzido, titulo_ia, tags_ia = self.processar_com_ia(lista_txt)
            
            # Fallback caso a tradução mude o número de palavras drasticamente
            if len(texto_traduzido) != len(palavras_trecho):
                print(f"⚠️ Aviso: A tradução gerou {len(texto_traduzido)} palavras para {len(palavras_trecho)} originais. Ajustando...")
                if abs(len(texto_traduzido) - len(palavras_trecho)) > 5:
                    texto_final = lista_txt
                else:
                    texto_final = texto_traduzido
            else:
                texto_final = texto_traduzido

            subs_clips = []
            for idx, w in enumerate(palavras_trecho):
                if idx >= len(texto_final): break
                
                s = w['start'] - start_t
                d = w['end'] - w['start']
                if d > 0:
                    subs_clips.append(self.create_subtitle(texto_final[idx], s, d))
            
            # --- RENDERIZAÇÃO ---
            final = CompositeVideoClip([sub_v] + subs_clips)
            final.write_videofile(os.path.join(pasta_corte, f"video_{i:02d}.mp4"), codec='libx264', audio_codec='aac', threads=4)
            
            with open(os.path.join(pasta_corte, "postagem.txt"), "w", encoding="utf-8") as f:
                f.write(f"TITULO: {titulo_ia}\nTAGS: {tags_ia}")

        video.close()

# --- BLOCO PRINCIPAL ---
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
        result = model_whisper.transcribe(args.video, word_timestamps=True, verbose=True)
        
        v_meta = VideoFileClip(args.video)
        total = v_meta.duration
        v_meta.close()
        
        intervalo = total / (args.max + 1)
        pontos = [{"timestamp": i * intervalo} for i in range(1, args.max + 1)]
        
        clipper.create_all_clips(args.video, result, pontos, "output")
        print("\n✅ TUDO PRONTO!")
