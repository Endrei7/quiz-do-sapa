"""Teste automatizado end-to-end com 10 equipes + ordem 200/150/100/50 + Boss 2x."""

import time
import webview
from main import DesktopApi, create_app_window


def main():
    api = DesktopApi()
    win = create_app_window(api, title="Teste 10 Equipes + Boss 2x")
    results = {}

    def on_loaded():
        time.sleep(0.45)
        # Seleciona 10 equipes na tela inicial
        win.evaluate_js("document.querySelector('.count-pill[data-count=\"10\"]').click();")
        time.sleep(0.15)
        results["start"] = win.evaluate_js("""
            (() => {
              const img = document.getElementById('start-mascot-img');
              return {
                active: document.getElementById('screen-start').classList.contains('active'),
                inputCount: document.querySelectorAll('#team-inputs .team-input-row').length,
                twoCols: document.getElementById('team-inputs').classList.contains('two-cols'),
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
                win.evaluate_js("document.getElementById('btn-start-boss').click();")
                time.sleep(0.25)

            info = win.evaluate_js("""
                (() => ({
                  badge: document.getElementById('q-counter-badge').textContent,
                  bossSpotDisplay: getComputedStyle(document.getElementById('boss-spot')).display,
                  brokenVisibleImgs: Array.from(document.querySelectorAll('#screen-quiz img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
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
                  // Marca as 4 primeiras equipes e a 10a equipe
                  [0, 1, 2, 3, 9].forEach(idx => { if (btns[idx]) btns[idx].click(); });
                  return {
                    btnCount: btns.length,
                    btnSample: [btns[0].textContent, btns[1].textContent, btns[2].textContent, btns[3].textContent, btns[9].textContent],
                    bossHpAfter: document.getElementById('boss-hp-text').textContent,
                    overflowAfterReveal: document.documentElement.scrollHeight > window.innerHeight + 2
                  };
                })()
            """)
            info.update(fb)
            q_checks.append(info)
            win.evaluate_js("document.getElementById('btn-next').click();")
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

    print("START (10 teams):", results["start"])
    print("Q0 sample:", results["questions"][0]["btnSample"], "overflowAfter:", results["questions"][0]["overflowAfterReveal"])
    print("Q9 Boss sample:", results["questions"][9]["btnSample"], "HP:", results["questions"][9]["bossHpAfter"], "overflowAfter:", results["questions"][9]["overflowAfterReveal"])
    print("PODIUM:", results["podium"])

    assert results["start"]["inputCount"] == 10 and results["start"]["twoCols"] and not results["start"]["overflowY"]
    assert results["questions"][0]["btnCount"] == 10
    assert "+200" in results["questions"][0]["btnSample"][0]
    assert "+150" in results["questions"][0]["btnSample"][1]
    assert "+100" in results["questions"][0]["btnSample"][2]
    assert "+50" in results["questions"][0]["btnSample"][3]
    assert "+50" in results["questions"][0]["btnSample"][4]
    # Boss vale 2x: 400, 300, 200, 100, 100
    assert "+400" in results["questions"][9]["btnSample"][0]
    assert "+300" in results["questions"][9]["btnSample"][1]
    assert "+200" in results["questions"][9]["btnSample"][2]
    assert "+100" in results["questions"][9]["btnSample"][3]
    assert "+100" in results["questions"][9]["btnSample"][4]
    assert "0 / 400 HP" in results["questions"][9]["bossHpAfter"]
    assert all(q["brokenVisibleImgs"] == 0 for q in results["questions"])
    assert not any(q["overflowY"] or q["overflowAfterReveal"] for q in results["questions"])
    assert results["podium"]["active"] and results["podium"]["otherRanksCount"] == 7
    assert results["podium"]["stageToFooterGap"] >= 0 and not results["podium"]["overflowY"]
    print("ALL 10-TEAM + BOSS 2X TESTS PASSED!")


if __name__ == "__main__":
    main()
