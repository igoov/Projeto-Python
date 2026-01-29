# 📊 Visão Geral do Sistema - Podcast Clipper

## Arquitetura do Sistema

O **Podcast Clipper** é um sistema modular dividido em três componentes principais:

```
┌─────────────────────────────────────────────────────────────┐
│                    PODCAST CLIPPER                          │
│                   (podcast_clipper.py)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │         PIPELINE DE PROCESSAMENTO        │
        └─────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│   MÓDULO 1   │    │    MÓDULO 2      │    │   MÓDULO 3   │
│    ÁUDIO     │───▶│    DETECÇÃO      │───▶│    VÍDEO     │
│  PROCESSOR   │    │   DE MOMENTOS    │    │   CLIPPER    │
└──────────────┘    └──────────────────┘    └──────────────┘
      │                     │                       │
      ▼                     ▼                       ▼
  Transcrição          Momentos               Clips Verticais
   + Áudio           Interessantes            com Legendas
```

---

## Módulos Detalhados

### 1️⃣ Audio Processor (`audio_processor.py`)

**Responsabilidade**: Extrair e transcrever áudio de vídeos

**Tecnologias**:
- FFmpeg (extração de áudio)
- OpenAI Whisper (transcrição)

**Funcionalidades**:
- Extração de áudio em formato otimizado (16kHz, mono)
- Transcrição com timestamps palavra por palavra
- Suporte a múltiplos idiomas
- Salvamento de transcrição em JSON

**Entrada**: Vídeo (MP4, MOV, AVI, etc.)  
**Saída**: Arquivo de áudio (WAV) + Transcrição (JSON)

---

### 2️⃣ Moment Detector (`moment_detector.py`)

**Responsabilidade**: Identificar momentos interessantes para clips

**Tecnologias**:
- Pydub (análise de áudio)
- NumPy/SciPy (processamento de sinais)
- OpenAI GPT (análise semântica)

**Métodos de Detecção**:

#### A. Análise de Energia do Áudio
- Detecta picos de volume/emoção
- Identifica momentos de alta energia
- Usa percentil 75 como threshold

#### B. Detecção de Risadas e Pausas
- Padrões regex para risadas (haha, kkkk, rsrs)
- Pausas longas (>2 segundos)
- Indicadores de momentos descontraídos

#### C. Análise de Conteúdo Textual
- Palavras-chave impactantes
- Perguntas provocativas
- Frases curtas e marcantes
- Exclamações

#### D. Análise Semântica com LLM
- Compreensão contextual profunda
- Identificação de histórias interessantes
- Detecção de insights valiosos
- Ranqueamento por potencial viral

**Entrada**: Transcrição + Áudio  
**Saída**: Lista de momentos ranqueados com timestamps

---

### 3️⃣ Video Clipper (`video_clipper.py`)

**Responsabilidade**: Gerar clips verticais com legendas

**Tecnologias**:
- MoviePy (edição de vídeo)
- FFmpeg (renderização)

**Funcionalidades**:

#### A. Conversão para Formato Vertical
- Crop inteligente (centralizado)
- Redimensionamento para 1080x1920
- Preservação de qualidade

#### B. Geração de Legendas
- **Estilo "Word"** (palavra por palavra):
  - Texto grande, amarelo, contorno preto
  - Sincronização perfeita
  - Estilo viral TikTok/Reels
  
- **Estilo "Phrase"** (frases completas):
  - Texto branco, contorno preto
  - Legendas por segmento
  - Estilo tradicional

#### C. Exportação Otimizada
- Codec H.264 (compatibilidade universal)
- Áudio AAC
- 30 FPS
- Preset "medium" (equilíbrio qualidade/velocidade)

**Entrada**: Vídeo + Transcrição + Momentos  
**Saída**: Clips MP4 verticais com legendas

---

## Fluxo de Dados

```
┌──────────────┐
│ Vídeo Input  │
│  (podcast)   │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  1. EXTRAÇÃO DE ÁUDIO                   │
│  ─────────────────────                  │
│  • FFmpeg extrai áudio                  │
│  • Converte para 16kHz mono             │
│  • Salva como WAV                       │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  2. TRANSCRIÇÃO                         │
│  ────────────                           │
│  • Whisper processa áudio               │
│  • Gera texto + timestamps              │
│  • Salva JSON com segmentos             │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  3. ANÁLISE DE MOMENTOS                 │
│  ────────────────────                   │
│  • Análise de energia (áudio)           │
│  • Detecção de risadas/pausas (texto)   │
│  • Análise de frases (texto)            │
│  • Análise semântica (LLM)              │
│  • Ranqueamento e seleção               │
└──────┬──────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────┐
│  4. GERAÇÃO DE CLIPS                    │
│  ─────────────────                      │
│  Para cada momento:                     │
│  • Extrai subclip (45-60s)              │
│  • Converte para vertical               │
│  • Adiciona legendas sincronizadas      │
│  • Exporta MP4 final                    │
└──────┬──────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ Clips Finais │
│  (output/)   │
└──────────────┘
```

---

## Decisões de Design

### Por que Whisper?
- **Precisão**: Estado da arte em transcrição
- **Timestamps**: Suporte nativo a word-level timestamps
- **Multilíngue**: Suporta 99+ idiomas
- **Open Source**: Gratuito e rodável localmente

### Por que LLM para Detecção?
- **Contexto**: Entende nuances semânticas
- **Qualidade**: Identifica momentos realmente interessantes
- **Flexibilidade**: Adaptável a diferentes estilos de conteúdo
- **Opcional**: Sistema funciona sem LLM (heurísticas)

