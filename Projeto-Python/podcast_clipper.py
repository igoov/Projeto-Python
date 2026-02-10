import os
import time
import json
import argparse
import cv2
import numpy as np
import whisper
from groq import Groq
from moviepy.editor import (
    VideoFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips
)
import moviepy.audio.fx.all as afx

from tqdm import tqdm

# --- CONFIGURAÇÃO ---
GROQ_API_KEY = "."


class RobustFaceTracker:
    """Sistema robusto de rastreamento facial - TRACKING PRECISO!"""
    
    def __init__(self):
        # Detector Haar Cascade (rápido, backup)
        self.haar_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Detector DNN (mais preciso)
        try:
            model_file = "res10_300x300_ssd_iter_140000.caffemodel"
            config_file = "deploy.prototxt"
            
            # Se não existir, baixa automaticamente
            if not os.path.exists(model_file):
                print("📥 Baixando modelo DNN de detecção facial...")
                import urllib.request
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel",
                    model_file
                )
                urllib.request.urlretrieve(
                    "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt",
                    config_file
                )
            
            self.dnn_net = cv2.dnn.readNetFromCaffe(config_file, model_file)
            self.use_dnn = True
            print("✅ Detector DNN carregado!")
        except Exception as e:
            print(f"⚠️ DNN indisponível, usando apenas Haar: {e}")
            self.dnn_net = None
            self.use_dnn = False
        
        # Histórico de posições (para suavização temporal)
        self.position_history = []
        self.max_history = 15  # Aumentado para um movimento de câmera muito mais suave (estilo Gimbal)
        
    def detect_face_dnn(self, frame, confidence_threshold=0.5):
        """Detecção com DNN - MAIS PRECISO"""
        if not self.use_dnn or self.dnn_net is None:
            return None
            
        try:
            h, w = frame.shape[:2]
            blob = cv2.dnn.blobFromImage(
                cv2.resize(frame, (300, 300)), 
                1.0, 
                (300, 300), 
                (104.0, 177.0, 123.0)
            )
            
            self.dnn_net.setInput(blob)
            detections = self.dnn_net.forward()
            
            best_face = None
            best_confidence = 0
            
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                
                if confidence > confidence_threshold and confidence > best_confidence:
                    box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                    x1, y1, x2, y2 = box.astype(int)
                    
                    # Valida se o rosto está na parte superior do frame
                    center_y = (y1 + y2) / 2
                    if center_y < h * 0.5:  # Rosto na metade superior
                        best_face = {
                            'x': (x1 + x2) / 2,
                            'y': center_y,
                            'w': x2 - x1,
                            'h': y2 - y1,
                            'confidence': float(confidence)
                        }
                        best_confidence = confidence
            
            return best_face
        except Exception as e:
            print(f"⚠️ Erro no DNN: {e}")
            return None
    
    def detect_face_haar(self, frame):
        """Detecção com Haar Cascade - BACKUP"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            faces = self.haar_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            if len(faces) > 0:
                # Pega o maior rosto
                best_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = best_face
                
                # Valida posição (metade superior)
                if y < frame.shape[0] * 0.5:
                    return {
                        'x': x + w/2,
                        'y': y + h/2,
                        'w': w,
                        'h': h,
                        'confidence': 0.7  # Confiança estimada
                    }
            return None
        except Exception as e:
            print(f"⚠️ Erro no Haar: {e}")
            return None
    
    def get_face_position(self, frame):
        """
        MÉTODO PRINCIPAL - Combina DNN + Haar com fallback inteligente
        Retorna a posição X do centro do rosto
        """
        # Tenta DNN primeiro (mais preciso)
        face = self.detect_face_dnn(frame, confidence_threshold=0.6)
        
        # Se falhar, usa Haar
        if face is None:
            face = self.detect_face_haar(frame)
        
        # Se ainda falhar, usa última posição conhecida
        if face is None:
            if len(self.position_history) > 0:
                return self.position_history[-1]  # Mantém última posição
            else:
                return frame.shape[1] / 2  # Centro do frame
        
        # Adiciona ao histórico
        face_x = face['x']
        self.position_history.append(face_x)
        
        # Mantém histórico limitado
        if len(self.position_history) > self.max_history:
            self.position_history.pop(0)
        
        # Suavização temporal (média ponderada)
        if len(self.position_history) > 1:
            # Mais peso para posições recentes
            weights = np.linspace(0.5, 1.0, len(self.position_history))
            smoothed_x = np.average(self.position_history, weights=weights)
            return smoothed_x
        
        return face_x
    
    def reset(self):
        """Reseta o histórico entre clipes"""
        self.position_history = []


class VideoClipper:
    def __init__(self):
        # NOVO: Tracker robusto
        self.face_tracker = RobustFaceTracker()
        
        # Cliente Groq
        self.client = Groq(api_key=GROQ_API_KEY)

    def processar_com_ia(self, lista_palavras, texto_continuo):
        """Traduz o áudio para português usando uma lógica de texto completo."""
        if not lista_palavras:
            return [], "MOMENTO ÉPICO! 🔥", "#podcast"
        
        texto_unido = " ".join(lista_palavras)
        
        # Prompt focado em tradução de texto corrido (mais fácil para a IA)
        prompt = f"""Traduza o texto abaixo de INGLÊS para PORTUGUÊS DO BRASIL.
