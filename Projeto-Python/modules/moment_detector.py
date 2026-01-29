"""
Módulo para detecção de momentos interessantes em podcasts
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
        Inicializa o detector de momentos interessantes
        
        Args:
            use_llm: Se True, usa LLM para análise semântica do conteúdo
        """
        self.use_llm = use_llm
        if use_llm:
            # Puxa a chave do seu arquivo .env
            api_key = os.getenv("GOOGLE_API_KEY")
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def analyze_audio_energy(self, audio_path):
        """
        Analisa a energia do áudio para detectar picos de emoção/volume
        
        Args:
            audio_path: Caminho do arquivo de áudio
            
        Returns:
            Lista de timestamps com alta energia
        """
        print("Analisando energia do áudio...")
        
        audio = AudioSegment.from_wav(audio_path)
        
        # Detectar segmentos não-silenciosos (onde há fala/ação)
        nonsilent_ranges = detect_nonsilent(
            audio,
            min_silence_len=500,  # 500ms de silêncio mínimo
            silence_thresh=audio.dBFS - 16  # Threshold relativo
        )
        
        # Calcular energia em janelas de 1 segundo
        chunk_length = 1000  # 1 segundo em ms
        energy_scores = []
        
        for i in range(0, len(audio), chunk_length):
            chunk = audio[i:i + chunk_length]
            if len(chunk) > 0:
                energy = chunk.dBFS
                energy_scores.append({
                    'timestamp': i / 1000.0,  # Converter para segundos
                    'energy': energy
                })
        
        # Identificar picos de energia (acima do percentil 75)
        energies = [s['energy'] for s in energy_scores]
        threshold = np.percentile(energies, 75)
        
        high_energy_moments = [
            s for s in energy_scores if s['energy'] > threshold
        ]
        
        print(f"Encontrados {len(high_energy_moments)} momentos de alta energia")
        return high_energy_moments
    
    def detect_laughter_pauses(self, segments):
        """
        Detecta risadas e pausas significativas na transcrição
        
        Args:
            segments: Segmentos da transcrição do Whisper
            
        Returns:
            Lista de momentos com risadas/pausas
        """
        print("Detectando risadas e pausas...")
        
        laughter_moments = []
        
        for i, segment in enumerate(segments):
            text = segment['text'].lower()
            
            # Padrões que indicam risada
            laughter_patterns = [
                r'\b(ha+h+a+|he+h+e+|hi+h+i+|kk+|rsrs|kkk+)\b',
                r'\[ris[ao]s?\]',
                r'\(ris[ao]s?\)',
            ]
            
            for pattern in laughter_patterns:
                if re.search(pattern, text):
                    laughter_moments.append({
                        'timestamp': segment['start'],
                        'type': 'laughter',
                        'text': segment['text'],
                        'confidence': 0.8
                    })
                    break
            
            # Detectar pausas longas entre segmentos
            if i < len(segments) - 1:
                pause_duration = segments[i + 1]['start'] - segment['end']
                if pause_duration > 2.0:  # Pausa maior que 2 segundos
                    laughter_moments.append({
                        'timestamp': segment['end'],
                        'type': 'pause',
                        'duration': pause_duration,
                        'confidence': 0.6
                    })
        
        print(f"Encontrados {len(laughter_moments)} momentos de risada/pausa")
        return laughter_moments
    
    def analyze_text_content(self, segments):
        """
        Analisa o conteúdo textual para encontrar frases impactantes
        
        Args:
            segments: Segmentos da transcrição
            
        Returns:
            Lista de momentos com frases fortes
        """
        print("Analisando conteúdo textual...")
        
        strong_moments = []
        
        # Palavras-chave que indicam conteúdo interessante
        keywords = [
            'incrível', 'impressionante', 'surpreendente', 'chocante',
            'nunca', 'sempre', 'jamais', 'todo mundo', 'ninguém',
            'segredo', 'verdade', 'mentira', 'descobri', 'revelação',
            'importante', 'fundamental', 'essencial', 'crucial',
            'problema', 'solução', 'dica', 'truque', 'hack'
        ]
        
        # Padrões de frases impactantes
        question_patterns = [
            r'\?$',  # Perguntas
            r'^(por que|como|quando|onde|o que|qual)',  # Perguntas abertas
        ]
        
        for segment in segments:
            text = segment['text'].lower().strip()
            score = 0
            
            # Verificar palavras-chave
            for keyword in keywords:
                if keyword in text:
                    score += 0.3
            
            # Verificar perguntas
            for pattern in question_patterns:
                if re.search(pattern, text):
                    score += 0.4
            
            # Frases longas (mais de 15 palavras) podem ser mais substantivas
            word_count = len(text.split())
            if word_count > 15:
                score += 0.2
            
            # Frases curtas e impactantes (5-10 palavras)
            if 5 <= word_count <= 10:
                score += 0.3
            
            # Exclamações
            if '!' in segment['text']:
                score += 0.3
            
            if score >= 0.5:  # Threshold para considerar interessante
                strong_moments.append({
                    'timestamp': segment['start'],
                    'type': 'strong_phrase',
                    'text': segment['text'],
                    'score': score,
                    'confidence': min(score, 1.0)
                })
        
        print(f"Encontradas {len(strong_moments)} frases fortes")
        return strong_moments
    
    def llm_analyze_segments(self, segments, max_clips=5):
        """
        Usa LLM para analisar semanticamente os melhores momentos
        
        Args:
            segments: Segmentos da transcrição
            max_clips: Número máximo de clips a gerar
            
        Returns:
            Lista dos melhores momentos identificados pela LLM
        """
        if not self.use_llm:
            return []
        
        print("Analisando conteúdo com LLM...")
        
        # Criar texto completo com timestamps
        full_text = ""
        for i, seg in enumerate(segments):
            full_text += f"[{seg['start']:.1f}s] {seg['text']}\n"
        
        # Limitar tamanho do texto para não exceder limites da API
        if len(full_text) > 8000:
            full_text = full_text[:8000] + "..."
        
        prompt = f"""Analise esta transcrição de podcast e identifique os {max_clips} momentos MAIS INTERESSANTES para criar clips virais de 45-60 segundos para redes sociais (Shorts/Reels/TikTok).

Critérios para momentos interessantes:
- Frases impactantes ou polêmicas
- Histórias engraçadas ou emocionantes
- Insights valiosos ou dicas práticas
- Momentos de surpresa ou revelação
- Perguntas provocativas
- Conclusões marcantes

Transcrição:
{full_text}

Responda APENAS com um JSON array contendo os {max_clips} melhores momentos, no formato:
[
  {{"timestamp": 123.5, "reason": "descrição breve do porquê este momento é interessante", "duration": 50}},
  ...
]

Importante: 
- Use o timestamp em segundos do início do momento
- A duração deve ser entre 45-60 segundos
- Ordene do mais interessante para o menos interessante
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "Você é um especialista em criar clips virais de podcasts para redes sociais."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extrair JSON da resposta
            import json
            # Tentar encontrar o array JSON na resposta
            json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
            if json_match:
                llm_moments = json.loads(json_match.group())
                
                print(f"LLM identificou {len(llm_moments)} momentos interessantes")
                
                return [{
                    'timestamp': m['timestamp'],
                    'type': 'llm_selected',
                    'reason': m['reason'],
                    'duration': m.get('duration', 50),
                    'confidence': 1.0
                } for m in llm_moments]
            else:
                print("Não foi possível extrair JSON da resposta da LLM")
                return []
                
        except Exception as e:
            print(f"Erro ao usar LLM: {e}")
            return []
    
    def find_best_moments(self, transcription, audio_path, max_clips=5):
        """
        Combina todas as análises para encontrar os melhores momentos
        
        Args:
            transcription: Dicionário com transcrição completa
            audio_path: Caminho do arquivo de áudio
            max_clips: Número máximo de clips a gerar
            
        Returns:
            Lista dos melhores momentos ranqueados
        """
        segments = transcription['segments']
        
        # Coletar momentos de diferentes análises
        all_moments = []
        
        # 1. Análise de energia do áudio
        try:
            energy_moments = self.analyze_audio_energy(audio_path)
            all_moments.extend(energy_moments)
        except Exception as e:
            print(f"Erro na análise de energia: {e}")
        
        # 2. Detecção de risadas e pausas
        try:
            laughter_moments = self.detect_laughter_pauses(segments)
            all_moments.extend(laughter_moments)
        except Exception as e:
            print(f"Erro na detecção de risadas: {e}")
        
        # 3. Análise de conteúdo textual
        try:
            text_moments = self.analyze_text_content(segments)
            all_moments.extend(text_moments)
        except Exception as e:
            print(f"Erro na análise textual: {e}")
        
        # 4. Análise com LLM (prioritária se disponível)
        llm_moments = []
        if self.use_llm:
            try:
                llm_moments = self.llm_analyze_segments(segments, max_clips)
            except Exception as e:
                print(f"Erro na análise LLM: {e}")
        
        # Se LLM retornou resultados, priorizar eles
        if llm_moments:
            print(f"\nUsando {len(llm_moments)} momentos selecionados pela LLM")
            return llm_moments
        
        # Caso contrário, ranquear momentos por heurísticas
        print("\nRanqueando momentos por heurísticas...")
        
        # Agrupar momentos próximos (dentro de 5 segundos)
        grouped_moments = []
        all_moments.sort(key=lambda x: x['timestamp'])
        
        for moment in all_moments:
            # Verificar se já existe um momento próximo
            found = False
            for group in grouped_moments:
                if abs(group['timestamp'] - moment['timestamp']) < 5.0:
                    # Atualizar score do grupo
                    group['score'] = group.get('score', 0) + moment.get('confidence', 0.5)
                    group['types'] = group.get('types', []) + [moment.get('type', 'unknown')]
                    found = True
                    break
            
            if not found:
                grouped_moments.append({
                    'timestamp': moment['timestamp'],
                    'score': moment.get('confidence', 0.5),
                    'types': [moment.get('type', 'unknown')],
                    'duration': 50  # Duração padrão
                })
        
        # Ordenar por score e pegar os top N
        grouped_moments.sort(key=lambda x: x['score'], reverse=True)
        best_moments = grouped_moments[:max_clips]
        
        # Adicionar informação sobre o tipo de momento
        for moment in best_moments:
            moment['type'] = 'heuristic_selected'
            moment['reason'] = f"Detectado: {', '.join(set(moment['types']))}"
        
        print(f"\nSelecionados {len(best_moments)} melhores momentos")
        return best_moments
