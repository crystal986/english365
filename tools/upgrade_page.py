"""Called only after all audio files pass validation; preserves lesson content."""
import re

CSS = '''
.audio-controls{display:flex;flex-wrap:wrap;gap:12px;margin-top:18px}
.audio-controls button{min-height:56px;flex:1 1 160px;padding:14px 18px;border:2px solid #1d64aa;border-radius:14px;background:#1d64aa;color:white;font-weight:700;font-size:20px;line-height:1.4;font-family:inherit;cursor:pointer;touch-action:manipulation}
.audio-controls button:focus-visible{outline:3px solid #a2482f;outline-offset:3px}
.audio-controls button[aria-pressed="true"]{background:#17436e}
#audio-status{font-size:19px;line-height:1.7;overflow-wrap:anywhere}
'''
JS = '''
(function () {
  'use strict';
  var player = document.getElementById('day1-player');
  var status = document.getElementById('audio-status');
  var buttons = document.querySelectorAll('[data-audio]');
  var current = null;
  var request = 0;
  function reset() {
    buttons.forEach(function (button) { button.setAttribute('aria-pressed', 'false'); });
  }
  function failed(id) {
    if (id !== request) return;
    reset();
    status.textContent = '播放失败，请检查网络后再点一次。若仍无声音，请在手机浏览器中打开本页，并检查手机音量。';
  }
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var id = ++request;
      player.pause();
      reset();
      current = button;
      player.src = button.getAttribute('data-audio');
      status.textContent = '正在加载：' + button.getAttribute('aria-label');
      button.setAttribute('aria-pressed', 'true');
      // Call play synchronously within the user gesture for iOS/WebView support.
      try {
        var result = player.play();
        if (result && typeof result.catch === 'function') result.catch(function () { failed(id); });
      } catch (error) { failed(id); }
    });
  });
  player.addEventListener('playing', function () {
    if (current) status.textContent = '正在播放：' + current.getAttribute('aria-label');
  });
  player.addEventListener('ended', function () { reset(); status.textContent = '播放完毕，可以再听一次。'; });
  player.addEventListener('error', function () { if (player.error) failed(request); });
}());
'''


def controls(key, text):
    return '<div class="audio-controls">' + ''.join(
        f'<button type="button" data-audio="audio/{key}_{speed}.mp3" aria-label="{text}，{label}" aria-pressed="false">{label}</button>'
        for speed, label in [('normal', '正常发音'), ('slow', '慢速发音')]) + '</div>'


def upgrade(html):
    if 'id="day1-player"' in html:
        raise ValueError('Already upgraded')
    html = html.replace('</style>', CSS + '</style>', 1)
    word = '<div class="meaning">你好！</div>'
    if html.count(word) != 1:
        raise ValueError('Word card does not match expected content')
    html = html.replace(word, word + controls('hello', 'Hello!'), 1)
    for key, text in [('hello', 'Hello!'), ('hello_mary', 'Hello, Mary!'), ('hello_everyone', 'Hello, everyone!')]:
        target = f'<section class="card"><div class="english">{text}</div>'
        if html.count(target) != 1:
            raise ValueError(f'Example card does not match: {text}')
        html = html.replace(target, target + controls(key, text), 1)
    html, count = re.subn(r'<div class="notice">.*?</div>',
        '<div class="notice"><strong>听一听：</strong>点击“正常发音”或“慢速发音”，跟着美语女声练习。音频由 Kokoro-82M 的 af_heart 声音生成。<div id="audio-status" role="status" aria-live="polite">点击按钮即可播放，请先调好手机音量。</div></div>', html, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Expected audio notice missing')
    return html.replace('</body>', '<audio id="day1-player" preload="none"></audio><script>' + JS + '</script></body>', 1)
