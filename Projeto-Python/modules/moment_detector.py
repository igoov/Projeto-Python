class MomentDetector:
    def find_best_moments(self, transcription, max_clips=10):
        segments = transcription.get('segments', [])
        triggers = ['pix', 'doação', 'pergunta', 'mandou', 'lê aí']
        moments = []
        for seg in segments:
            if any(word in seg['text'].lower() for word in triggers):
                # Evita clips sobrepostos (intervalo de 2 min)
                if not moments or (seg['start'] - moments[-1]['timestamp'] > 120):
                    moments.append({'timestamp': seg['start']})
            if len(moments) >= max_clips: break
        return moments