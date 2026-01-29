# 🎬 Podcast Clipper

**Sistema automático de geração de clips virais para redes sociais**

Transforme seus podcasts em clips verticais otimizados para YouTube Shorts, Instagram Reels e TikTok com legendas automáticas e detecção inteligente de momentos interessantes.

---

## 🚀 Funcionalidades

### ✨ Principais Recursos

- **Transcrição Automática**: Utiliza OpenAI Whisper para transcrever o áudio com alta precisão
- **Detecção Inteligente de Momentos**: Identifica automaticamente os melhores momentos usando:
  - Análise de energia do áudio (picos de emoção)
  - Detecção de risadas e pausas
  - Análise de frases impactantes
  - IA (LLM) para análise semântica avançada
- **Formato Vertical**: Converte automaticamente para 1080x1920 (formato ideal para redes sociais)
- **Legendas Automáticas**: Dois estilos disponíveis:
  - **Palavra por palavra** (estilo viral - recomendado)
  - **Frases completas** (estilo tradicional)
- **Exportação Pronta**: Vídeos prontos para upload direto nas redes sociais

---

## 📋 Requisitos

### Sistema
- Python 3.8 ou superior
- FFmpeg instalado no sistema
- 4GB+ de RAM (8GB+ recomendado para vídeos longos)
- GPU (opcional, acelera a transcrição)

### Dependências Python
```bash
pip install openai-whisper ffmpeg-python moviepy numpy scipy pydub
```

---

## 🛠️ Instalação

### 1. Clone ou baixe o projeto

```bash
cd /home/ubuntu/podcast-clipper
```

### 2. Instale as dependências

```bash
sudo pip3 install openai-whisper ffmpeg-python moviepy numpy scipy pydub
```

### 3. Verifique a instalação do FFmpeg

```bash
ffmpeg -version
```

Se não estiver instalado:
```bash
sudo apt update && sudo apt install ffmpeg -y  # Ubuntu/Debian
```

---

## 📖 Como Usar

### Uso Básico

```bash
python podcast_clipper.py seu_video.mp4
```

Este comando irá:
- Processar o vídeo
- Gerar 5 clips dos melhores momentos
- Adicionar legendas palavra por palavra (estilo viral)
- Salvar os clips na pasta `output/`

### Opções Avançadas

```bash
# Gerar 3 clips com legendas em frases completas
python podcast_clipper.py meu_podcast.mp4 --max-clips 3 --subtitle-style phrase

# Usar modelo Whisper maior para melhor precisão (mais lento)
python podcast_clipper.py meu_podcast.mp4 --whisper-model medium

# Desabilitar análise LLM (mais rápido, mas menos preciso)
python podcast_clipper.py meu_podcast.mp4 --no-llm

# Ver todas as opções disponíveis
python podcast_clipper.py --help
```

### Parâmetros Disponíveis

| Parâmetro | Descrição | Padrão |
|-----------|-----------|--------|
| `video` | Caminho do vídeo de entrada (obrigatório) | - |
| `--max-clips` | Número máximo de clips a gerar | 5 |
| `--subtitle-style` | Estilo das legendas: `word` ou `phrase` | `word` |
| `--whisper-model` | Modelo Whisper: `tiny`, `base`, `small`, `medium`, `large` | `base` |
| `--no-llm` | Desabilitar análise com IA (usa apenas heurísticas) | False |
| `--no-save-transcription` | Não salvar arquivo de transcrição | False |

---

## 📁 Estrutura de Arquivos

```
podcast-clipper/
├── podcast_clipper.py          # Script principal
├── modules/                     # Módulos do sistema
│   ├── audio_processor.py      # Extração e transcrição de áudio
│   ├── moment_detector.py      # Detecção de momentos interessantes
│   └── video_clipper.py        # Geração de clips com legendas
├── output/                      # Clips gerados (criado automaticamente)
├── temp/                        # Arquivos temporários (criado automaticamente)
└── README.md                    # Esta documentação
```

