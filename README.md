# Media Downloader CLI (yt-dlp wrapper)

**Descrição curta:**  
Script CLI em Python que identifica se uma URL tem vídeo ou só áudio e baixa a mídia.  
Vídeos são salvos como `.mp4` (quando possível). Áudios são extraídos e salvos como `.mp3`.

> **AVISO LEGAL:** Use apenas para conteúdo que você tem permissão para baixar. Não use para contornar DRM ou paywalls.

---

## Requisitos
- Python 3.8+ (testado com 3.10)
- `yt-dlp` (biblioteca/CLI)
- `ffmpeg` instalado no sistema (necessário para mux/convert)

### Instalando no Linux (Debian/Ubuntu)
```bash
sudo apt update
sudo apt install -y ffmpeg python3 python3-venv python3-pip
python3 -m pip install --upgrade pip
python3 -m pip install yt-dlp

### macOS (Homebrew)
brew install ffmpeg python
python3 -m pip install --upgrade pip
python3 -m pip install yt-dlp

### Windows (PowerShell / Admin)
Instale ffmpeg (ex.: via choco install ffmpeg se usar Chocolatey) ou baixe release do site do ffmpeg e adicione ao PATH.

Instale Python 3 e depois:

python -m pip install --upgrade pip
python -m pip install yt-dlp

### Instalação do projeto

Salve md-load.py em uma pasta.
Torne executável (Linux/macOS):
chmod +x downloader_cli.py


(ou execute com python downloader_cli.py ...)

# Uso

## Exemplos básicos:

### Baixar uma URL (será perguntado confirmação):

./md-load.py "https://exemplo.com/alguma-pagina"


### Baixar e não perguntar (assume que você tem permissão):

./md-load.py --yes "https://exemplo.com/alguma-pagina"


### Especificar diretório de saída:

./md-load.py -o meus_downloads "https://exemplo.com/alguma-pagina"


# Comportamento:

- Para itens com vídeo: tenta bestvideo+bestaudio e mescla em .mp4 (usa ffmpeg).
- Para áudio-only: baixa melhor áudio e converte para .mp3 (192 kbps por padrão).
- Se a URL for uma playlist, processa cada entrada.

# Observações & Limitações
- O script não tenta contornar DRM, paywalls, nem fornece métodos para obter conteúdo protegido ilegalmente.
- A qualidade final depende do que o site/servidor oferece.
- Para sites muito específicos ou se tiver problemas, pode ser necessário ajustes em opções do yt-dlp.
- Se quiser saída verbosa para debug, remova/comment a opção quiet nas opções de YoutubeDL no código-fonte.
