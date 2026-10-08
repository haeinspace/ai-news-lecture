#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fb_post.py — visible-Chrome(WSLg, CDP :9222)로 Facebook에 텍스트+사진 게시.

사용법:
  fb_post.py --text-file FILE [--photo PATH] [--dry-run]

- 시작 시 항상 facebook.com으로 이동해 이전 대화상자 잔해를 정리한다.
- composer는 1회만 연다. 실패 시 예외 종료(중복 composer 생성 없음).
- dry-run: 입력+사진 첨부까지만 하고 '게시' 클릭 없이 대화상자를 닫는다.
"""
import argparse, json, sys, time, urllib.request
import websocket

CDP_JSON = "http://127.0.0.1:9222/json"
MARK = "__HERMES_FB_DONE__"


class FB:
    def __init__(self):
        # connect to browser-level CDP and create a FRESH tab — reusing old tabs
        # is unreliable (FB leaves half-dead targets whose navigate() hangs)
        ver = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=10))
        self.ws = websocket.create_connection(ver["webSocketDebuggerUrl"], timeout=30)
        self._id = 0
        self.session = None
        r = self.send("Target.createTarget", url="https://www.facebook.com/",
                      tabConfiguration={"activate": True})
        self.target_id = r["targetId"]
        att = self.send("Target.attachToTarget", targetId=self.target_id, flatten=True)
        self.session = att["sessionId"]

    def send(self, method, _no_session=False, **params):
        self._id += 1
        msg = {"id": self._id, "method": method, "params": params}
        if self.session and not _no_session:
            msg["sessionId"] = self.session
        self.ws.send(json.dumps(msg))
        deadline = time.time() + 40
        self.ws.settimeout(5)
        while time.time() < deadline:
            try:
                resp = json.loads(self.ws.recv())
            except Exception:
                continue
            if resp.get("id") == self._id:
                self.ws.settimeout(30)
                if "error" in resp:
                    raise RuntimeError(f"{method}: {resp['error']}")
                return resp.get("result", {})
        raise RuntimeError(f"{method}: timeout")

    def ev(self, expr):
        r = self.send("Runtime.evaluate", expression=expr, returnByValue=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def close(self, close_tab=False):
        try:
            if close_tab and getattr(self, "target_id", None):
                self.send("Target.closeTarget", targetId=self.target_id)
        except Exception:
            pass
        try:
            self.ws.close()
        except Exception:
            pass


def reset(fb):
    fb.send("Page.enable")
    fb.send("Page.navigate", url="https://www.facebook.com/")
    time.sleep(8)


def composer_opened(fb):
    return fb.ev("""(() => {
      const ds=[...document.querySelectorAll('[role="dialog"]')];
      return ds.some(d => d.offsetParent && d.querySelector('div[contenteditable="true"][role="textbox"]'));
    })()""")


def open_composer(fb):
    ok = fb.ev("""(() => {
      const el=[...document.querySelectorAll('div[role="button"],span')]
        .find(e=>/무슨 생각을 하고 계신가요|Create post/i.test((e.getAttribute('aria-label')||'')+e.textContent));
      if(!el) return false;
      el.scrollIntoView(); el.click(); return true;
    })()""")
    if not ok:
        sys.exit("ERROR: composer 트리거 없음 (로그인 상태 확인)")
    for _ in range(10):
        time.sleep(1.5)
        if composer_opened(fb):
            return
    sys.exit("ERROR: composer 대화상자 안 열림")


def type_text(fb, text):
    fb.ev("""(() => {
      const ds=[...document.querySelectorAll('[role="dialog"]')];
      const d=ds.find(d=>d.offsetParent&&d.querySelector('div[contenteditable="true"][role="textbox"]'));
      const e=d.querySelector('div[contenteditable="true"][role="textbox"]');
      e.focus(); return true;
    })()""")
    time.sleep(0.5)
    for ch in text:
        if ch == "\n":
            fb.send("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter",
                    windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
            fb.send("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter",
                    windowsVirtualKeyCode=13, nativeVirtualKeyCode=13)
        else:
            fb.send("Input.insertText", text=ch)
    time.sleep(1)
    typed = fb.ev("""(() => {
      const ds=[...document.querySelectorAll('[role="dialog"]')];
      const d=ds.find(d=>d.offsetParent&&d.querySelector('div[contenteditable="true"][role="textbox"]'));
      return d && d.querySelector('div[contenteditable="true"]').innerText.length;
    })()""")
    if not typed or typed < len(text) * 0.9:
        sys.exit(f"ERROR: 입력 유실 ({typed}/{len(text)})")


def attach_photo(fb, path):
    fb.send("DOM.enable")
    clicked = fb.ev("""(() => {
      const ds=[...document.querySelectorAll('[role="dialog"]')];
      const d=ds.find(d=>d.offsetParent&&d.querySelector('div[contenteditable="true"][role="textbox"]'));
      if(!d) return 'no-dialog';
      const b=[...d.querySelectorAll('[aria-label]')]
        .filter(a=>/사진\\/동영상|Photo\\/video/i.test(a.getAttribute('aria-label')||''));
      if(!b.length) return 'no-btn';
      b[0].click(); return 'clicked';
    })()""")
    if clicked != "clicked":
        sys.exit("ERROR: 사진 버튼 클릭 실패 — " + str(clicked))
    time.sleep(3)
    doc = fb.send("DOM.getDocument", depth=-1)
    nodes = fb.send("DOM.querySelectorAll", nodeId=doc["root"]["nodeId"],
                    selector="input[type=file]")["nodeIds"]
    if not nodes:
        sys.exit("ERROR: input[type=file] 없음")
    fb.send("DOM.setFileInputFiles", files=[path], nodeId=nodes[-1])
    for _ in range(12):
        time.sleep(2)
        ready = fb.ev("""(() => {
          const ds=[...document.querySelectorAll('[role="dialog"]')];
          const d=ds.find(d=>d.offsetParent&&d.querySelector('div[contenteditable="true"][role="textbox"]'));
          if(!d) return false;
          return !!(d.querySelector('img[src^="blob:"], img[src*="scontent"], img[src*="external"], img[src*="fbhosted"]')
                    || /사진 1개|1개의 사진|이미지 1개|사진 미리|게시물 미리/.test(d.innerText));
        })()""")
        if ready:
            return True
    return False


def close_dialog(fb):
    for _ in range(5):
        done = fb.ev("""(() => {
          const ds=[...document.querySelectorAll('[role="dialog"]')].filter(d=>d.offsetParent);
          if(!ds.length) return true;
          const d=ds[ds.length-1];
          const x=[...d.querySelectorAll('[aria-label]')].find(a=>/대화 상자 닫기|작성 도구 대화 상자 닫기|Close dialog/i.test(a.getAttribute('aria-label')||''));
          if(x){x.click(); return false;}
          return true;
        })()""")
        time.sleep(1.5)
        if done:
            return


def click_post(fb):
    r = fb.ev("""(() => {
      const ds=[...document.querySelectorAll('[role="dialog"]')];
      const d=ds.find(d=>d.offsetParent&&d.querySelector('div[contenteditable="true"][role="textbox"]'));
      if(!d) return 'no-dialog';
      const btns=[...d.querySelectorAll('div[role="button"]')]
        .filter(b=>/^게시$|^Post$/.test((b.getAttribute('aria-label')||b.textContent||'').trim()));
      if(!btns.length) return 'no-post-btn';
      const b=btns[btns.length-1];
      b.scrollIntoView(); b.click(); return 'posted-click';
    })()""")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--photo")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-open", action="store_true",
                    help="dry-run 후 대화상자를 닫지 않고 게시 직전 상태로 유지")
    a = ap.parse_args()
    text = open(a.text_file, encoding="utf-8").read().strip()

    fb = FB()
    try:
        reset(fb)
        open_composer(fb)
        type_text(fb, text)
        photo_ok = False
        if a.photo:
            photo_ok = attach_photo(fb, a.photo)
        if a.dry_run:
            print(json.dumps({"dry_run": True, "text_len": len(text),
                              "photo_attached": bool(photo_ok)}, ensure_ascii=False))
            if not a.keep_open:
                close_dialog(fb)
            return
        r = click_post(fb)
        if r != "posted-click":
            sys.exit("ERROR: 게시 버튼 실패 — " + str(r))
        time.sleep(8)
        gone = not fb.ev("document.querySelectorAll('[role=\"dialog\"]').length")
        print(json.dumps({"posted": True, "dialogClosed": gone,
                          "photo_attached": bool(photo_ok)}, ensure_ascii=False))
    finally:
        fb.close(close_tab=not a.keep_open)


if __name__ == "__main__":
    main()
