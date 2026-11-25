# 🐸 Quiz do S.A.P.A. — Guardiões dos Rios

Jogo educativo estilo Kahoot desenvolvido para crianças do **5º ano do Ensino Fundamental I** (10 a 11 anos) em apresentações escolares com projetor ou TV, apresentando o projeto **S.A.P.A. (*Sistema de Alerta e Previsão contra Alagamentos*)**.

Funciona **100% off-line** (sem dependência de internet, CDNs ou fontes externas), empacotável em um único executável Windows (`.exe`) via **PyInstaller + PyWebView (Edge WebView2)**.

---

## ✨ Principais Funcionalidades

- **100% Off-line e Embutido em Base64:** Todos os sprites do mascote, do vilão, avatares das equipes e logotipo são convertidos para `data:image/png;base64,...` dentro de `web/sapa_data.js`, enquanto os efeitos sonoros são sintetizados localmente via Web Audio API (com botão de mudo no topo).
- **2 a 10 Equipes com Mascotes Amazônicos:**
  - Seleção visual de **10 mascotes** (`Boto-Cor-de-Rosa`, `Ariranha`, `Peixe-Boi`, `Tartaruga`, `Onça-Pintada`, `Preguiça`, `Tucano`, `Arara-Azul`, `Pirarucu` e `Sapo-Boi`) com medalhão colorido, setas `<` `>` e mini-grade modal **5×2**.
  - Bloqueio automático de avatares repetidos (quando há menos de 10 equipes ativas) e troca direta entre equipes quando todas as 10 vagas estão ativas.
  - Sugestão automática do nome da equipe ao trocar o mascote, mantendo nomes personalizados digitados manualmente.
- **Pontuação Dinâmica por Quantidade de Equipes e Ordem de Resposta (Sem Cronômetro):**
  - **Questões 1 a 9 (`N × 50` descendo de `50` em `50` pts até `50 pts`):**
    - `4 equipes`: `200, 150, 100, 50 pts`
    - `8 equipes`: `400, 350, 300, 250, 200, 150, 100, 50 pts`
    - `9 equipes`: `450, 400, 350, 300, 250, 200, 150, 100, 50 pts`
    - `10 equipes`: `500, 450, 400, 350, 300, 250, 200, 150, 100, 50 pts`
  - **Questão 10 — Fase Boss (2× Pontos!):** Enfrente o **Capitão Garrafão** (HP proporcional ao topo da rodada: `400 HP` com 4 equipes até `1000 HP` com 10 equipes) com transição estilo história em quadrinhos, tema tempestade e pontuação dobrada (`1ª` de `+200` com 2 equipes até `+1000` com 10 equipes).
- **Pódio Final Animado & Chuva de Confetes:** Colunas de 1º, 2º e 3º lugar com medalhões ampliados dos mascotes vencedores em destaque, pílulas com mini-avatares para 4º a 10º lugar e animação de comemoração.
- **Responsivo para Projetores e TVs (`1280×720` até `1920×1080`):** Layout sem barras de rolagem (`overflow: hidden`) e proteção contra cliques duplos acidentais entre telas.

---

## ⌨️ Atalhos de Teclado

| Tecla | Ação |
| :--- | :--- |
| `1`–`4` ou `A`–`D` | Seleciona a alternativa correspondente durante a pergunta |
| `Enter` | Inicia a batalha na introdução do Boss ou avança na tela de resposta |
| `Esc` | Fecha o modal de seleção de mascote (quando aberto) |
| `F11` | Alterna o modo Tela Cheia |

---

## 📁 Estrutura do Projeto

```text
quiz_sapa/
├── main.py                  # Launcher desktop PyWebView (resolução sys._MEIPASS para .exe)
├── questions.py             # Banco das 10 perguntas educativas (inclui Fase Boss na Q10)
├── build_data_js.py         # Gera web/sapa_data.js embutindo sprites, avatares, logo e perguntas
├── build_portable.py        # Gera cópia portátil universal (HTML único + ZIPs) em dist_colegas/
├── slice_sprites.py         # Fatiamento 3×2 de spritesheet.jpeg (poses do Sapinho Explorador)
├── slice_boss_sprites.py    # Fatiamento 2×2 de boss_spritesheet.jpg (poses do Capitão Garrafão)
├── slice_team_sprites.py    # Fatiamento 5×2 de equipes_spritesheet.jpg (10 avatares das equipes)
├── test_webview_flow.py     # Auditoria off-line e teste E2E em 1280×720 no Edge WebView2
├── requirements.txt         # Dependências Python (pillow, pywebview, pyinstaller)
├── spritesheet.jpeg         # Folha de sprites do Sapinho Explorador
├── boss_spritesheet.jpg     # Folha de sprites do Capitão Garrafão
├── equipes_spritesheet.jpg  # Folha de sprites dos 10 animais amazônicos
└── web/
    ├── index.html           # Interface completa (HTML/CSS/JS + áudio Web Audio off-line)
    ├── sapa_data.js         # Bundle gerado com todos os assets Base64 + perguntas
    └── assets/
        ├── sapa_logo.png
        ├── sprites/         # PNGs transparentes do Sapinho (6) e do Boss (4)
        └── avatars/         # PNGs transparentes dos 10 mascotes das equipes
```

---

## 🚀 Como Executar em Desenvolvimento

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Iniciar o aplicativo

```bash
python main.py
```

---

## 🛠️ Reprocessamento de Assets e Testes

Sempre que alterar perguntas em `questions.py` ou gerar novamente os PNGs em `web/assets/`, atualize `web/sapa_data.js` antes de testar ou compilar:

```bash
# Opcional: refatiar as sprite sheets originais
python slice_sprites.py
python slice_boss_sprites.py
python slice_team_sprites.py

# Regerar web/sapa_data.js (Base64 + perguntas)
python build_data_js.py

# Executar bateria completa de auditoria off-line, avatares, 10 equipes e Boss em 720p
python test_webview_flow.py
```

---

## 📦 Gerar Executável Windows (`.exe`) e Cópia Portátil (`dist_colegas/`)

Para empacotar o jogo em um executável único em `dist/Quiz_do_SAPA.exe`:

```bash
pyinstaller --noconfirm --onefile --windowed --name "Quiz_do_SAPA" --add-data "web;web" main.py
```

Para gerar o pacote portátil pronto para enviar aos colegas (`dist_colegas/`):

```bash
python build_portable.py
```

Arquivos gerados em `dist_colegas/`:
- `Quiz_do_SAPA_Universal.html`: arquivo único 100% off-line para abrir com dois cliques em qualquer notebook (Windows, MacBook, Linux ou Chromebook).
- `Quiz_do_SAPA_Qualquer_Notebook.zip`: pacote leve (`HTML + LEIA-ME.txt`) sem `.exe`, ideal para enviar por WhatsApp ou e-mail sem bloqueios.
- `Quiz_do_SAPA_Windows.exe`: cópia do executável nativo para Windows 10/11.
- `Quiz_do_SAPA_Completo_Com_EXE.zip`: pacote completo (`HTML + EXE + LEIA-ME.txt`) para pendrive ou Google Drive.
