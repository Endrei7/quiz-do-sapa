"""Teste automatizado end-to-end da UI HTML5 dentro do PyWebView."""

import time
import webview
from main import DesktopApi, create_app_window


def main():
    api = DesktopApi()
    win = create_app_window(api, title="Teste Quiz S.A.P.A.")
    results = {}

    def on_loaded():
        time.sleep(0.5)
        results["start"] = win.evaluate_js("""
            (() => {
              const img = document.getElementById('start-mascot-img');
              return {
                active: document.getElementById('screen-start').classList.contains('active'),
                src: img.getAttribute('src'),
                currentSrc: img.currentSrc,
                complete: img.complete,
                naturalWidth: img.naturalWidth,
                qCount: (window.__SAPA_DATA__ && window.__SAPA_DATA__.questions || []).length,
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.evaluate_js("document.getElementById('btn-start-game').click();")
        time.sleep(0.25)

        q_checks = []
        for i in range(10):
            info = win.evaluate_js("""
                (() => {
                  const m = document.getElementById('quiz-mascot-img');
                  return {
                    badge: document.getElementById('q-counter-badge').textContent,
                    isAngry: m.classList.contains('anim-angry'),
                    naturalWidth: m.naturalWidth,
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
                  const pick = q.is_pollution ? q.correct : ((q.correct + 1) % 4);
                  document.querySelectorAll('.kahoot-btn')[pick].click();
                })()
            """)
            time.sleep(0.15)
            fb = win.evaluate_js("""
                (() => {
                  const btns = document.querySelectorAll('.team-award-btn');
                  if (btns[0]) btns[0].click();
                  if (btns[1]) btns[1].click();
                  return {
                    fbVisible: document.getElementById('feedback-panel').classList.contains('visible'),
                    mascotCls: document.getElementById('quiz-mascot-img').className,
                    overflowAfterReveal: document.documentElement.scrollHeight > window.innerHeight + 2
                  };
                })()
            """)
            info.update(fb)
            q_checks.append(info)
            win.evaluate_js("document.getElementById('btn-next').click();")
            time.sleep(0.15)

        results["questions"] = q_checks
        time.sleep(1.4)
        results["podium"] = win.evaluate_js("""
            (() => ({
              active: document.getElementById('screen-podium').classList.contains('active'),
              cols: document.querySelectorAll('.podium-col.revealed').length,
              headline: document.getElementById('podium-headline').textContent,
              overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
            }))()
        """)
        win.destroy()

    win.events.loaded += on_loaded
    webview.start(gui="edgechromium", http_server=False)
    print("START:", results.get("start"))
    print("Q0:", results.get("questions", [None])[0])
    print("Q2 (pollution):", results.get("questions", [None] * 3)[2])
    print("ANY OVERFLOW:", any(q.get("overflowY") or q.get("overflowAfterReveal") for q in results.get("questions", [])))
    print("PODIUM:", results.get("podium"))
    assert results["start"]["active"] and results["start"]["naturalWidth"] > 100
    assert len(results["questions"]) == 10
    assert results["questions"][0]["paused_txt"] == "PAUSA"
    assert all(q["fbVisible"] for q in results["questions"])
    assert results["questions"][2]["isAngry"] is True
    assert results["podium"]["active"] and results["podium"]["cols"] == 3
    print("ALL PYWEBVIEW TESTS PASSED!")


if __name__ == "__main__":
    main()