---

## 🎯 Como Funciona

### Fluxo de Processamento

```
1. EXTRAÇÃO DE ÁUDIO
   ├─ Extrai áudio do vídeo usando FFmpeg
   └─ Converte para formato otimizado (16kHz, mono)

2. TRANSCRIÇÃO
   ├─ Transcreve usando Whisper (OpenAI)
   └─ Gera timestamps palavra por palavra

3. DETECÇÃO DE MOMENTOS
   ├─ Análise de energia do áudio (picos de volume/emoção)
   ├─ Detecção de risadas e pausas
   ├─ Análise de frases impactantes (palavras-chave, perguntas)
   └─ Análise semântica com LLM (opcional, mas recomendado)

4. GERAÇÃO DE CLIPS
   ├─ Corta os melhores momentos (45-60 segundos)
   ├─ Converte para formato vertical (1080x1920)
   ├─ Adiciona legendas automáticas sincronizadas
   └─ Exporta vídeos prontos para redes sociais
```

### Critérios de Detecção

O sistema identifica momentos interessantes baseado em:

- **Picos de Emoção**: Aumento súbito de volume/energia
- **Risadas**: Detecção de padrões de risada na transcrição
- **Pausas Dramáticas**: Silêncios estratégicos (>2 segundos)
- **Frases Impactantes**: Palavras-chave como "incrível", "nunca", "segredo", etc.
- **Perguntas Provocativas**: Perguntas abertas que geram curiosidade
- **Análise Semântica**: IA analisa o contexto e identifica os momentos mais virais

---

## 🎨 Estilos de Legendas

### Palavra por Palavra (Recomendado)
- Estilo viral usado em TikTok/Reels
- Cada palavra aparece individualmente
- Texto grande, amarelo com contorno preto
- Sincronização perfeita com a fala

### Frases Completas
- Estilo tradicional de legendas
- Frases aparecem por segmento
- Texto branco com contorno preto
- Mais legível para conteúdo denso

---

## ⚙️ Modelos Whisper

| Modelo | Tamanho | Velocidade | Precisão | Uso Recomendado |
|--------|---------|------------|----------|-----------------|
| `tiny` | 39 MB | Muito rápido | Básica | Testes rápidos |
| `base` | 74 MB | Rápido | Boa | **Uso geral (padrão)** |
| `small` | 244 MB | Médio | Muito boa | Qualidade superior |
| `medium` | 769 MB | Lento | Excelente | Produção profissional |
| `large` | 1550 MB | Muito lento | Máxima | Máxima precisão |

---

## 📊 Arquivos de Saída

Após o processamento, você encontrará na pasta `output/`:

### Clips de Vídeo
- `{nome_video}_clip_01.mp4`
- `{nome_video}_clip_02.mp4`
- ... (até o número de clips solicitado)

### Arquivos de Informação
- `{nome_video}_clips_info.json` - Metadados sobre os clips gerados
- `{nome_video}_transcription.json` - Transcrição completa com timestamps

### Exemplo de clips_info.json
```json
{
  "video_source": "/path/to/video.mp4",
  "video_name": "meu_podcast",
  "clips_generated": 5,
  "subtitle_style": "word",
  "moments": [
    {
      "timestamp": 125.3,
      "duration": 50,
      "reason": "Frase impactante sobre empreendedorismo",
      "type": "llm_selected"
    }
  ],
  "clips": [
    "/path/to/output/meu_podcast_clip_01.mp4"
  ]
}
```

---

## 🔧 Solução de Problemas

### Erro: "FFmpeg not found"
```bash
# Instale o FFmpeg
sudo apt update && sudo apt install ffmpeg -y
```

### Erro: "Out of memory"
- Use um modelo Whisper menor (`--whisper-model tiny`)
- Processe vídeos mais curtos
- Aumente a RAM disponível

