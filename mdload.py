#!/usr/bin/env python3
# coding: utf-8
"""
mdload.py

CLI que identifica e baixa mídias a partir de uma URL.
- Vídeo -> tenta salvar como .mp4
- Áudio -> extrai e converte para .mp3

Novidades nesta versão:
- --verbose : saída mais verbosa (mostra progresso/erros do yt-dlp)
- --cookies : aceita um arquivo de cookies (formato Netscape / cookies.txt) para autenticação
- --username / --password : para sites que usam autenticação HTTP/forma
- --headers : JSON string com cabeçalhos HTTP adicionais (ex: '{"Authorization":"Bearer ..."}')

AVISO: só use para conteúdo que você tem permissão para baixar. Não ajude a contornar DRM.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional
from yt_dlp import YoutubeDL

# -------------------------
# Funções utilitárias
# -------------------------

def parse_headers(headers_str: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Recebe uma string JSON com pares chave:valor e retorna dict ou None em caso vazio.
    Exemplo: '{"Authorization":"Bearer TOKEN", "User-Agent":"MyAgent/1.0"}'
    """
    if not headers_str:
        return None
    try:
        parsed = json.loads(headers_str)
        if isinstance(parsed, dict):
            # Garantir que todos os valores são strings
            return {str(k): str(v) for k, v in parsed.items()}
        else:
            print("ERRO: --headers deve ser um JSON object (ex: '{\"Header\":\"Value\"}').", file=sys.stderr)
            return None
    except json.JSONDecodeError as e:
        print(f"ERRO ao parsear --headers JSON: {e}", file=sys.stderr)
        return None

def has_video(info: Dict[str, Any]) -> bool:
    """
    Decide se o item tem vídeo:
    - Verifica 'formats' por vcodec != 'none'
    - Fallback: checa presença de width/height/is_live
    """
    formats = info.get('formats') or []
    for f in formats:
        vcodec = f.get('vcodec')
        if vcodec and vcodec != 'none':
            return True
    if info.get('is_live') or info.get('width') or info.get('height'):
        return True
    return False

def build_base_opts(outdir: str, quiet: bool, cookiefile: Optional[str],
                    username: Optional[str], password: Optional[str],
                    headers: Optional[Dict[str,str]]) -> Dict[str, Any]:
    """
    Retorna opções base para YoutubeDL de acordo com parâmetros.
    - quiet: reduz a verbosidade (quando False, mostra progresso e logs)
    - cookiefile: caminho para arquivo de cookies (Netscape cookies.txt)
    - us/pwd: (onde aplicável)
    - headers: dict de cabeçalhos HTTP para passar via 'http_headers'
    """
    opts: Dict[str, Any] = {
        # controlos de saída/feedback
        'quiet': quiet,
        'no_warnings': quiet,
        # template de saída padrão (ext será ajustada por postprocessors/merge)
        'outtmpl': os.path.join(outdir, '%(title)s - %(id)s.%(ext)s'),
        # evita falha completa em entradas individuais de playlists
        'ignoreerrors': True,
    }

    # Cookies: yt-dlp aceita 'cookiefile' option
    if cookiefile:
        opts['cookiefile'] = cookiefile

    # Credenciais
    if username:
        opts['username'] = username
    if password:
        opts['password'] = password

    # Headers (ex: Authorization)
    if headers:
        opts['http_headers'] = headers

    return opts

