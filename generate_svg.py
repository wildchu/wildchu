import os
import json
import urllib.request
from datetime import datetime

USERNAME = "wildchu"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_graphql(query):
    url = "https://api.github.com/graphql"
    data = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Wildchu-Profile-Generator"
    })
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def fetch_rest(url):
     headers = {"User-Agent": "Wildchu-Profile-Generator"}
     if TOKEN:
         headers["Authorization"] = f"Bearer {TOKEN}"
     req = urllib.request.Request(url, headers=headers)
     with urllib.request.urlopen(req) as resp:
         return json.loads(resp.read().decode("utf-8"))

def main():
    # Ambil data realtime via GraphQL (jika token tersedia) atau fallback REST
    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
          totalCount
          nodes {
            stargazerCount
            forkCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node { name color }
              }
            }
          }
        }
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
              }
            }
          }
        }
      }
    }
    """ % USERNAME

    stars, forks, repos, commits, total_contribs = 0, 0, 0, 0, 0
    lang_Map = {}
    weeks = []

    if TOKEN:
        res = fetch_graphql(query)
        user = res.get("data", {}).get("user", {})
        if user:
            repo_data = user["repositories"]
            repos = repo_data["totalCount"]
            for r in repo_data["nodes"]:
                stars += r["stargazerCount"]
                forks += r["forkCount"]
                for edge in r["languages"]["edges"]:
                    lname = edge["node"]["name"]
                    lcolor = edge["node"]["color"] or "#ff2a4b"
                    lang_Map[lname] = lang_Map.get(lname, {"size": 0, "color": lcolor})
                    lang_Map[lname]["size"] += edge["size"]

            cc = user["contributionsCollection"]
            commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
            cal = cc["contributionCalendar"]
            total_contribs = cal["totalContributions"]
            weeks = cal["weeks"][-42:] # Ambil 42 minggu terakhir agar pas di card

    # Hitung persentase bahasa secara live
    total_size = sum(v["size"] for v in lang_Map.values()) or 1
    sorted_langs = sorted(lang_Map.items(), key=lambda x: x[1]["size"], reverse=True)[:10]

    # Render bar Stack Analytics & Legend
    bar_svg = ""
    legend_svg = ""
    cur_x = 0
    total_bar_width = 790

    for idx, (lname, ldata) in enumerate(sorted_langs):
        pct = round((ldata["size"] / total_size) * 100, 1)
        w = max(8, int((ldata["size"] / total_size) * total_bar_width))
        if cur_x + w > total_bar_width:
            w = max(0, total_bar_width - cur_x)
        if w > 0:
            bar_svg += f'<rect x="{cur_x}" y="0" width="{w}" height="9" rx="4.5" fill="{ldata["color"]}" />'
            cur_x += w + 4

        row = idx // 5
        col = idx % 5
        lx = col * 160
        ly = row * 32
        legend_svg += f'''
        <g transform="translate({lx}, {ly})">
          <circle cx="6" cy="-4" r="5" fill="{ldata["color"]}" />
          <text x="18" y="0" class="lang-name">{lname}</text>
          <text x="105" y="0" class="lang-pct">{pct}%</text>
        </g>'''

    # Render kotak-kotak Activity Pulse (Gradasi Merah berdasarkan jumlah kontribusi asli)
    pulse_cells = ""
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week["contributionDays"]):
            cnt = day["contributionCount"]
            x = w_idx * 19
            y = d_idx * 16
            if cnt == 0:
                color = "#12151e"
            elif cnt == 1:
                color = "#4c0519"
            elif cnt <= 3:
                color = "#881337"
            elif cnt <= 6:
                color = "#e11d48"
            elif cnt <= 10:
                color = "#ff2a4b"
            else:
                color = "#ffe4e6" # Merah terang menyala untuk commit banyak
            pulse_cells += f'<rect x="{x}" y="{y}" width="14" height="12" rx="3" fill="{color}" />\n'

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 920" width="100%" height="100%">
  <defs>
    <radialGradient id="redGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff1e42" stop-opacity="0.38" />
      <stop offset="60%" stop-color="#79103c" stop-opacity="0.15" />
      <stop offset="100%" stop-color="#0a0c12" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="purpleGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#8b2cf5" stop-opacity="0.32" />
      <stop offset="65%" stop-color="#3a0ca3" stop-opacity="0.1" />
      <stop offset="100%" stop-color="#0a0c12" stop-opacity="0" />
    </radialGradient>
    <filter id="textGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <style>
      .title {{ font: 800 44px 'Segoe UI', -apple-system, sans-serif; fill: #ffffff; letter-spacing: 14px; }}
      .role {{ font: 600 12px 'JetBrains Mono', monospace; fill: #ff2a4b; letter-spacing: 5px; }}
      .subrole {{ font: 500 11px 'JetBrains Mono', monospace; fill: #d8b4fe; letter-spacing: 3px; }}
      .techline {{ font: 500 10px 'JetBrains Mono', monospace; fill: #ff4d6d; letter-spacing: 2.5px; }}
      .link {{ font: 400 11px 'JetBrains Mono', monospace; fill: #4b5563; letter-spacing: 1px; }}
      .pill-text {{ font: 600 12px 'Segoe UI', sans-serif; }}
      .stat-num {{ font: 800 30px 'Segoe UI', sans-serif; fill: #ffffff; }}
      .stat-lbl {{ font: 700 10px 'JetBrains Mono', monospace; letter-spacing: 2.5px; }}
      .sec-hdr {{ font: 700 11px 'JetBrains Mono', monospace; fill: #ff3355; letter-spacing: 3.5px; }}
      .lang-name {{ font: 600 12px 'Segoe UI', sans-serif; fill: #e5e7eb; }}
      .lang-pct {{ font: 400 11px 'JetBrains Mono', monospace; fill: #9ca3af; }}
      .divider {{ stroke: #181c26; stroke-width: 1; }}
    </style>
  </defs>

  <rect width="900" height="920" rx="18" fill="#090b10" stroke="#181c26" stroke-width="1.5" />
  <ellipse cx="340" cy="155" rx="280" ry="130" fill="url(#purpleGlow)" />
  <ellipse cx="590" cy="185" rx="240" ry="110" fill="url(#redGlow)" />
  <ellipse cx="450" cy="480" rx="340" ry="90" fill="url(#redGlow)" />
  <ellipse cx="700" cy="670" rx="220" ry="110" fill="url(#purpleGlow)" />

  <path d="M 35 48 L 35 35 L 48 35" fill="none" stroke="#ff2a4b" stroke-width="2" stroke-linecap="round" />
  <path d="M 865 48 L 865 35 L 852 35" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" />
  <path d="M 35 282 L 35 295 L 48 295" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" />
  <path d="M 865 282 L 865 295 L 852 295" fill="none" stroke="#ff2a4b" stroke-width="2" stroke-linecap="round" />

  <text x="457" y="115" text-anchor="middle" class="title" filter="url(#textGlow)">WILDCHU</text>
  <text x="450" y="160" text-anchor="middle" class="role">S O F T W A R E   E N G I N E E R</text>
  <text x="450" y="200" text-anchor="middle" class="subrole">BACKEND DEVELOPER | AI AUTOMATION</text>
  <text x="450" y="226" text-anchor="middle" class="techline">REST APIs • AI BOTS • C++ PLUGINS • SERVER AUTOMATION</text>
  <text x="450" y="258" text-anchor="middle" class="link">github.com/wildchu</text>

  <line x1="40" y1="320" x2="860" y2="320" class="divider" />

  <g transform="translate(72, 345)">
    <rect x="0" y="0" width="76" height="32" rx="16" fill="#0d1017" stroke="#2d1622" stroke-width="1.2" />
    <text x="38" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">PHP</text>
    <rect x="88" y="0" width="94" height="32" rx="16" fill="#0d1017" stroke="#27173a" stroke-width="1.2" />
    <text x="135" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">Python</text>
    <rect x="194" y="0" width="80" height="32" rx="16" fill="#0d1017" stroke="#2d1622" stroke-width="1.2" />
    <text x="234" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">C++</text>
    <rect x="286" y="0" width="110" height="32" rx="16" fill="#0d1017" stroke="#1e2230" stroke-width="1.2" />
    <text x="341" y="20" text-anchor="middle" class="pill-text" fill="#f8fafc">JavaScript</text>
    <rect x="408" y="0" width="90" height="32" rx="16" fill="#0d1017" stroke="#27173a" stroke-width="1.2" />
    <text x="453" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">MySQL</text>
    <rect x="510" y="0" width="112" height="32" rx="16" fill="#0d1017" stroke="#2d1622" stroke-width="1.2" />
    <text x="566" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">PostgreSQL</text>
    <rect x="634" y="0" width="118" height="32" rx="16" fill="#0d1017" stroke="#27173a" stroke-width="1.2" />
    <text x="693" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">Automation</text>
  </g>

  <line x1="40" y1="405" x2="860" y2="405" class="divider" />

  <!-- LIVE STATS COUNTER -->
  <g transform="translate(0, 465)">
    <text x="165" y="0" text-anchor="middle" class="stat-num">{stars}</text>
    <text x="165" y="24" text-anchor="middle" class="stat-lbl" fill="#f59e0b">STARS</text>
    <line x1="260" y1="-28" x2="260" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="355" y="0" text-anchor="middle" class="stat-num">{forks}</text>
    <text x="355" y="24" text-anchor="middle" class="stat-lbl" fill="#c084fc">FORKS</text>
    <line x1="450" y1="-28" x2="450" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="545" y="0" text-anchor="middle" class="stat-num">{repos}</text>
    <text x="545" y="24" text-anchor="middle" class="stat-lbl" fill="#38bdf8">REPOS</text>
    <line x1="640" y1="-28" x2="640" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="735" y="0" text-anchor="middle" class="stat-num">{commits}</text>
    <text x="735" y="24" text-anchor="middle" class="stat-lbl" fill="#ff2a4b">COMMITS</text>
  </g>

  <line x1="40" y1="535" x2="860" y2="535" class="divider" />

  <!-- LIVE STACK ANALYTICS -->
  <text x="55" y="572" class="sec-hdr">S T A C K   A N A L Y T I C S</text>
  <g transform="translate(55, 592)">
    {bar_svg}
  </g>
  <g transform="translate(55, 632)">
    {legend_svg}
  </g>

  <line x1="40" y1="705" x2="860" y2="705" class="divider" />

  <!-- LIVE ACTIVITY PULSE -->
  <text x="55" y="740" class="sec-hdr">A C T I V I T Y   P U L S E</text>
  <text x="845" y="740" text-anchor="end" class="lang-pct">{total_contribs} contributions</text>

  <g transform="translate(55, 760)">
    {pulse_cells}
  </g>
</svg>'''

    with open("profile-card.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

if __name__ == "__main__":
    main()
