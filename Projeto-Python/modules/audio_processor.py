import whisper
import time

class AudioProcessor: # Nome da classe deve ser exatamente este
    def __init__(self, model_size='tiny'):
        print(f"→ Carregando modelo Whisper ({model_size})...")
        self.model = whisper.load_model(model_size)

    def process_video(self, video_path):
        print("\n[PASSO 1/3] 🎤 Transcrevendo áudio (IA)...")
        start = time.time()
        # Word timestamps ativado para as legendas
        result = self.model.transcribe(video_path, word_timestamps=True, verbose=False)
        print(f"✓ Concluído em {int(time.time() - start)} segundos.")
        return result