### Clips sem legendas
- Verifique se a transcrição foi bem-sucedida
- Tente um modelo Whisper maior para melhor precisão
- Verifique se o idioma está correto (padrão: português)

### Qualidade de vídeo ruim
- O sistema mantém a qualidade original do vídeo
- Para melhor qualidade, use vídeos fonte em alta resolução
- O crop para vertical pode afetar enquadramento - grave com isso em mente

---

## 💡 Dicas para Melhores Resultados

### Gravação
- **Grave em alta resolução** (1080p ou superior)
- **Enquadramento centralizado** (o crop vertical pega o centro)
- **Áudio limpo** (sem ruídos de fundo excessivos)
- **Fale claramente** (facilita a transcrição)

### Processamento
- **Use análise LLM** para melhores seleções de momentos
- **Modelo Whisper `base`** é um bom equilíbrio velocidade/qualidade
- **Legendas palavra por palavra** funcionam melhor para conteúdo viral
- **3-5 clips** é ideal para não saturar seu público

### Pós-Produção
- Revise os clips gerados antes de publicar
- Adicione thumbnails atraentes
- Teste diferentes momentos se necessário
- Ajuste `--max-clips` para gerar mais opções

---

## 🚀 Exemplos de Uso

### Caso 1: Podcast Completo (1 hora)
```bash
python podcast_clipper.py podcast_ep42.mp4 --max-clips 5 --whisper-model base
```
**Resultado**: 5 clips dos melhores momentos, prontos para publicar

### Caso 2: Entrevista Curta (15 minutos)
```bash
python podcast_clipper.py entrevista.mp4 --max-clips 3 --subtitle-style phrase
```
**Resultado**: 3 clips com legendas tradicionais

### Caso 3: Processamento Rápido (sem LLM)
```bash
python podcast_clipper.py video.mp4 --no-llm --whisper-model tiny
```
**Resultado**: Processamento mais rápido, mas seleção menos precisa

### Caso 4: Máxima Qualidade
```bash
python podcast_clipper.py podcast.mp4 --whisper-model large --max-clips 10
```
**Resultado**: Transcrição perfeita, 10 clips dos melhores momentos

---

## 📝 Notas Técnicas

### Formato de Saída
- **Resolução**: 1080x1920 (vertical)
- **Codec de vídeo**: H.264 (libx264)
- **Codec de áudio**: AAC
- **FPS**: 30
- **Bitrate**: Automático (baseado no vídeo original)

### Requisitos de API
- Se usar análise LLM, é necessário ter a variável de ambiente `OPENAI_API_KEY` configurada
- O sistema usa o modelo `gpt-4.1-mini` por padrão
- Sem LLM (`--no-llm`), o sistema funciona 100% offline

### Privacidade
- Todo processamento é local (exceto análise LLM opcional)
- Nenhum vídeo é enviado para servidores externos
- Arquivos temporários são mantidos em `temp/` e podem ser deletados

---

## 🤝 Contribuindo

Sugestões de melhorias:
- Adicionar mais estilos de legendas
- Suporte para múltiplos idiomas
- Interface gráfica (GUI)
- Detecção de faces para melhor enquadramento
- Filtros e efeitos visuais
- Integração com APIs de redes sociais para upload automático

---

## 📄 Licença

Este projeto é fornecido como está, para uso pessoal e comercial.

---

## 🆘 Suporte

Para problemas ou dúvidas:
1. Verifique a seção "Solução de Problemas" acima
2. Revise os logs de erro gerados pelo sistema
3. Teste com um vídeo menor para isolar o problema
4. Verifique se todas as dependências estão instaladas corretamente

---

## 🎉 Comece Agora!

```bash
# Exemplo rápido para testar
python podcast_clipper.py seu_primeiro_video.mp4
```

Seus clips estarão prontos em `output/` em alguns minutos! 🚀

---

**Desenvolvido para criadores de conteúdo que querem maximizar o alcance de seus podcasts nas redes sociais.**
