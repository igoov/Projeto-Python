#!/usr/bin/env python3
"""
Podcast Clipper - Sistema automático de geração de clips virais
Processa vídeos de podcast e gera cortes verticais com legendas para redes sociais
"""
import os
from dotenv import load_dotenv
from modules.moment_detector import MomentDetector
import sys
import argparse
from pathlib import Path
import json

load_dotenv()
detector = MomentDetector(use_llm=True)

# Adicionar diretório modules ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from audio_processor import AudioProcessor
from moment_detector import MomentDetector
from video_clipper import VideoClipper


class PodcastClipper:
    def __init__(self, whisper_model='base', use_llm=True):
        """
        Inicializa o sistema de clipagem de podcasts
        
        Args:
            whisper_model: Tamanho do modelo Whisper (tiny, base, small, medium, large)
            use_llm: Se True, usa LLM para análise semântica
        """
        print("=" * 60)
        print("PODCAST CLIPPER - Gerador Automático de Clips Virais")
        print("=" * 60)
        
        self.audio_processor = AudioProcessor(model_size=whisper_model)
        self.moment_detector = MomentDetector(use_llm=use_llm)
        self.video_clipper = VideoClipper()
        
        # Diretórios
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_dir, 'temp')
        self.output_dir = os.path.join(self.base_dir, 'output')
        
        # Criar diretórios se não existirem
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def process_video(self, video_path, max_clips=5, subtitle_style='word', 
                     save_transcription=True):
        """
        Processa um vídeo completo e gera clips
        
        Args:
            video_path: Caminho do vídeo de entrada
            max_clips: Número máximo de clips a gerar
            subtitle_style: 'word' (palavra por palavra) ou 'phrase' (frases completas)
            save_transcription: Se True, salva a transcrição em JSON
            
        Returns:
            Lista de caminhos dos clips gerados
        """
        if not os.path.exists(video_path):
            print(f"✗ Erro: Vídeo não encontrado: {video_path}")
            return []
        
        video_name = Path(video_path).stem
        print(f"\n{'='*60}")
        print(f"Processando: {video_name}")
        print(f"{'='*60}\n")
        
        # ETAPA 1: Extração de áudio e transcrição
        print("ETAPA 1/4: Extração de áudio e transcrição")
        print("-" * 60)
        
        try:
            transcription = self.audio_processor.process_video(video_path, self.temp_dir)
            audio_path = os.path.join(self.temp_dir, f"{video_name}_audio.wav")
            
            print(f"✓ Transcrição concluída: {len(transcription['text'])} caracteres")
            print(f"✓ Segmentos: {len(transcription['segments'])}")
            
        except Exception as e:
            print(f"✗ Erro na transcrição: {e}")
            return []
        
        # ETAPA 2: Detecção de momentos interessantes
        print(f"\nETAPA 2/4: Detecção de momentos interessantes")
        print("-" * 60)
        
        try:
            moments = self.moment_detector.find_best_moments(
                transcription,
                audio_path,
                max_clips=max_clips
            )
            
            if not moments:
                print("✗ Nenhum momento interessante detectado")
                return []
            
            print(f"\n✓ {len(moments)} momentos selecionados:")
            for i, moment in enumerate(moments, 1):
                print(f"  {i}. [{moment['timestamp']:.1f}s] - {moment.get('reason', 'N/A')}")
            
        except Exception as e:
            print(f"✗ Erro na detecção de momentos: {e}")
            return []
        
        # ETAPA 3: Geração de clips
        print(f"\nETAPA 3/4: Geração de clips verticais")
        print("-" * 60)
        
        try:
            clips = self.video_clipper.create_all_clips(
                video_path,
                transcription,
                moments,
                self.output_dir,
                subtitle_style=subtitle_style
            )
            
            print(f"\n✓ {len(clips)} clips gerados com sucesso")
            
        except Exception as e:
            print(f"✗ Erro na geração de clips: {e}")
            return []
        
        # ETAPA 4: Finalização
        print(f"\nETAPA 4/4: Finalização")
        print("-" * 60)
        
        # Salvar informações sobre os clips gerados
        clips_info = {
            'video_source': video_path,
            'video_name': video_name,
            'clips_generated': len(clips),
            'subtitle_style': subtitle_style,
            'moments': moments,
            'clips': clips
        }
        
        info_path = os.path.join(self.output_dir, f"{video_name}_clips_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(clips_info, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Informações salvas: {info_path}")
        
        if save_transcription:
            trans_path = os.path.join(self.output_dir, f"{video_name}_transcription.json")
            with open(trans_path, 'w', encoding='utf-8') as f:
                json.dump(transcription, f, ensure_ascii=False, indent=2)
            print(f"✓ Transcrição salva: {trans_path}")
        
        # Resumo final
        print(f"\n{'='*60}")
        print("PROCESSAMENTO CONCLUÍDO!")
        print(f"{'='*60}")
        print(f"Clips gerados: {len(clips)}")
        print(f"Diretório de saída: {self.output_dir}")
        print(f"\nClips criados:")
        for i, clip_path in enumerate(clips, 1):
            file_size = os.path.getsize(clip_path) / (1024 * 1024)  # MB
            print(f"  {i}. {os.path.basename(clip_path)} ({file_size:.1f} MB)")
        print(f"{'='*60}\n")
        
        return clips


def main():
    parser = argparse.ArgumentParser(
        description='Podcast Clipper - Gerador automático de clips virais para redes sociais',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  
  # Processar vídeo com configurações padrão (5 clips, legendas palavra por palavra)
  python podcast_clipper.py meu_podcast.mp4
  
  # Gerar 3 clips com legendas em frases completas
  python podcast_clipper.py meu_podcast.mp4 --max-clips 3 --subtitle-style phrase
  
  # Usar modelo Whisper maior para melhor precisão
  python podcast_clipper.py meu_podcast.mp4 --whisper-model medium
  
  # Desabilitar análise LLM (mais rápido, mas menos preciso)
  python podcast_clipper.py meu_podcast.mp4 --no-llm
        """
    )
    
    parser.add_argument(
        'video',
        help='Caminho do vídeo de podcast (mp4, mov, avi, etc.)'
    )
    
    parser.add_argument(
        '--max-clips',
        type=int,
        default=5,
        help='Número máximo de clips a gerar (padrão: 5)'
    )
    
    parser.add_argument(
        '--subtitle-style',
        choices=['word', 'phrase'],
        default='word',
        help='Estilo das legendas: "word" (palavra por palavra, estilo viral) ou "phrase" (frases completas) (padrão: word)'
    )
    
    parser.add_argument(
        '--whisper-model',
        choices=['tiny', 'base', 'small', 'medium', 'large'],
        default='base',
        help='Tamanho do modelo Whisper (padrão: base). Modelos maiores são mais precisos mas mais lentos'
    )
    
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Desabilitar análise com LLM (usa apenas heurísticas)'
    )
    
    parser.add_argument(
        '--no-save-transcription',
        action='store_true',
        help='Não salvar arquivo de transcrição'
    )
    
    args = parser.parse_args()
    
    # Validar arquivo de entrada
    if not os.path.exists(args.video):
        print(f"✗ Erro: Arquivo não encontrado: {args.video}")
        sys.exit(1)
    
    # Inicializar sistema
    clipper = PodcastClipper(
        whisper_model=args.whisper_model,
        use_llm=not args.no_llm
    )
    
    # Processar vídeo
    clips = clipper.process_video(
        args.video,
        max_clips=args.max_clips,
        subtitle_style=args.subtitle_style,
        save_transcription=not args.no_save_transcription
    )
    
    # Status de saída
    if clips:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
