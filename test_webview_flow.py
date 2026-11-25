"""Teste automatizado end-to-end (incluindo Fase Boss Q10) dentro do PyWebView."""

import time
import webview
from main import DesktopApi, create_app_window


def main():
    api = DesktopApi()
    win = create_app_window(api, title="Teste Quiz S.A.P.A. + Boss")
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
                # Verifica Alerta de Chefe e entra na luta
                boss_alert = win.evaluate_js("""
                    (() => ({
                      overlayActive: document.getElementById('boss-intro-overlay').classList.contains('active'),
                      bossMode: document.body.classList.contains('boss-mode'),
                      introSpriteW: document.getElementById('boss-intro-img').naturalWidth
                    }))()
                """)
                results["boss_alert"] = boss_alert
                win.evaluate_js("document.getElementById('btn-start-boss').click();")
                time.sleep(0.25)

            info = win.evaluate_js("""
                (() => {
                  const m = document.getElementById('quiz-mascot-img');
                  const b = document.getElementById('boss-img');
                  return {
                    badge: document.getElementById('q-counter-badge').textContent,
                    isAngry: m.classList.contains('anim-angry-burst'),
                    naturalWidth: m.naturalWidth,
                    bossVisible: document.getElementById('boss-hp-panel').classList.contains('visible'),
                    bossWidth: b ? b.naturalWidth : 0,
                    bossHp: document.getElementById('boss-hp-text').textContent,
                    overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
                  };
                })()
            """)
            if i == 0:
                win.evaluate_js("document.getElementById('btn-pause').click();")
                paused_txt = win.evaluate_js("document.getElementById('timer-badge').textContent")
                win.evaluate_js("document.getElementById('btn-pause').click();")
                info["paused_txt"] = paused_txt

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
                  return {
                    fbVisible: document.getElementById('feedback-panel').classList.contains('visible'),
                    mascotCls: document.getElementById('quiz-mascot-img').className,
                    bossCls: document.getElementById('boss-img').className,
                    bossSrc: document.getElementById('boss-img').getAttribute('src'),
                    bossHpAfter: document.getElementById('boss-hp-text').textContent,
                    awardBtnText: btns[0] ? btns[0].textContent : '',
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
              const topRect = document.querySelector('.top-bar').getBoundingClientRect();
              const stageRect = document.querySelector('.podium-stage').getBoundingClientRect();
              const fourthRect = document.getElementById('fourth-place-pill').getBoundingClientRect();
              const soundRect = document.getElementById('btn-sound').getBoundingClientRect();
              return {
                active: document.getElementById('screen-podium').classList.contains('active'),
                bossModeCleared: !document.body.classList.contains('boss-mode'),
                cols: document.querySelectorAll('.podium-col.revealed').length,
                topBarH: Math.round(topRect.height),
                soundBtnH: Math.round(soundRect.height),
                stageToFourthGap: Math.round(fourthRect.top - stageRect.bottom),
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.destroy()

    win.events.loaded += on_loaded
    webview.start(gui="edgechromium", http_server=False)

    print("START:", results.get("start"))
    print("BOSS_ALERT:", results.get("boss_alert"))
    print("Q9 (Boss):", results.get("questions", [None] * 10)[9])
    print("ANY OVERFLOW:", any(q.get("overflowY") or q.get("overflowAfterReveal") for q in results.get("questions", [])))
    print("PODIUM:", results.get("podium"))

    assert results["start"]["active"] and results["start"]["naturalWidth"] > 100
    assert results["boss_alert"]["overlayActive"] and results["boss_alert"]["bossMode"]
    assert results["boss_alert"]["introSpriteW"] > 100
    q9 = results["questions"][9]
    assert q9["bossVisible"] and q9["bossWidth"] > 100
    assert "0 / 200 HP" in q9["bossHpAfter"]
    assert "boss_defeated.png" in (q9["bossSrc"] or "")
    assert "200" in q9["awardBtnText"]
    assert not any(q["overflowY"] or q["overflowAfterReveal"] for q in results["questions"])
    assert results["podium"]["active"] and results["podium"]["bossModeCleared"]
    assert results["podium"]["stageToFourthGap"] >= 0
    print("ALL BOSS + PYWEBVIEW TESTS PASSED!")


if __name__ == "__main__":
    main()