def download_entries(info_or_url: Any, outdir: str, verbose: bool,
                     cookiefile: Optional[str], username: Optional[str],
                     password: Optional[str], headers: Optional[Dict[str,str]]) -> None:
    """
    Recebe o resultado de extract_info (ou uma url) e processa as entradas.
    Para cada entry decide vídeo vs áudio e executa o download correspondente.
    """
    # Decide quiet baseado em verbose
    quiet = not verbose

    # Se recebeu uma URL simples em vez de info dict, primeiro extraí info sem baixar
    base_opts = build_base_opts(outdir, quiet, cookiefile, username, password, headers)

    # Se info_or_url for dict vindo de extract_info já, use-o; caso contrário, trate como URL e extraia
    initial_info = None
    if isinstance(info_or_url, dict):
        initial_info = info_or_url
    else:
        try:
            with YoutubeDL(base_opts) as ydl:
                initial_info = ydl.extract_info(info_or_url, download=False)
        except Exception as e:
            print(f"Erro ao extrair informações iniciais da URL: {e}", file=sys.stderr)
            return

    if not initial_info:
        print("Nenhuma informação foi obtida da URL.", file=sys.stderr)
        return

    # Normalize entries (se playlist, iterar entries)
    entries: List[Dict[str, Any]] = []
    if isinstance(initial_info, dict) and initial_info.get('entries'):
        for e in initial_info.get('entries') or []:
            if e:
                entries.append(e)
    else:
        entries.append(initial_info)

    # Processa cada entrada
    for entry in entries:
        if not entry:
            continue
        entry_url = entry.get('webpage_url') or entry.get('url')
        title = entry.get('title') or entry.get('id') or 'untitled'
        print(f"\nProcessando: {title}")

        # Decide se tem vídeo
        try:
            # Em alguns casos entry não tem 'formats' até que extract_info seja chamado novamente.
            # Vamos extrair info detalhado se necessário.
            detailed_info = entry
            if not entry.get('formats'):
                # Obter info detalhado para essa entry
                with YoutubeDL(base_opts) as ydl:
                    detailed_info = ydl.extract_info(entry_url or entry.get('id'), download=False)
            is_video = has_video(detailed_info)
        except Exception as e:
            print(f"Erro ao analisar formats do item: {e}. Tentando fallback assumindo vídeo.", file=sys.stderr)
            is_video = True

        # Monta opções específicas para vídeo ou áudio
        opts = build_base_opts(outdir, quiet, cookiefile, username, password, headers)

        if is_video:
            print(" -> Tipo detectado: VÍDEO. Baixando melhor vídeo + áudio e mesclando em .mp4 (quando possível).")
            opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                # Assegura conversão para mp4 se necessário
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4'
                    }
                ],
            })
        else:
            print(" -> Tipo detectado: ÁUDIO. Baixando áudio e convertendo para .mp3 (192 kbps).")
            opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }
                ],
            })

        # Se verbose, deixar yt-dlp mostrar progresso (quiet já reflete isso)
        try:
            with YoutubeDL(opts) as ydl:
                ydl.download([entry_url])
            print(" --> Concluído.")
        except Exception as e:
            print(f"Erro durante o download/processing: {e}", file=sys.stderr)

# -------------------------
# CLI
# -------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Baixa mídias (vídeo -> mp4, áudio -> mp3) a partir de uma URL. Use apenas para conteúdo legal."
    )
    parser.add_argument('url', help='URL da página/stream/playlist a baixar')
    parser.add_argument('-o', '--outdir', default='downloads', help='Diretório de saída')
    parser.add_argument('--yes', action='store_true', help='Assume que você tem permissão (não pergunta)')
    parser.add_argument('--verbose', action='store_true', help='Saída verbosa (mostra progresso e logs do yt-dlp)')
    parser.add_argument('--cookies', help='Arquivo de cookies (Netscape cookies.txt) para autenticação')
    parser.add_argument('--username', help='Username para autenticação (quando aplicável)')
    parser.add_argument('--password', help='Password para autenticação (quando aplicável)')
    parser.add_argument('--headers', help='JSON string com cabeçalhos HTTP adicionais (ex: \'{"Authorization":"Bearer ..."}\')')
    args = parser.parse_args()

    url = args.url
    outdir = os.path.abspath(args.outdir)
    os.makedirs(outdir, exist_ok=True)

    # Parse headers JSON, se fornecido
    headers = parse_headers(args.headers)
    if args.headers and headers is None:
        # parse_headers prints o erro; aborta
        sys.exit(1)

    # Aviso legal — requer confirmação, salvo se --yes
    legal_notice = (
        "ATENÇÃO: você declara que tem direito/legalidade para baixar o conteúdo desta URL.\n"
        "Não use para contornar DRM, paywalls ou baixar conteúdo protegido sem autorização."
    )
    print(legal_notice)
    if not args.yes:
        resp = input("Deseja continuar? [y/N]: ").strip().lower()
        if resp not in ('y', 'yes'):
            print("Operação cancelada.")
            sys.exit(1)

    # Informações sobre autenticação (feedback direto, sem expor senhas)
    if args.cookies:
        if not os.path.isfile(args.cookies):
            print(f"ERRO: arquivo de cookies não encontrado: {args.cookies}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"Usando cookies a partir de: {args.cookies}")
    if args.username:
        print("Usando autenticação por usuário/senha (password não será exibida).")

    # Executa
    download_entries(url, outdir, args.verbose, args.cookies, args.username, args.password, headers)


if __name__ == '__main__':
    main()
