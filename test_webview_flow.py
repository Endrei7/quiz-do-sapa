"""Teste automatizado end-to-end (sem tempo + pontuacao por ordem 200/150/100/50 + Boss Q10)."""

import time
import webview
from main import DesktopApi, create_app_window


def main():
    api = DesktopApi()
    win = create_app_window(api, title="Teste Quiz S.A.P.A. Ordem Pontos")
    results = {}

    def on_loaded():
        time.sleep(0.45)
        results["start"] = win.evaluate_js("""
            (() => {
              const img = document.getElementById('start-mascot-img');
              return {
                active: document.getElementById('screen-start').classList.contains('active'),
                complete: img.complete,
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
                results["boss_alert"] = win.evaluate_js("""
                    (() => ({
                      overlayActive: document.getElementById('boss-intro-overlay').classList.contains('active'),
                      bossMode: document.body.classList.contains('boss-mode'),
                      introSpriteW: document.getElementById('boss-intro-img').naturalWidth
                    }))()
                """)
                win.evaluate_js("document.getElementById('btn-start-boss').click();")
                time.sleep(0.25)

            info = win.evaluate_js("""
                (() => ({
                  badge: document.getElementById('q-counter-badge').textContent,
                  noTimer: document.getElementById('timer-panel') === null,
                  hasActionBar: document.getElementById('action-panel') !== null,
                  bossVisible: document.getElementById('boss-hp-panel').classList.contains('visible'),
                  bossSpotDisplay: getComputedStyle(document.getElementById('boss-spot')).display,
                  brokenVisibleImgs: Array.from(document.querySelectorAll('#screen-quiz img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
                  overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
                }))()
            """)

            # Seleciona alternativa e testa pontuacao por ordem (200, 150, 100, 50)
            win.evaluate_js("""
                (() => {
                  const idx = Number(document.getElementById('q-counter-badge').textContent.split('/')[0].trim()) - 1;
                  const q = window.__SAPA_DATA__.questions[idx];
                  const pick = (q.is_pollution || q.is_boss) ? q.correct : ((q.correct + 1) % 4);
                  document.querySelectorAll('.kahoot-btn')[pick].click();
                })()
            """)
            time.sleep(0.18)
            fb = win.evaluate_js("""
                (() => {
                  const btns = document.querySelectorAll('.team-award-btn');
                  if (btns[0]) btns[0].click();
                  if (btns[1]) btns[1].click();
                  if (btns[2]) btns[2].click();
                  if (btns[3]) btns[3].click();
                  return {
                    fbVisible: document.getElementById('feedback-panel').classList.contains('visible'),
                    btnTexts: Array.from(btns).map(b => b.textContent),
                    hudTexts: Array.from(document.querySelectorAll('#hud-scores .score-pill')).map(p => p.textContent),
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
              const pts = Array.from(document.querySelectorAll('.podium-team-pts')).map(el => el.textContent);
              const fourth = document.getElementById('fourth-place-pill').textContent;
              return {
                active: document.getElementById('screen-podium').classList.contains('active'),
                podiumPts: pts,
                fourthText: fourth,
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.destroy()

    win.events.loaded += on_loaded
    webview.start(gui="edgechromium", http_server=False)

    print("Q0 btnTexts:", results["questions"][0]["btnTexts"])
    print("Q9 hudTexts:", results["questions"][9]["hudTexts"])
    print("PODIUM:", results["podium"])

    q0 = results["questions"][0]
    assert q0["noTimer"] and q0["hasActionBar"]
    assert q0["bossSpotDisplay"] == "none"
    assert all(q["brokenVisibleImgs"] == 0 for q in results["questions"])
    assert results["questions"][9]["bossSpotDisplay"] == "flex"
    assert "+200" in q0["btnTexts"][0]
    assert "+150" in q0["btnTexts"][1]
    assert "+100" in q0["btnTexts"][2]
    assert "+50" in q0["btnTexts"][3]
    assert results["questions"][9]["hudTexts"] == [
        "Equipe Sapo-Boi: 2000",
        "Equipe Vitória-Régia: 1500",
        "Equipe Igarapé: 1000",
        "Equipe Guaraná: 500",
    ]
    assert "0 / 200 HP" in results["questions"][9]["bossHpAfter"]
    assert not any(q["overflowY"] or q["overflowAfterReveal"] for q in results["questions"])
    assert results["podium"]["overflowY"] is False
    print("ALL ORDER-SCORING + BOSS TESTS PASSED!")


if __name__ == "__main__":
    main()
