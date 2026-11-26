"""Gera copia portatil do Quiz do S.A.P.A. para qualquer notebook na pasta dist_colegas/."""

import os
import re
import shutil
import time
import zipfile
from build_data_js import build as build_data_bundle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")
INDEX_HTML = os.path.join(WEB_DIR, "index.html")
DATA_JS = os.path.join(WEB_DIR, "sapa_data.js")
EXE_SRC = os.path.join(BASE_DIR, "dist", "Quiz_do_SAPA.exe")
OUT_DIR = os.path.join(BASE_DIR, "dist_colegas")

UNIVERSAL_HTML_NAME = "Quiz_do_SAPA_Universal.html"
WINDOWS_EXE_NAME = "Quiz_do_SAPA_Windows.exe"
README_TXT_NAME = "LEIA-ME.txt"
ZIP_ANY_OS_NAME = "Quiz_do_SAPA_Qualquer_Notebook.zip"
ZIP_WITH_EXE_NAME = "Quiz_do_SAPA_Completo_Com_EXE.zip"

SCRIPT_TAG = '<script src="sapa_data.js"></script>'

LEIA_ME_CONTENT = """====================================================================
  QUIZ DO S.A.P.A. — GUARDIOES DOS RIOS (COPIA PORTATIL 100% OFF-LINE)
====================================================================

1) COMO ABRIR EM QUALQUER NOTEBOOK (Windows, MacBook, Linux, Chromebook)
   - De dois cliques no arquivo:
       Quiz_do_SAPA_Universal.html
   - Ele abre direto no navegador (Chrome, Edge, Firefox, Safari ou Brave),
     sem precisar instalar Python, sem servidor e SEM INTERNET.

2) OPCAO NATIVA PARA WINDOWS 10 / 11 (SE DISPONIVEL NA PASTA)
   - Voce tambem pode abrir diretamente:
       Quiz_do_SAPA_Windows.exe
   - Dica para WhatsApp/E-mail: envie o arquivo
       Quiz_do_SAPA_Qualquer_Notebook.zip
     (ele contem apenas o HTML unico e este guia, sem bloqueios de antivirus).

3) DICAS DE USO EM SALA DE AULA / PROJETOR
   - Pressione F11 (ou clique em "Tela Cheia") para projetar em tela cheia.
   - Escolha de 2 a 10 equipes e selecione os 10 mascotes da Amazonia
     usando as setinhas (< >) ou clicando no avatar.
   - Fase 1 (10 perguntas) com pontuacao automatica ajustada ao numero de equipes
     (descendo de 50 em 50 pontos) + Emboscada surpresa do Capitao Garrafao no
     Podio + Cutscenes HQ + Fase 2 (Boss Fight de 7 desafios valendo o DOBRO
     e devolucao em 2x dos pontos da Fase 1 ao derrotar o vilao!).

4) ATALHOS DO TECLADO (E APONTADORES DE SLIDES)
   - 1 a 4 ou A a D        : Seleciona a alternativa durante a pergunta
   - Espaco / Enter / ->   : Avanca a emboscada e os dialogos das cutscenes HQ
   - Enter / -> / PageDown : Avanca para a proxima pergunta apos revelar resposta
   - Esc                   : Fecha a janelinha de escolha de mascote
   - F11                   : Entra ou sai do modo Tela Cheia
====================================================================
"""


def build_portable() -> None:
    build_data_bundle()

    with open(INDEX_HTML, "r", encoding="utf-8") as f:
        html_src = f.read()
    with open(DATA_JS, "r", encoding="utf-8") as f:
        data_js_src = f.read()

    occurrences = html_src.count(SCRIPT_TAG)
    if occurrences != 1:
        raise RuntimeError(
            f"Esperado exatamente 1 '{SCRIPT_TAG}' em {INDEX_HTML}, encontrado {occurrences}."
        )

    universal_html = html_src.replace(
        SCRIPT_TAG,
        f"<script>\n{data_js_src}\n</script>",
        1,
    )

    if 'src="sapa_data.js"' in universal_html:
        raise AssertionError("Referencia externa sapa_data.js ainda presente no HTML portatil.")
    if "assets/" in universal_html:
        raise AssertionError("Caminho relativo 'assets/' encontrado no HTML portatil.")
    ext_urls = [u for u in re.findall(r"https?://\S+", universal_html) if "w3.org/2000/svg" not in u]
    if ext_urls:
        raise AssertionError(f"URL externa encontrada no HTML portatil: {ext_urls}")

    os.makedirs(OUT_DIR, exist_ok=True)
    universal_path = os.path.join(OUT_DIR, UNIVERSAL_HTML_NAME)
    readme_path = os.path.join(OUT_DIR, README_TXT_NAME)
    exe_dst = os.path.join(OUT_DIR, WINDOWS_EXE_NAME)
    zip_any_path = os.path.join(OUT_DIR, ZIP_ANY_OS_NAME)
    zip_exe_path = os.path.join(OUT_DIR, ZIP_WITH_EXE_NAME)

    with open(universal_path, "w", encoding="utf-8") as f:
        f.write(universal_html)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(LEIA_ME_CONTENT)

    exe_for_zip = exe_dst
    if os.path.exists(EXE_SRC) and (
        not os.path.exists(exe_dst) or os.path.getmtime(EXE_SRC) > os.path.getmtime(exe_dst)
    ):
        copied = False
        for _ in range(8):
            try:
                shutil.copy2(EXE_SRC, exe_dst)
                copied = True
                break
            except PermissionError:
                time.sleep(0.5)
        if not copied:
            exe_for_zip = EXE_SRC
    elif os.path.exists(exe_dst):
        try:
            shutil.copy2(exe_dst, EXE_SRC)
        except PermissionError:
            pass
    else:
        raise FileNotFoundError(
            f"Executavel nao encontrado em {EXE_SRC} nem em {exe_dst}. Rode o PyInstaller antes."
        )

    with zipfile.ZipFile(zip_any_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(universal_path, arcname=UNIVERSAL_HTML_NAME)
        zf.write(readme_path, arcname=README_TXT_NAME)

    with zipfile.ZipFile(zip_exe_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(universal_path, arcname=UNIVERSAL_HTML_NAME)
        zf.write(exe_for_zip, arcname=WINDOWS_EXE_NAME)
        zf.write(readme_path, arcname=README_TXT_NAME)

    for path in (universal_path, readme_path, exe_dst, zip_any_path, zip_exe_path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"OK: {path} ({os.path.getsize(path)} bytes / {size_mb:.2f} MB)")


if __name__ == "__main__":
    build_portable()
