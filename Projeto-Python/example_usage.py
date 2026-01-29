#!/usr/bin/env python3
"""
Exemplo de uso programático do Podcast Clipper
Demonstra como usar o sistema diretamente em código Python
"""
import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from podcast_clipper import PodcastClipper


def example_basic_usage():
    """
    Exemplo 1: Uso básico com configurações padrão
    """
    print("\n" + "="*60)
    print("EXEMPLO 1: Uso Básico")
    print("="*60 + "\n")
    
    # Inicializar o clipper
    clipper = PodcastClipper(
        whisper_model='base',  # Modelo padrão
        use_llm=True           # Usar análise LLM
    )
    
    # Processar vídeo
    video_path = 'seu_video.mp4'  # Substitua pelo caminho real
    
    clips = clipper.process_video(
        video_path=video_path,
        max_clips=5,                    # Gerar 5 clips
        subtitle_style='word',          # Legendas palavra por palavra
        save_transcription=True         # Salvar transcrição
    )
    
    print(f"\n✓ Gerados {len(clips)} clips!")
    for clip in clips:
        print(f"  - {clip}")


def example_custom_settings():
    """
    Exemplo 2: Configurações personalizadas
    """
    print("\n" + "="*60)
    print("EXEMPLO 2: Configurações Personalizadas")
    print("="*60 + "\n")
    
    # Usar modelo Whisper maior para melhor precisão
    clipper = PodcastClipper(
        whisper_model='medium',  # Modelo maior
        use_llm=True
    )
    
    video_path = 'seu_video.mp4'
    
    clips = clipper.process_video(
        video_path=video_path,
        max_clips=3,                    # Apenas 3 clips
        subtitle_style='phrase',        # Legendas em frases
        save_transcription=True
    )
    
    print(f"\n✓ Gerados {len(clips)} clips com alta qualidade!")


def example_fast_processing():
    """
    Exemplo 3: Processamento rápido (sem LLM)
    """
    print("\n" + "="*60)
    print("EXEMPLO 3: Processamento Rápido")
    print("="*60 + "\n")
    
    # Desabilitar LLM para processamento mais rápido
    clipper = PodcastClipper(
        whisper_model='tiny',   # Modelo mais rápido
        use_llm=False           # Sem análise LLM
    )
    
    video_path = 'seu_video.mp4'
    
    clips = clipper.process_video(
        video_path=video_path,
        max_clips=5,
        subtitle_style='word',
        save_transcription=False  # Não salvar transcrição
    )
    
    print(f"\n✓ Processamento rápido concluído! {len(clips)} clips gerados.")


def example_batch_processing():
    """
    Exemplo 4: Processar múltiplos vídeos em lote
    """
    print("\n" + "="*60)
    print("EXEMPLO 4: Processamento em Lote")
    print("="*60 + "\n")
    
    # Lista de vídeos para processar
    videos = [
        'podcast_ep01.mp4',
        'podcast_ep02.mp4',
        'podcast_ep03.mp4'
    ]
    
    # Inicializar clipper uma vez (reutilizar modelo Whisper)
    clipper = PodcastClipper(whisper_model='base', use_llm=True)
    
    all_clips = []
    
    for video in videos:
        if os.path.exists(video):
            print(f"\nProcessando: {video}")
            clips = clipper.process_video(
                video_path=video,
                max_clips=3,
                subtitle_style='word'
            )
            all_clips.extend(clips)
        else:
            print(f"⚠ Vídeo não encontrado: {video}")
    
    print(f"\n✓ Total de clips gerados: {len(all_clips)}")


def example_using_modules_directly():
    """
    Exemplo 5: Usar módulos individuais diretamente
    """
    print("\n" + "="*60)
    print("EXEMPLO 5: Uso Avançado - Módulos Individuais")
    print("="*60 + "\n")
    
    from modules.audio_processor import AudioProcessor
    from modules.moment_detector import MomentDetector
    from modules.video_clipper import VideoClipper
    
    video_path = 'seu_video.mp4'
    
    # 1. Processar áudio
    audio_proc = AudioProcessor(model_size='base')
    transcription = audio_proc.process_video(video_path, './temp')
    
    print(f"✓ Transcrição: {len(transcription['segments'])} segmentos")
    
    # 2. Detectar momentos
    detector = MomentDetector(use_llm=True)
    audio_path = './temp/seu_video_audio.wav'
    moments = detector.find_best_moments(transcription, audio_path, max_clips=5)
    
    print(f"✓ Momentos detectados: {len(moments)}")
    
    # 3. Gerar clips
    clipper = VideoClipper()
    clips = clipper.create_all_clips(
        video_path,
        transcription,
        moments,
        './output',
        subtitle_style='word'
    )
    
    print(f"✓ Clips gerados: {len(clips)}")


if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════════╗
║         PODCAST CLIPPER - Exemplos de Uso                  ║
║                                                            ║
║  Este arquivo demonstra diferentes formas de usar o       ║
║  sistema Podcast Clipper em seus próprios scripts Python  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    print("\nEscolha um exemplo para executar:")
    print("  1. Uso básico com configurações padrão")
    print("  2. Configurações personalizadas")
    print("  3. Processamento rápido (sem LLM)")
    print("  4. Processamento em lote")
    print("  5. Uso avançado - módulos individuais")
    print("\nNota: Substitua 'seu_video.mp4' pelo caminho real do seu vídeo")
    print("\nPara executar via linha de comando, use:")
    print("  python podcast_clipper.py seu_video.mp4")
