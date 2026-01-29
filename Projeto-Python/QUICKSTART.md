# 🚀 Guia de Início Rápido

## Instalação em 3 Passos

### 1. Instale as dependências
```bash
sudo pip3 install -r requirements.txt
```

### 2. Verifique o FFmpeg
```bash
ffmpeg -version
```

Se não estiver instalado:
```bash
sudo apt install ffmpeg -y  # Ubuntu/Debian
```

### 3. Configure a API OpenAI (opcional, mas recomendado)
```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

**Nota**: Sem a chave da API, o sistema ainda funciona usando apenas heurísticas (use `--no-llm`).

---

## Primeiro Uso

### Comando Básico
```bash
python podcast_clipper.py seu_video.mp4
```

Isso irá:
- ✅ Transcrever o áudio automaticamente
- ✅ Detectar os 5 melhores momentos
- ✅ Gerar clips verticais (1080x1920)
- ✅ Adicionar legendas palavra por palavra
- ✅ Salvar tudo na pasta `output/`

---

## Exemplos Rápidos

### Gerar 3 clips rápidos
```bash
python podcast_clipper.py video.mp4 --max-clips 3
```

### Legendas em frases (estilo tradicional)
```bash
python podcast_clipper.py video.mp4 --subtitle-style phrase
```

### Sem usar IA (mais rápido)
```bash
python podcast_clipper.py video.mp4 --no-llm
```

### Máxima qualidade
```bash
python podcast_clipper.py video.mp4 --whisper-model large
```

---

## Estrutura de Saída

Após processar, você encontrará em `output/`:

```
output/
├── seu_video_clip_01.mp4       # Clip 1 (pronto para publicar)
├── seu_video_clip_02.mp4       # Clip 2
├── seu_video_clip_03.mp4       # Clip 3
├── ...
├── seu_video_clips_info.json   # Metadados dos clips
└── seu_video_transcription.json # Transcrição completa
```

---

## Dicas Importantes

### ✅ Melhores Práticas
- Use vídeos em **alta resolução** (1080p+)
- Grave com **enquadramento centralizado**
- Mantenha **áudio limpo** sem ruídos
- Use **análise LLM** para melhores resultados

### ⚡ Performance
- **Modelo `base`**: Bom equilíbrio (recomendado)
- **Modelo `tiny`**: Mais rápido, menos preciso
- **Modelo `large`**: Mais lento, máxima precisão
- **Sem LLM**: Processamento 100% local e mais rápido

### 📱 Formato de Saída
- **Resolução**: 1080x1920 (vertical)
- **Formato**: MP4 (H.264 + AAC)
- **Duração**: 45-60 segundos por clip
- **Legendas**: Embutidas no vídeo

---

## Solução Rápida de Problemas

### Erro: "FFmpeg not found"
```bash
sudo apt install ffmpeg -y
```

### Erro: "Out of memory"
```bash
# Use modelo menor
python podcast_clipper.py video.mp4 --whisper-model tiny
```

### Sem legendas nos clips
```bash
# Tente modelo maior
python podcast_clipper.py video.mp4 --whisper-model medium
```

---

## Próximos Passos

1. **Revise os clips** gerados em `output/`
2. **Escolha os melhores** para publicar
3. **Adicione thumbnails** atraentes
4. **Publique** no YouTube Shorts, Instagram Reels ou TikTok
5. **Analise** o engajamento e ajuste os parâmetros

---

## Ajuda Completa

Para documentação completa, veja [README.md](README.md)

Para ver todas as opções:
```bash
python podcast_clipper.py --help
```

---

**Pronto para criar seus primeiros clips virais? 🎬**

```bash
python podcast_clipper.py seu_podcast.mp4
```
