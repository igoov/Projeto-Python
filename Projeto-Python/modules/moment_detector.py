"""
Módulo para detecção de momentos interessantes em podcasts - Versão com Chave Configurada
"""
import numpy as np
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import re
import google.generativeai as genai
import os

class MomentDetector:
    def __init__(self, use_llm=True):
        """
        Inicializa o detector de momentos interessantes usando Gemini
        """
        self.use_llm = use_llm
        if use_llm:
            # Chave configurada diretamente conforme solicitado
            api_key = "AIzaSyCqfteZkSbcd6lO_ePiOq5RqXqiYzqzD-A"
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_audio_energy(self, audio_path):
        print("Analisando energia do áudio...")
        audio = AudioSegment.from_wav(audio_path)
        nonsilent_ranges = detect_nonsilent(audio, min_silence_len=500, silence_thresh=audio.dBFS - 16)
        chunk_length = 1000
        energy_scores = []
        for i in range(0, len(audio), chunk_length):
            chunk = audio[i:i + chunk_length]
            if len(chunk) > 0:
                energy_scores.append({'timestamp': i / 1000.0, 'energy': chunk.dBFS})
        energies = [s['energy'] for s in energy_scores]
        threshold = np.percentile(energies, 75)
        high_energy_moments = [s for s in energy_scores if s['energy'] > threshold]
        print(f"Encontrados {len(high_energy_moments)} momentos de alta energia")
        return high_energy_moments
    
    def detect_laughter_pauses(self, segments):
        print("Detectando risadas e pausas...")
        laughter_moments = []
        for i, segment in enumerate(segments):
            text = segment['text'].lower()
            laughter_patterns = [r'\b(ha+h+a+|he+h+e+|hi+h+i+|kk+|rsrs|kkk+)\b', r'\[ris[ao]s?\]', r'\(ris[ao]s?\)']
            for pattern in laughter_patterns:
                if re.search(pattern, text):
                    laughter_moments.append({'timestamp': segment['start'], 'type': 'laughter', 'text': segment['text'], 'confidence': 0.8})
                    break
            if i < len(segments) - 1:
                pause_duration = segments[i + 1]['start'] - segment['end']
                if pause_duration > 2.0:
                    laughter_moments.append({'timestamp': segment['end'], 'type': 'pause', 'duration': pause_duration, 'confidence': 0.6})
        print(f"Encontrados {len(laughter_moments)} momentos de risada/pausa")
        return laughter_moments
    
    def analyze_text_content(self, segments):
        print("Analisando conteúdo textual...")
        strong_moments = []
        keywords = ['incrível', 'impressionante', 'surpreendente', 'chocante', 'nunca', 'sempre', 'jamais', 'segredo', 'verdade', 'mentira', 'descobri', 'revelação', 'importante', 'fundamental', 'essencial', 'crucial', 'problema', 'solução', 'dica', 'truque', 'hack']
        question_patterns = [r'\?$', r'^(por que|como|quando|onde|o que|qual)']
        for segment in segments:
            text = segment['text'].lower().strip()
            score = 0
            for keyword in keywords:
                if keyword in text: score += 0.3
            for pattern in question_patterns:
                if re.search(pattern, text): score += 0.4
            word_count = len(text.split())
            if word_count > 15: score += 0.2
            if 5 <= word_count <= 10: score += 0.3
            if '!' in segment['text']: score += 0.3
            if score >= 0.5:
                strong_moments.append({'timestamp': segment['start'], 'type': 'strong_phrase', 'text': segment['text'], 'score': score, 'confidence': min(score, 1.0)})
        print(f"Encontradas {len(strong_moments)} frases fortes")
        return strong_moments
    
    def llm_analyze_segments(self, segments, max_clips=5):
        if not self.use_llm: return []
        print("Analisando conteúdo com Gemini...")
        full_text = ""
        for i, seg in enumerate(segments):
            full_text += f"[{seg['start']:.1f}s] {seg['text']}\n"
        if len(full_text) > 30000: full_text = full_text[:30000]
        
        prompt = f"""Analise esta transcrição de podcast e identifique os {max_clips} momentos MAIS INTERESSANTES para criar clips virais.
        Responda APENAS com um JSON array no formato:
        [
          {{"timestamp": 123.5, "reason": "motivo", "duration": 50, "text": "transcrição do trecho"}},
          ...
        ]
        Transcrição:
        {full_text}
        """
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            import json
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                llm_moments = json.loads(json_match.group())
                return [{
                    'timestamp': m['timestamp'],
                    'type': 'llm_selected',
                    'reason': m['reason'],
                    'duration': m.get('duration', 50),
                    'text': m.get('text', ''),
                    'confidence': 1.0
                } for m in llm_moments]
            return []
        except Exception as e:
            print(f"Erro Gemini: {e}")
            return []
    
    def find_best_moments(self, transcription, audio_path, max_clips=5):
        segments = transcription['segments']
        all_moments = []
        try:
            all_moments.extend(self.analyze_audio_energy(audio_path))
        except: pass
        try:
            all_moments.extend(self.detect_laughter_pauses(segments))
        except: pass
        try:
            all_moments.extend(self.analyze_text_content(segments))
        except: pass
        
        llm_moments = []
        if self.use_llm:
            llm_moments = self.llm_analyze_segments(segments, max_clips)
        
        if llm_moments:
            return llm_moments
        
        all_moments.sort(key=lambda x: x['timestamp'])
        grouped_moments = []
        for moment in all_moments:
            found = False
            for group in grouped_moments:
                if abs(group['timestamp'] - moment['timestamp']) < 5.0:
                    group['score'] = group.get('score', 0) + moment.get('confidence', 0.5)
                    if 'text' in moment: group['text'] = group.get('text', '') + " " + moment['text']
                    found = True
                    break
            if not found:
                grouped_moments.append({'timestamp': moment['timestamp'], 'score': moment.get('confidence', 0.5), 'text': moment.get('text', ''), 'duration': 50})
        
        grouped_moments.sort(key=lambda x: x['score'], reverse=True)
        best_moments = grouped_moments[:max_clips]
        for m in best_moments:
            m['type'] = 'heuristic_selected'
            m['reason'] = "Detectado por heurísticas"
        return best_moments
