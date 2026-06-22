from jmcomic import *
import os, json, shutil
from pathlib import Path

keyword = os.getenv('SEARCH_KEYWORD', '').strip()
if not keyword:
    print('❌ 未提供搜索关键词')
    exit(1)

output_dir = Path('site')
covers_dir = output_dir / 'covers'
shutil.rmtree(output_dir, ignore_errors=True)
covers_dir.mkdir(parents=True, exist_ok=True)

client = JmOption.default().new_jm_client()

print('=' * 60)
print(f'🔍 搜索关键词: {keyword}')
print('=' * 60)

page = client.search_site(search_query=keyword, page=1)
total = page.total

print(f'📊 共找到 {total} 个结果（第 1 页）')

results = []
failed = 0

for album_id, title in page:
    try:
        detail = client.get_album_detail(album_id)

        # 下载封面
        cover_path = covers_dir / f'{album_id}.jpg'
        try:
            client.download_album_cover(album_id, str(cover_path))
        except Exception:
            cover_path = None

        # 标签处理
        tags = detail.tags if hasattr(detail, 'tags') and detail.tags else []
        if isinstance(tags, list):
            tags = tags[:6]  # 最多6个标签

        results.append({
            'id': str(album_id),
            'title': title,
            'author': detail.author if hasattr(detail, 'author') else '?',
            'page_count': str(detail.page_count) if hasattr(detail, 'page_count') else '?',
            'tags': tags,
            'has_cover': cover_path is not None,
        })
        print(f'  ✓ [{album_id}] {title[:40]}')
    except Exception as e:
        failed += 1
        print(f'  ✗ [{album_id}] 获取失败: {str(e)[:60]}')

print(f'✅ 成功: {len(results)}, 失败: {failed}')

# ─── 生成 HTML ───────────────────────────────────────────

def esc(text):
    """HTML 转义"""
    if not isinstance(text, str):
        text = str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

cards_html = ''
for r in results:
    tags_html = ''.join(
        f'<span class="tag">{esc(t)}</span>'
        for t in (r['tags'] or [])
    )
    cover_html = (
        f'<img class="cover" src="covers/{r["id"]}.jpg" alt="{esc(r["title"])}" loading="lazy">'
        if r['has_cover'] else
        f'<div class="cover placeholder">📚</div>'
    )

    cards_html += f'''
    <div class="card" data-id="{r['id']}">
      {cover_html}
      <div class="info">
        <div class="id-badge" onclick="copyId('{r['id']}')" title="点击复制 ID">ID: {r['id']} 📋</div>
        <div class="title">{esc(r['title'])}</div>
        <div class="meta">👤 {esc(r['author'])} · 📄 {r['page_count']} 页</div>
        <div class="tags">{tags_html}</div>
        <a class="dl-btn" href="https://github.com/nairbhaha/JMComic-Crawler-Python/actions/workflows/download_dispatch.yml" target="_blank">⬇ 下载</a>
      </div>
    </div>'''

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>搜索结果: {esc(keyword)}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
  background: #0f0f13;
  color: #e0e0e0;
  min-height: 100vh;
}}
.header {{
  text-align: center;
  padding: 40px 20px 30px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}}
.header h1 {{ font-size: 28px; margin-bottom: 8px; }}
.header .sub {{ color: #888; font-size: 14px; }}
.count {{ color: #f0c040; }}
.grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
  padding: 30px;
  max-width: 1400px;
  margin: 0 auto;
}}
.card {{
  background: #1c1c24;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s;
  border: 1px solid #2a2a35;
}}
.card:hover {{ transform: translateY(-4px); box-shadow: 0 8px 30px rgba(0,0,0,0.4); }}
.cover {{
  width: 100%;
  aspect-ratio: 3/4;
  object-fit: cover;
  display: block;
  background: #2a2a35;
}}
.cover.placeholder {{
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48px;
  color: #555;
}}
.info {{ padding: 14px; }}
.id-badge {{
  display: inline-block;
  background: #f0c040;
  color: #1a1a2e;
  font-size: 12px;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 20px;
  cursor: pointer;
  margin-bottom: 8px;
  user-select: none;
}}
.id-badge:hover {{ background: #ffd866; }}
.id-badge.copied {{ background: #4caf50; color: #fff; }}
.title {{
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 8px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.meta {{ font-size: 12px; color: #999; margin-bottom: 8px; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 12px; }}
.tag {{
  font-size: 11px;
  background: #2a2a35;
  color: #aaa;
  padding: 2px 8px;
  border-radius: 10px;
}}
.dl-btn {{
  display: block;
  text-align: center;
  background: #2563eb;
  color: #fff;
  text-decoration: none;
  padding: 8px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.2s;
}}
.dl-btn:hover {{ background: #3b82f6; }}
.empty {{
  text-align: center;
  padding: 80px 20px;
  color: #666;
}}
.toast {{
  position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
  background: #333; color: #fff; padding: 10px 24px; border-radius: 8px;
  font-size: 14px; opacity: 0; transition: opacity 0.3s; z-index: 999;
}}
.toast.show {{ opacity: 1; }}
</style>
</head>
<body>
<div class="header">
  <h1>🔍 <span class="count">{len(results)}</span> 个结果 · <span style="color:#888">{esc(keyword)}</span></h1>
  <div class="sub">共找到 {total} 个相关本子，点击 ID 复制，点击下载跳转到 workflow</div>
</div>
<div class="grid">
  {cards_html if results else '<div class="empty">😕 没有找到结果，换个关键词试试</div>'}
</div>
<div id="toast" class="toast"></div>
<script>
function copyId(id) {{
  navigator.clipboard.writeText(id).then(() => {{
    const badge = document.querySelector(`.card[data-id="${{id}}"] .id-badge`);
    if (badge) {{ badge.textContent = '✅ 已复制!'; badge.classList.add('copied'); }}
    showToast('已复制 ID: ' + id);
    setTimeout(() => {{ if (badge) {{ badge.textContent = 'ID: ' + id + ' 📋'; badge.classList.remove('copied'); }} }}, 2000);
  }});
}}
function showToast(msg) {{
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2000);
}}
</script>
</body>
</html>'''

write(output_dir / 'index.html', html)
print(f'✅ 页面已生成: {output_dir / "index.html"}')
print(f'🌐 即将部署到 GitHub Pages...')
