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

    for sub in ("sprites", "avatars"):
        sp_dir = os.path.join(base_dir, "web", "assets", sub)
        assert os.path.isdir(sp_dir), f"Missing asset dir: {sp_dir}"
        for fn in sorted(os.listdir(sp_dir)):
            im = Image.open(os.path.join(sp_dir, fn)).convert("RGBA")
            w, h = im.size
            px = im.load()
            assert all(px[x, 0][3] <= 20 and px[x, h - 1][3] <= 20 for x in range(w)), f"Top/bottom touch in {sub}/{fn}"
            assert all(px[0, y][3] <= 20 and px[w - 1, y][3] <= 20 for y in range(h)), f"Left/right touch in {sub}/{fn}"

    av_dir = os.path.join(base_dir, "web", "assets", "avatars")
    expected_avatars = {
        "boto.png", "ariranha.png", "peixe_boi.png", "tartaruga.png", "onca.png",
        "preguica.png", "tucano.png", "arara.png", "pirarucu.png", "sapo.png",
    }
    assert set(os.listdir(av_dir)) == expected_avatars, f"Unexpected avatars: {os.listdir(av_dir)}"


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
        results["start4_avatars"] = win.evaluate_js("""
            (() => {
              const rows = Array.from(document.querySelectorAll('#team-inputs .team-input-row'));
              const initIds = rows.map(r => r.querySelector('.avatar-medallion').dataset.avatarId);
              const initVals = rows.map(r => r.querySelector('input').value);
              const overflow4 = document.documentElement.scrollHeight > window.innerHeight + 2;

              // Equipe 1 clica > (boto -> pula ariranha/peixe_boi/tartaruga -> vai para onca)
              rows[0].querySelector('.avatar-next-btn').click();
              const row0AfterNext = document.querySelector('#team-inputs .team-input-row');
              const afterArrowId = row0AfterNext.querySelector('.avatar-medallion').dataset.avatarId;
              const afterArrowName = row0AfterNext.querySelector('input').value;

              // Abre modal da Equipe 1 e verifica animais ocupados/desabilitados
              row0AfterNext.querySelector('.avatar-medallion').click();
              const modalActive = document.getElementById('avatar-picker-modal').classList.contains('active');
              const modalBtns = Array.from(document.querySelectorAll('#avatar-picker-grid .avatar-option-btn'));
              const takenDisabledCount = modalBtns.filter(b => b.classList.contains('taken') && b.disabled).length;
              // Seleciona Tucano no modal
              document.querySelector('#avatar-picker-grid .avatar-option-btn[data-avatar-id="tucano"]').click();
              const modalClosed = !document.getElementById('avatar-picker-modal').classList.contains('active');
              const row0AfterModal = document.querySelector('#team-inputs .team-input-row');
              const afterModalId = row0AfterModal.querySelector('.avatar-medallion').dataset.avatarId;
              const afterModalName = row0AfterModal.querySelector('input').value;

              // Equipe 2 digita nome customizado e troca avatar: deve manter o nome customizado
              const row1Input = document.querySelectorAll('#team-inputs .team-input-row')[1].querySelector('input');
              row1Input.value = 'Turma Guardiã';
              row1Input.dispatchEvent(new Event('input', { bubbles: true }));
              document.querySelectorAll('#team-inputs .team-input-row')[1].querySelector('.avatar-next-btn').click();
              const row1After = document.querySelectorAll('#team-inputs .team-input-row')[1];
              const customNamePreserved = row1After.querySelector('input').value;
              const row1AfterId = row1After.querySelector('.avatar-medallion').dataset.avatarId;

              return {
                initIds,
                initVals,
                overflow4,
                afterArrowId,
                afterArrowName,
                modalActive,
                modalCount: modalBtns.length,
                takenDisabledCount,
                modalClosed,
                afterModalId,
                afterModalName,
                customNamePreserved,
                row1AfterId
              };
            })()
        """)
        results["score_hints"] = win.evaluate_js("""
            (() => {
              const hints = {};
              [2, 4, 8, 9, 10].forEach((n) => {
                document.querySelector(`.count-pill[data-count="${n}"]`).click();
                hints[n] = document.getElementById('start-score-hint').textContent;
              });
              return hints;
            })()
        """)
        time.sleep(0.15)
        results["start"] = win.evaluate_js("""
            (() => {
              const img = document.getElementById('start-mascot-img');
              const medallions = Array.from(document.querySelectorAll('#team-inputs .avatar-medallion'));
              const avatarIds = medallions.map(m => m.dataset.avatarId);
              const brokenAvatars = medallions.filter(m => m.querySelector('img').naturalWidth === 0).length;
              return {
                active: document.getElementById('screen-start').classList.contains('active'),
                inputCount: document.querySelectorAll('#team-inputs .team-input-row').length,
                twoCols: document.getElementById('team-inputs').classList.contains('two-cols'),
                uniqueAvatars: new Set(avatarIds).size,
                brokenAvatars,
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
            info = win.evaluate_js("""
                (() => ({
                  badge: document.getElementById('q-counter-badge').textContent,
                  bossSpotDisplay: getComputedStyle(document.getElementById('boss-spot')).display,
                  bossMode: document.body.classList.contains('boss-mode'),
                  hudAvatarCount: document.querySelectorAll('#hud-scores .hud-avatar-icon').length,
                  brokenVisibleImgs: Array.from(document.querySelectorAll('#screen-quiz img, #hud-scores img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
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
                    btnAvatarCount: document.querySelectorAll('.team-award-btn .award-btn-avatar').length,
                    brokenBtnAvatars: Array.from(document.querySelectorAll('.team-award-btn .award-btn-avatar')).filter(im => im.naturalWidth === 0).length,
                    btnSample: [btns[0].textContent, btns[1].textContent, btns[2].textContent, btns[3].textContent, btns[9].textContent],
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

        # 1. Podio Falso (comemoracao limpa inicial) -> Emboscada + Roubo -> Cutscene Pre-Boss
        results["fake_podium"] = win.evaluate_js("""
            (() => ({
              podiumActive: document.getElementById('screen-podium').classList.contains('active'),
              bossMode: document.body.classList.contains('boss-mode'),
              heistBanner: document.getElementById('podium-heist-banner').classList.contains('active')
            }))()
        """)
        time.sleep(3.15)
        # Espera 2.6s extras para provar que NAO pula automaticamente (exige acao manual)
        time.sleep(2.6)
        results["heist"] = win.evaluate_js("""
            (() => ({
              heistBanner: document.getElementById('podium-heist-banner').classList.contains('active'),
              cutsceneStillClosed: !document.getElementById('cutscene-overlay').classList.contains('active'),
              hasContinueBtn: Boolean(document.getElementById('btn-heist-continue')),
              bossMode: document.body.classList.contains('boss-mode'),
              lockedHudCount: document.querySelectorAll('#hud-scores .score-pill.locked-pill').length,
              stolenTexts: Array.from(document.querySelectorAll('.podium-team-pts.stolen')).map(e => e.textContent)
            }))()
        """)
        win.evaluate_js("document.getElementById('btn-heist-continue').click();")
        time.sleep(0.25)

        pre_steps = []
        for _ in range(4):
            pre_steps.append(win.evaluate_js("""
                (() => ({
                  overlay: document.getElementById('cutscene-overlay').classList.contains('active'),
                  counter: document.getElementById('cutscene-step-counter').textContent,
                  speakerTag: document.getElementById('cutscene-speaker-tag').textContent,
                  text: document.getElementById('cutscene-text').textContent,
                  brokenImgs: Array.from(document.querySelectorAll('#cutscene-overlay img')).filter(im => im.naturalWidth === 0).length,
                  overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
                }))()
            """))
            time.sleep(0.28)
            win.evaluate_js("document.getElementById('btn-cutscene-next').click();")
            time.sleep(0.12)
        results["pre_cutscene"] = pre_steps

        # 2. Fase 2: Boss Fight (7 Perguntas Mais Dificeis + HP 7 segmentos + Ataque + 2x)
        boss_checks = []
        for b in range(7):
            info = win.evaluate_js("""
                (() => ({
                  badge: document.getElementById('q-counter-badge').textContent,
                  bossSpotDisplay: getComputedStyle(document.getElementById('boss-spot')).display,
                  bossMode: document.body.classList.contains('boss-mode'),
                  hpSegCount: document.querySelectorAll('#boss-hp-track .boss-hp-seg').length,
                  hpLostBefore: document.querySelectorAll('#boss-hp-track .boss-hp-seg.lost').length,
                  brokenVisibleImgs: Array.from(document.querySelectorAll('#screen-quiz img, #hud-scores img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
                  optH: Math.round(document.querySelector('.kahoot-btn').getBoundingClientRect().height),
                  overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
                }))()
            """)
            win.evaluate_js(f"""
                (() => {{
                  const q = window.__SAPA_DATA__.bossQuestions[{b}];
                  document.querySelectorAll('.kahoot-btn')[q.correct].click();
                }})()
            """)
            time.sleep(0.18)
            fb = win.evaluate_js("""
                (() => {
                  const btns = document.querySelectorAll('.team-award-btn');
                  [0, 1, 2, 3, 9].forEach(idx => { if (btns[idx]) btns[idx].click(); });
                  return {
                    btnSample: [btns[0].textContent, btns[1].textContent, btns[2].textContent, btns[3].textContent, btns[9].textContent],
                    hpLostAfter: document.querySelectorAll('#boss-hp-track .boss-hp-seg.lost').length,
                    bossHpAfter: document.getElementById('boss-hp-text').textContent,
                    optHAfter: Math.round(document.querySelector('.kahoot-btn').getBoundingClientRect().height),
                    overflowAfterReveal: document.documentElement.scrollHeight > window.innerHeight + 2
                  };
                })()
            """)
            info.update(fb)
            boss_checks.append(info)

            time.sleep(0.42)
            win.evaluate_js("document.getElementById('btn-next').click();")
            time.sleep(0.18)
        results["boss_questions"] = boss_checks

        # 3. Cutscene Final: Cenario restaurado + Pontos em Dobro + Reflexao
        final_steps = []
        for _ in range(4):
            final_steps.append(win.evaluate_js("""
                (() => ({
                  overlay: document.getElementById('cutscene-overlay').classList.contains('active'),
                  counter: document.getElementById('cutscene-step-counter').textContent,
                  speakerTag: document.getElementById('cutscene-speaker-tag').textContent,
                  bossModeAfterRestore: document.body.classList.contains('boss-mode'),
                  lockedHudCount: document.querySelectorAll('#hud-scores .score-pill.locked-pill').length,
                  brokenImgs: Array.from(document.querySelectorAll('#cutscene-overlay img')).filter(im => im.naturalWidth === 0).length
                }))()
            """))
            time.sleep(0.28)
            win.evaluate_js("document.getElementById('btn-cutscene-next').click();")
            time.sleep(0.12)
        results["final_cutscene"] = final_steps

        # 4. Podio Final Verdadeiro
        time.sleep(1.4)
        results["podium"] = win.evaluate_js("""
            (() => {
              const stageRect = document.querySelector('.podium-stage').getBoundingClientRect();
              const footerRect = document.querySelector('.podium-footer').getBoundingClientRect();
              const headerRect = document.querySelector('.podium-header').getBoundingClientRect();
              const r1Wrap = document.querySelector('.podium-col.rank-1 .podium-team-avatar-wrap');
              const r2Wrap = document.querySelector('.podium-col.rank-2 .podium-team-avatar-wrap');
              const r1Rect = r1Wrap ? r1Wrap.getBoundingClientRect() : null;
              return {
                active: document.getElementById('screen-podium').classList.contains('active'),
                bossMode: document.body.classList.contains('boss-mode'),
                podiumPts: Array.from(document.querySelectorAll('.podium-team-pts')).map(el => el.textContent),
                podiumBarDetails: Array.from(document.querySelectorAll('.podium-bar-detail')).map(el => el.textContent),
                podiumAvatarCount: document.querySelectorAll('.podium-team-avatar').length,
                rank1AvatarHeight: r1Wrap ? Math.round(r1Wrap.offsetHeight) : 0,
                rank2AvatarHeight: r2Wrap ? Math.round(r2Wrap.offsetHeight) : 0,
                headerToRank1AvatarGap: r1Rect ? Math.round(r1Rect.top - headerRect.bottom) : 0,
                otherRanksCount: document.querySelectorAll('#other-ranks-row .fourth-place-pill').length,
                otherRankAvatarCount: document.querySelectorAll('#other-ranks-row .other-rank-avatar').length,
                brokenPodiumImgs: Array.from(document.querySelectorAll('#screen-podium img')).filter(im => im.offsetParent !== null && im.naturalWidth === 0).length,
                stageToFooterGap: Math.round(footerRect.top - stageRect.bottom),
                overflowY: document.documentElement.scrollHeight > window.innerHeight + 2
              };
            })()
        """)
        win.destroy()

    win.events.loaded += on_loaded
    webview.start(gui="edgechromium", http_server=False)

    print("SCORE HINTS BY TEAM COUNT:", results["score_hints"])
    print("AVATARS 4-TEAM:", results["start4_avatars"])
    print("START (720p):", results["start"])
    print("PHASE 1 Q0 (720p):", results["questions"][0])
    print("Q1 badge after double-click on Q0:", results["questions"][1]["badge"])
    print("FAKE PODIUM:", results["fake_podium"])
    print("HEIST:", results["heist"])
    print("PRE CUTSCENE:", [(s["counter"], s["speakerTag"]) for s in results["pre_cutscene"]])
    print("BOSS Q0 (720p):", results["boss_questions"][0])
    print("BOSS Q6 (720p):", results["boss_questions"][6])
    print("FINAL CUTSCENE:", [(s["counter"], s["speakerTag"], s["bossModeAfterRestore"], s["lockedHudCount"]) for s in results["final_cutscene"]])
    print("TRUE PODIUM (720p):", results["podium"])

    hints = results["score_hints"]
    assert "+100" in hints["2"] and "+200" in hints["4"]
    assert "+400" in hints["8"] and "+450" in hints["9"] and "+500" in hints["10"]

    av4 = results["start4_avatars"]
    assert av4["initIds"] == ["boto", "ariranha", "peixe_boi", "tartaruga"]
    assert av4["initVals"] == ["Equipe Boto-Cor-de-Rosa", "Equipe Ariranha", "Equipe Peixe-Boi", "Equipe Tartaruga"]
    assert not av4["overflow4"]
    assert av4["afterArrowId"] == "onca" and av4["afterArrowName"] == "Equipe Onça-Pintada"
    assert av4["modalActive"] and av4["modalCount"] == 10 and av4["takenDisabledCount"] == 3 and av4["modalClosed"]
    assert av4["afterModalId"] == "tucano" and av4["afterModalName"] == "Equipe Tucano"
    assert av4["customNamePreserved"] == "Turma Guardiã" and av4["row1AfterId"] != "ariranha"

    assert results["start"]["hasBase64"] and results["start"]["inputCount"] == 10 and not results["start"]["overflowY"]
    assert results["start"]["uniqueAvatars"] == 10 and results["start"]["brokenAvatars"] == 0
    assert results["questions"][1]["badge"] == "2 / 10", "Double-click skipped a question!"
    assert all(q["bossSpotDisplay"] == "none" and not q["bossMode"] for q in results["questions"])
    assert results["questions"][0]["hudAvatarCount"] == 10
    assert results["questions"][0]["btnAvatarCount"] == 10 and results["questions"][0]["brokenBtnAvatars"] == 0
    assert "+500" in results["questions"][0]["btnSample"][0]
    assert "+300" in results["questions"][0]["btnSample"][4]
    assert all(q["optHAfter"] >= 70 and q["brokenVisibleImgs"] == 0 for q in results["questions"])
    assert not any(q["overflowY"] or q["overflowAfterReveal"] for q in results["questions"])

    assert results["fake_podium"]["podiumActive"] and not results["fake_podium"]["bossMode"]
    assert results["heist"]["heistBanner"] and results["heist"]["cutsceneStillClosed"] and results["heist"]["hasContinueBtn"]
    assert results["heist"]["bossMode"] and results["heist"]["lockedHudCount"] == 10
    assert len(results["pre_cutscene"]) == 4 and all(s["overlay"] and s["brokenImgs"] == 0 and not s["overflowY"] for s in results["pre_cutscene"])

    assert len(results["boss_questions"]) == 7
    for idx, bq in enumerate(results["boss_questions"]):
        assert bq["bossSpotDisplay"] == "flex" and bq["bossMode"]
        assert bq["hpSegCount"] == 7 and bq["hpLostBefore"] == idx and bq["hpLostAfter"] == idx + 1
        assert "+1000" in bq["btnSample"][0] and "+600" in bq["btnSample"][4]
        assert bq["optHAfter"] >= 70 and bq["brokenVisibleImgs"] == 0
        assert not bq["overflowY"] and not bq["overflowAfterReveal"]
    assert "0 / 7" in results["boss_questions"][6]["bossHpAfter"]

    assert len(results["final_cutscene"]) == 4
    assert all(s["overlay"] and not s["bossModeAfterRestore"] and s["lockedHudCount"] == 0 and s["brokenImgs"] == 0 for s in results["final_cutscene"])

    assert results["podium"]["active"] and not results["podium"]["bossMode"]
    assert results["podium"]["podiumPts"] == ["15300 pts", "17000 pts", "13600 pts"]
    assert "2x F1: 10000 + Boss: 7000" in results["podium"]["podiumBarDetails"]
    assert results["podium"]["podiumAvatarCount"] == 3
    assert results["podium"]["rank1AvatarHeight"] >= 100
    assert results["podium"]["rank2AvatarHeight"] >= 90
    assert results["podium"]["headerToRank1AvatarGap"] >= 12
    assert results["podium"]["otherRanksCount"] == 7 and results["podium"]["otherRankAvatarCount"] == 7
    assert results["podium"]["brokenPodiumImgs"] == 0 and results["podium"]["stageToFooterGap"] >= 6
    assert not results["podium"]["overflowY"]
    print("ALL AUDIT + 720P + HEIST + CUTSCENES + 7-BOSS + DOUBLE-RESTORE TESTS PASSED!")


if __name__ == "__main__":
    main()