### Por que MoviePy?
- **Pythônico**: API simples e intuitiva
- **Completo**: Suporta todas as operações necessárias
- **Legendas**: Fácil criação de TextClips
- **FFmpeg**: Usa FFmpeg por baixo (performance)

### Por que Formato Vertical?
- **Redes Sociais**: Otimizado para Shorts/Reels/TikTok
- **Engajamento**: Formato preferido em mobile
- **Alcance**: Maior visibilidade nas plataformas

---

## Configurações e Parâmetros

### Modelos Whisper

| Modelo   | RAM    | VRAM  | Velocidade | Precisão |
|----------|--------|-------|------------|----------|
| tiny     | ~1 GB  | ~1 GB | 32x        | ~       |
| base     | ~1 GB  | ~1 GB | 16x        | ~+      |
| small    | ~2 GB  | ~2 GB | 6x         | ~++     |
| medium   | ~5 GB  | ~5 GB | 2x         | ~+++    |
| large    | ~10 GB | ~10 GB| 1x         | ~++++   |

### Duração dos Clips
- **Mínimo**: 30 segundos
- **Padrão**: 45-60 segundos
- **Máximo**: 90 segundos (limite das plataformas)
- **Padding**: +2 segundos antes/depois (contexto)

### Resolução de Vídeo
- **Entrada**: Qualquer (recomendado 1080p+)
- **Saída**: 1080x1920 (vertical)
- **Aspect Ratio**: 9:16

### Legendas
- **Posição**: 75-80% da altura (parte inferior)
- **Margem**: 50px de cada lado
- **Fonte**: Arial Bold
- **Tamanho**: 80px (word), 50px (phrase)

---

## Performance e Otimizações

### Tempo de Processamento Estimado

Para um vídeo de **1 hora**:

| Etapa              | Tempo (base) | Tempo (large) |
|--------------------|--------------|---------------|
| Extração de áudio  | ~10s         | ~10s          |
| Transcrição        | ~5 min       | ~20 min       |
| Detecção (sem LLM) | ~30s         | ~30s          |
| Detecção (com LLM) | ~1 min       | ~1 min        |
| Geração de 5 clips | ~5 min       | ~5 min        |
| **TOTAL**          | **~11 min**  | **~26 min**   |

*Tempos aproximados em CPU moderna (8 cores) sem GPU*

### Otimizações Implementadas

1. **Reutilização de Modelo**: Whisper carregado uma vez
2. **Processamento em Lote**: Múltiplos clips sem recarregar vídeo
3. **Preset Medium**: Equilíbrio qualidade/velocidade no FFmpeg
4. **Threads**: 4 threads para renderização
5. **Cache**: Transcrição salva para reprocessamento

---

## Extensibilidade

### Adicionar Novo Método de Detecção

```python
# Em moment_detector.py
def detect_custom_moments(self, segments):
    """Seu método personalizado"""
    moments = []
    # Sua lógica aqui
    return moments

# Em find_best_moments()
custom_moments = self.detect_custom_moments(segments)
all_moments.extend(custom_moments)
```

### Adicionar Novo Estilo de Legenda

```python
# Em video_clipper.py
def create_custom_subtitle(self, text, start, duration, video_size):
    """Seu estilo personalizado"""
    txt_clip = TextClip(
        text,
        fontsize=60,
        color='blue',
        # Suas configurações
    )
    return txt_clip

# Em add_subtitles()
elif style == 'custom':
    txt_clip = self.create_custom_subtitle(...)
```

### Adicionar Pós-Processamento

```python
# Em video_clipper.py, após criar clip
clip = self.add_effects(clip)  # Filtros, transições, etc.
```

---

## Limitações Conhecidas

1. **Memória**: Vídeos muito longos (>3h) podem causar problemas
2. **Idioma**: Otimizado para português, mas funciona em outros idiomas
3. **Enquadramento**: Crop centralizado pode não ser ideal para todos os casos
4. **Qualidade**: Limitada pela qualidade do vídeo original
5. **Contexto**: Clips podem perder contexto do episódio completo

---

## Roadmap Futuro

### Curto Prazo
- [ ] Interface gráfica (GUI)
- [ ] Detecção de faces para crop inteligente
- [ ] Mais estilos de legendas
- [ ] Suporte a múltiplos idiomas simultâneos

### Médio Prazo
- [ ] Análise de sentimento
- [ ] Geração de thumbnails automáticas
- [ ] Suporte a múltiplas câmeras
- [ ] Efeitos visuais e transições

### Longo Prazo
- [ ] Upload automático para redes sociais
- [ ] Análise de performance dos clips
- [ ] Recomendações baseadas em métricas
- [ ] API REST para integração

---

## Conclusão

O **Podcast Clipper** é um sistema robusto e modular que automatiza o processo de criação de clips virais para redes sociais. Com uma arquitetura bem definida e tecnologias de ponta, oferece resultados de alta qualidade com mínima intervenção manual.

**Principais Vantagens**:
- ✅ Totalmente automatizado
- ✅ Alta precisão na detecção
- ✅ Legendas sincronizadas
- ✅ Formato otimizado para redes sociais
- ✅ Extensível e customizável
- ✅ Open source e gratuito

---

Para mais informações, consulte:
- [README.md](README.md) - Documentação completa
- [QUICKSTART.md](QUICKSTART.md) - Guia de início rápido
- [example_usage.py](example_usage.py) - Exemplos de código
