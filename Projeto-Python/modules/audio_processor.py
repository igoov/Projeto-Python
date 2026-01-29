"""
Módulo para extração de áudio e transcrição usando Whisper
"""
import whisper
import os
from pathlib import Path
import json
import subprocess


class AudioProcessor:
    def __init__(self, model_size="base"):
        """
        Inicializa o processador de áudio
        
        Args:
            model_size: Tamanho do modelo Whisper (tiny, base, small, medium, large)
        """
        print(f"Carregando modelo Whisper ({model_size})...")
        self.model = whisper.load_model(model_size)
        print("Modelo carregado com sucesso!")
    
    def extract_audio(self, video_path, output_audio_path):
        """
        Extrai o áudio de um vídeo usando FFmpeg
        
        Args:
            video_path: Caminho do vídeo de entrada
            output_audio_path: Caminho para salvar o áudio extraído
        """
        print(f"Extraindo áudio de {video_path}...")
        
        command = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # Sem vídeo
            '-acodec', 'pcm_s16le',  # Codec de áudio
            '-ar', '16000',  # Sample rate (Whisper prefere 16kHz)
            '-ac', '1',  # Mono
            '-y',  # Sobrescrever arquivo existente
            output_audio_path
        ]
        
        try:
            subprocess.run(command, check=True, capture_output=True)
            print(f"Áudio extraído com sucesso: {output_audio_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Erro ao extrair áudio: {e}")
            return False
    
    def transcribe(self, audio_path, language="pt"):
        """
        Transcreve o áudio usando Whisper
        
        Args:
            audio_path: Caminho do arquivo de áudio
            language: Idioma do áudio (pt para português)
            
        Returns:
            Dicionário com transcrição completa e segmentos
        """
        print(f"Transcrevendo áudio: {audio_path}...")
        
        result = self.model.transcribe(
            audio_path,
            language=language,
            verbose=False,
            word_timestamps=True  # Importante para sincronização de legendas
        )
        
        print(f"Transcrição concluída! {len(result['segments'])} segmentos encontrados.")
        
        return {
            'text': result['text'],
            'segments': result['segments'],
            'language': result['language']
        }
    
    def save_transcription(self, transcription, output_path):
        """
        Salva a transcrição em formato JSON
        
        Args:
            transcription: Dicionário com dados da transcrição
            output_path: Caminho para salvar o arquivo JSON
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)
        
        print(f"Transcrição salva em: {output_path}")
    
    def process_video(self, video_path, temp_dir):
        """
        Processa um vídeo completo: extrai áudio e transcreve
        
        Args:
            video_path: Caminho do vídeo
            temp_dir: Diretório temporário para arquivos intermediários
            
        Returns:
            Dicionário com transcrição
        """
        video_name = Path(video_path).stem
        audio_path = os.path.join(temp_dir, f"{video_name}_audio.wav")
        transcription_path = os.path.join(temp_dir, f"{video_name}_transcription.json")
        
        # Extrair áudio
        if not self.extract_audio(video_path, audio_path):
            raise Exception("Falha ao extrair áudio do vídeo")
        
        # Transcrever
        transcription = self.transcribe(audio_path)
        
        # Salvar transcrição
        self.save_transcription(transcription, transcription_path)
        
        return transcription
