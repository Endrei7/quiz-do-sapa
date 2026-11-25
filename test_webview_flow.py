"""Teste automatizado completo (1280x720 + 10 equipes + anti-duplo-clique + sprites + offline + Boss 2x)."""

import os
import re
import time
from PIL import Image
import webview
from main import DesktopApi, resource_path


def check_offline_and_sprites():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for root, _, files in os.walk(base_dir):
        if any(skip in root for skip in (".git", "build", "dist", "__pycache__")):
            continue
        for fn in files:
            if fn.endswith((".py", ".html", ".js", ".css")):
                p = os.path.join(root, fn)
                txt = open(p, encoding="utf-8", errors="ignore").read()
                urls = [u for u in re.findall(r"https?://\S+", txt) if "w3.org/2000/svg" not in u]
                assert not urls, f"External URL found in {p}: {urls}"

    sp_dir = os.path.join(base_dir, "web", "assets", "sprites")
    for fn in sorted(os.listdir(sp_dir)):
        im = Image.open(os.path.join(sp_dir, fn)).convert("RGBA")
        w, h = im.size
        px = im.load()
        assert all(px[x, 0][3] <= 20 and px[x, h - 1][3] <= 20 for x in range(w)), f"Top/bottom touch in {fn}"
        assert all(px[0, y][3] <= 20 and px[w - 1, y][3] <= 20 for y in range(h)), f"Left/right touch in {fn}"


def main():
    check_offline_and_sprites()
    api = DesktopApi()
    index_file = resource_path(os.path.join("web", "index.html"))
    win = webview.create_window(
        title="Audit 720p — Quiz do S.A.P.A.",
        url=index_file,
        js_api=api,
        width=1280,
        height=720,
        background_color="#0ea5e9",
    )
    results = {}

    def on_loaded():
        time.sleep(0.5)
        win.evaluate_js("document.querySelector('.count-pill[data-count=\"10\"]').click();")
        time.sleep(0.15)
        results["start"] = win.evaluate_js("""
            (() => {
              const img = document.getElementById('start-mascot-img');
              return {
                active: document.getElementById('screen-start').classList.contains('active'),
                inputCount: document.querySelectorAll('#team-inputs .team-input-row').length,
                twoCols: document.getElementById('team-inputs').classList.contains('two-cols'),
                hasBase64: img.src.startsWith('data:image/png;base64,'),
                naturalWidth: img.naturalWidth,
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.evaluate_js("document.getElementById('btn-start-game').click();")
        time.sleep(0.25)

        q_checks = []
        for i in range(10):
            if i == 9:
                results["boss_intro"] = win.evaluate_js("""
                    (() => ({
                      overlay: document.getElementById('boss-intro-overlay').classList.contains('active'),
                      bossMode: document.body.classList.contains('boss-mode')
                    }))()
                """)
                time.sleep(0.42)
                win.evaluate_js("document.getElementById('btn-start-boss').click();")
                time.sleep(0.25)

            info = win.evaluate_js("""
                (() => ({
                  badge: document.getElementById('q-counter-badge').textContent,
                  bossSpotDisplay: getComputedStyle(document.getElementById('boss-spot')).display,
                  brokenVisibleImgs: Array.from(document.querySelectorAll('#screen-quiz img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
                  optH: Math.round(document.querySelector('.kahoot-btn').getBoundingClientRect().height),
                  overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
                }))()
            """)

            win.evaluate_js("""
                (() => {
                  const idx = Number(document.getElementById('q-counter-badge').textContent.split('/')[0].trim()) - 1;
                  const q = window.__SAPA_DATA__.questions[idx];
                  document.querySelectorAll('.kahoot-btn')[q.correct].click();
                })()
            """)
            time.sleep(0.18)
            fb = win.evaluate_js("""
                (() => {
                  const btns = document.querySelectorAll('.team-award-btn');
                  [0, 1, 2, 3, 9].forEach(idx => { if (btns[idx]) btns[idx].click(); });
                  return {
                    btnCount: btns.length,
                    btnSample: [btns[0].textContent, btns[1].textContent, btns[2].textContent, btns[3].textContent, btns[9].textContent],
                    bossHpAfter: document.getElementById('boss-hp-text').textContent,
                    optHAfter: Math.round(document.querySelector('.kahoot-btn').getBoundingClientRect().height),
                    overflowAfterReveal: document.documentElement.scrollHeight > window.innerHeight + 2
                  };
                })()
            """)
            info.update(fb)
            q_checks.append(info)

            # Testa protecao contra clique duplo rapido no botao Proxima
            time.sleep(0.42)
            win.evaluate_js("const b = document.getElementById('btn-next'); b.click(); b.click();")
            time.sleep(0.18)

        results["questions"] = q_checks
        time.sleep(1.4)
        results["podium"] = win.evaluate_js("""
            (() => {
              const stageRect = document.querySelector('.podium-stage').getBoundingClientRect();
              const footerRect = document.querySelector('.podium-footer').getBoundingClientRect();
              return {
                active: document.getElementById('screen-podium').classList.contains('active'),
                podiumPts: Array.from(document.querySelectorAll('.podium-team-pts')).map(el => el.textContent),
                otherRanksCount: document.querySelectorAll('#other-ranks-row .fourth-place-pill').length,
                stageToFooterGap: Math.round(footerRect.top - stageRect.bottom),
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.destroy()

    win.events.loaded += on_loaded
    webview.start(gui="edgechromium", http_server=False)

    print("START (720p):", results["start"])
    print("Q0 (720p):", results["questions"][0])
    print("Q1 badge after double-click on Q0:", results["questions"][1]["badge"])
    print("Q9 Boss (720p):", results["questions"][9])
    print("PODIUM (720p):", results["podium"])

    assert results["start"]["hasBase64"] and results["start"]["inputCount"] == 10 and not results["start"]["overflowY"]
    assert results["questions"][1]["badge"] == "2 / 10", "Double-click skipped a question!"
    assert results["questions"][0]["optHAfter"] >= 70
    assert results["questions"][9]["optHAfter"] >= 70, f"Boss optHAfter too small: {results['questions'][9]['optHAfter']}"
    assert "+400" in results["questions"][9]["btnSample"][0]
    assert "0 / 400 HP" in results["questions"][9]["bossHpAfter"]
    assert all(q["brokenVisibleImgs"] == 0 for q in results["questions"])
    assert not any(q["overflowY"] or q["overflowAfterReveal"] for q in results["questions"])
    assert results["podium"]["active"] and results["podium"]["otherRanksCount"] == 7 and not results["podium"]["overflowY"]
    print("ALL AUDIT + 720P + 10-TEAM + BOSS 2X TESTS PASSED!")


if __name__ == "__main__":
    main()