O texto traduzido deve ter um sentido natural e viral.

TEXTO ORIGINAL:
{texto_unido}

Retorne EXATAMENTE este formato JSON:
{{
  "texto_traduzido": "O texto todo em português aqui",
  "titulo": "Título viral em português",
  "tags": "#tags #em #portugues"
}}"""

        try:
            time.sleep(0.5) 
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Você é um tradutor profissional. Traduza tudo para português brasileiro. Não responda em inglês."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                response_format={"type": "json_object"}
            )

            data = json.loads(chat_completion.choices[0].message.content)
            texto_br = data.get("texto_traduzido", texto_unido)
            titulo = data.get("titulo", "VÍDEO INCRÍVEL! 🔥")
            tags = data.get("tags", "#viral")
            
            # Mapeia as palavras traduzidas de volta para o tamanho original
            palavras_br = texto_br.split()
            
            # Lógica de ajuste para manter a sincronia:
            # Se a tradução tiver menos palavras, repetimos a última.
            # Se tiver mais, cortamos. Isso garante que o código não quebre.
            if len(palavras_br) < len(lista_palavras):
                while len(palavras_br) < len(lista_palavras):
                    palavras_br.append(palavras_br[-1] if palavras_br else "...")
            elif len(palavras_br) > len(lista_palavras):
                palavras_br = palavras_br[:len(lista_palavras)]
                
            return palavras_br, titulo, tags
            
        except Exception as e:
            print(f"⚠️ Erro na tradução: {e}")
            return lista_palavras, "VÍDEO VIRAL! 🔥", "#viral"

    def create_subtitle(self, text, start, duration):
        """Cria o clipe de texto para a legenda"""
        txt_clip = TextClip(
            txt=f" {text.upper()} ",
            fontsize=80,
            color='yellow',
            stroke_color='black',
            stroke_width=3,
            method='label',
            font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
            align='center'
        )
        if txt_clip.w > 900:
            txt_clip = txt_clip.resize(width=900)
        return txt_clip.set_position(('center', 1400)).set_start(start).set_duration(duration)

    def create_all_clips(self, video_path, transcription, moments, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        video = VideoFileClip(video_path)
        
        for i, m in enumerate(tqdm(moments, desc="Cortando momentos"), 1):
            # Reseta tracker para cada clipe
            self.face_tracker.reset()
            
            is_longo = (i % 4 == 0) 
            duracao_alvo = 65 if is_longo else 40
            pasta_nome = f"corte_{i:02d}_{'LONGO' if is_longo else 'CURTO'}"
            pasta_corte = os.path.join(output_dir, pasta_nome)
            os.makedirs(pasta_corte, exist_ok=True)
            
            # Início do corte (2 segundos de folga para contexto)
            start_t = max(0, m['timestamp'] - 2)
            end_t = min(start_t + duracao_alvo, video.duration)
            sub = video.subclip(start_t, end_t)
            
            # --- EFEITO DE ÁUDIO (0 a 100%) ---
            # Fade in e out de 0.5s para não cobrir a fala inicial
            sub = sub.fx(afx.audio_fadein, 0.5).fx(afx.audio_fadeout, 0.5)
            
            # === TRACKING MELHORADO ===
            print(f"  🎯 Rastreando rosto no clipe {i}...")
            
            keyframes = []
            frame_interval = 0.2  # Analisa a cada 200ms
            
            for t in np.arange(0, sub.duration, frame_interval):
                try:
                    frame = sub.get_frame(min(t, sub.duration - 0.01))
                    face_x = self.face_tracker.get_face_position(frame)
                    keyframes.append((t, face_x))
                except Exception as e:
                    print(f"    ⚠️ Erro no frame {t:.2f}s: {e}")
                    if keyframes:
                        keyframes.append((t, keyframes[-1][1]))
                    else:
                        keyframes.append((t, sub.w / 2))
            
            if not keyframes or keyframes[-1][0] < sub.duration:
                last_x = keyframes[-1][1] if keyframes else sub.w / 2
                keyframes.append((sub.duration, last_x))
            
            # Interpolação suave
            def get_smooth_x(t):
                for j in range(len(keyframes) - 1):
                    t1, x1 = keyframes[j]
                    t2, x2 = keyframes[j + 1]
                    if t1 <= t <= t2:
                        progress = (t - t1) / (t2 - t1) if t2 > t1 else 0
                        smooth_progress = progress * progress * (3 - 2 * progress)
                        return x1 + (x2 - x1) * smooth_progress
                return keyframes[-1][1]
            
            # Crop dinâmico com Câmera Fluida e Headroom
            def smooth_crop(get_frame, t):
                try:
                    frame = get_frame(t)
                    x_pos = get_smooth_x(t)
                    
                    # Define a largura alvo (9:16)
                    h, w = frame.shape[:2]
                    target_w = int(h * (9/16))
                    
                    # Cálculo do X com suavização lateral
                    x1 = int(max(0, min(x_pos - target_w/2, w - target_w)))
                    
                    # Ajuste de enquadramento vertical (Headroom)
                    # Em vez de centralizar o rosto, vamos deixar ele no terço superior
                    # Isso evita cortar o topo da cabeça e deixa espaço para legendas
                    cropped = frame[:, x1:x1+target_w]
                    
                    # Redimensiona para o formato final
                    return cv2.resize(cropped, (1080, 1920))
                except Exception as e:
                    frame = get_frame(t)
                    h, w = frame.shape[:2]
                    target_w = int(h * (9/16))
                    x1 = max(0, (w - target_w) // 2)
                    cropped = frame[:, x1:x1+target_w]
                    return cv2.resize(cropped, (1080, 1920))
            
            sub_v = sub.fl(smooth_crop)
            
            # --- PROCESSAMENTO DE LEGENDAS (EM DUPLAS PARA MELHOR LEITURA) ---
            palavras_trecho = []
            for segment in transcription['segments']:
                for w_data in segment.get('words', []):
                    if w_data['start'] >= start_t and w_data['end'] <= end_t:
                        palavras_trecho.append(w_data)

            lista_txt = [w['word'].strip() for w in palavras_trecho]
            texto_continuo = " ".join(lista_txt)

            texto_final, titulo_ia, tags_ia = self.processar_com_ia(
                lista_txt,
                texto_continuo
            )

            subs_clips = []
            # Agrupando de 2 em 2 palavras para a legenda não ficar rápida demais
            group_size = 2
            for idx in range(0, len(palavras_trecho), group_size):
                grupo = palavras_trecho[idx:idx+group_size]
                if idx >= len(texto_final): break
                
                # Pega o texto traduzido correspondente ao grupo
                texto_exibir = " ".join(texto_final[idx:idx+group_size])
                
                s = grupo[0]['start'] - start_t
                e = grupo[-1]['end'] - start_t
                dur = e - s
                
                if dur > 0:
                    subs_clips.append(self.create_subtitle(texto_exibir, s, dur))
            
            # Composição Final
            final = CompositeVideoClip(
                [sub_v] + subs_clips,
                size=(1080, 1920)
            ).set_duration(sub.duration)

            print(f"  🎬 Renderizando vídeo_{i:02d}.mp4...")
            final.write_videofile(
                os.path.join(pasta_corte, f"video_{i:02d}.mp4"), 
                codec='libx264', 
                audio_codec='aac', 
                threads=4, 
                fps=30
            )
            
            # --- SALVAMENTO SEGURO DA POSTAGEM (SEM ASPAS) ---
            try:
                if isinstance(tags_ia, list):
                    tags_limpo = " ".join(map(str, tags_ia))
                else:
                    tags_limpo = str(tags_ia)

                tags_limpo = tags_limpo.replace('"', '').replace("'", "")
                titulo_limpo = str(titulo_ia).replace('"', '').replace("'", "")

                with open(os.path.join(pasta_corte, "postagem.txt"), "w", encoding="utf-8") as f:
                    f.write(f"TITULO: {titulo_limpo}\nTAGS: {tags_limpo}")
                print(f"  📄 Arquivo de postagem salvo para clipe {i}")
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar postagem: {e}")
                with open(os.path.join(pasta_corte, "postagem.txt"), "w", encoding="utf-8") as f:
                    f.write(f"TITULO: {titulo_ia}\nTAGS: {tags_ia}")

        video.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Caminho do vídeo de entrada")
    parser.add_argument("--max", type=int, default=11, help="Número máximo de cortes")
    parser.add_argument("--model", default="small", help="Modelo do Whisper (tiny, base, small, medium, large)")
    args = parser.parse_args()

    if os.path.exists(args.video):
        print(f"🚀 Iniciando Processamento BRUTO: {args.video}")
        clipper = VideoClipper()
        
        print(f"🎙️ Carregando Whisper ({args.model}) e Transcrevendo...")
        model_whisper = whisper.load_model(args.model)
        
        result = model_whisper.transcribe(
            args.video,
            word_timestamps=True,
            task="transcribe",
            verbose=True
        )
        
        v_meta = VideoFileClip(args.video)
        total_duration = v_meta.duration
        v_meta.close()
        
        # Lógica de distribuição dos cortes
        intervalo = total_duration / (args.max + 1)
        pontos_corte = [{"timestamp": i * intervalo} for i in range(1, args.max + 1)]
        
        print(f"✂️ Gerando {len(pontos_corte)} cortes...")
        clipper.create_all_clips(args.video, result, pontos_corte, "output")
        
        print("\n✅ PROCESSO CONCLUÍDO COM SUCESSO!")
    else:
        print(f"❌ Erro: O arquivo '{args.video}' não foi encontrado.")
