import os
import json
import urllib.request

USERNAME = "wildchu"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# === KUSTOMISASI QUOTES DI SINI ===
MAIN_QUOTE = "STILL LEARNING • DIVING DEEPER"
SUB_QUOTE = "CURIOSITY-DRIVEN BUILDER | UNRAVELING HOW THINGS WORK"
MANTRA_LINE = "SURFACE LEVEL IS NEVER ENOUGH • ALWAYS EXPLORING THE UNKNOWN"

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

def main():
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
    lang_map = {}
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
                    lang_map[lname] = lang_map.get(lname, {"size": 0, "color": lcolor})
                    lang_map[lname]["size"] += edge["size"]

            cc = user["contributionsCollection"]
            commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
            cal = cc["contributionCalendar"]
            total_contribs = cal["totalContributions"]
            weeks = cal["weeks"][-42:]

    total_size = sum(v["size"] for v in lang_map.values()) or 1
    sorted_langs = sorted(lang_map.items(), key=lambda x: x[1]["size"], reverse=True)[:10]

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

    pulse_cells = ""
    for w_idx, week in enumerate(weeks):
        for d_idx, day in enumerate(week["contributionDays"]):
            cnt = day["contributionCount"]
            x = w_idx * 19
            y = d_idx * 16
            extra_class = ""
            if cnt == 0:
                color = "#12151e"
            elif cnt == 1:
                color = "#4c0519"
            elif cnt <= 3:
                color = "#881337"
            elif cnt <= 6:
                color = "#e11d48"
                extra_class = 'class="pulse-glow"'
            elif cnt <= 10:
                color = "#ff2a4b"
                extra_class = 'class="pulse-glow"'
            else:
                color = "#ffe4e6"
                extra_class = 'class="pulse-hot"'
            pulse_cells += f'<rect x="{x}" y="{y}" width="14" height="12" rx="3" fill="{color}" {extra_class} />\n'

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 920" width="100%" height="100%">
  <defs>
    <radialGradient id="redGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#ff1e42" stop-opacity="0.42" />
      <stop offset="55%" stop-color="#79103c" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#090b10" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="purpleGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#8b2cf5" stop-opacity="0.36" />
      <stop offset="60%" stop-color="#3a0ca3" stop-opacity="0.12" />
      <stop offset="100%" stop-color="#090b10" stop-opacity="0" />
    </radialGradient>
    <filter id="textGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <filter id="cellGlow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="2.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <style>
      .title {{ font: 800 44px 'Segoe UI', -apple-system, sans-serif; fill: #ffffff; letter-spacing: 14px; }}
      .role {{ font: 600 12px 'JetBrains Mono', monospace; fill: #ff2a4b; letter-spacing: 4.5px; }}
      .subrole {{ font: 500 11px 'JetBrains Mono', monospace; fill: #e9d5ff; letter-spacing: 2.5px; }}
      .techline {{ font: 500 10px 'JetBrains Mono', monospace; fill: #ff4d6d; letter-spacing: 2px; opacity: 0.9; }}
      .link {{ font: 400 11px 'JetBrains Mono', monospace; fill: #4b5563; letter-spacing: 1px; }}
      .pill-text {{ font: 600 12px 'Segoe UI', sans-serif; }}
      .stat-num {{ font: 800 30px 'Segoe UI', sans-serif; fill: #ffffff; }}
      .stat-lbl {{ font: 700 10px 'JetBrains Mono', monospace; letter-spacing: 2.5px; }}
      .sec-hdr {{ font: 700 11px 'JetBrains Mono', monospace; fill: #ff3355; letter-spacing: 3.5px; }}
      .lang-name {{ font: 600 12px 'Segoe UI', sans-serif; fill: #e5e7eb; }}
      .lang-pct {{ font: 400 11px 'JetBrains Mono', monospace; fill: #9ca3af; }}
      .divider {{ stroke: #181c26; stroke-width: 1; }}
      
      @keyframes twinkle {{
        0%, 100% {{ opacity: 0.2; transform: scale(0.8); }}
        50% {{ opacity: 0.95; transform: scale(1.3); }}
      }}
      @keyframes pulseCell {{
        0%, 100% {{ opacity: 0.82; }}
        50% {{ opacity: 1; }}
      }}
      .star-1 {{ animation: twinkle 4s ease-in-out infinite; }}
      .star-2 {{ animation: twinkle 5.5s ease-in-out infinite 1.5s; }}
      .star-3 {{ animation: twinkle 3.5s ease-in-out infinite 0.7s; }}
      .pulse-glow {{ filter: url(#cellGlow); animation: pulseCell 3s infinite ease-in-out; }}
      .pulse-hot {{ filter: url(#cellGlow); animation: pulseCell 1.8s infinite ease-in-out; }}
    </style>
  </defs>

  <!-- Main Card Background -->
  <rect width="900" height="920" rx="18" fill="#090b10" stroke="#181c26" stroke-width="1.5" />

  <!-- Animated Ambient Orbs (Breathing & Floating Effect like ACE) -->
  <ellipse cx="330" cy="155" rx="280" ry="130" fill="url(#purpleGlow)">
    <animate attributeName="rx" values="260;310;260" dur="9s" repeatCount="indefinite" />
    <animate attributeName="cx" values="330;355;330" dur="11s" repeatCount="indefinite" />
  </ellipse>
  <ellipse cx="590" cy="185" rx="240" ry="110" fill="url(#redGlow)">
    <animate attributeName="rx" values="230;275;230" dur="8s" repeatCount="indefinite" />
    <animate attributeName="cy" values="185;165;185" dur="10s" repeatCount="indefinite" />
  </ellipse>
  <ellipse cx="450" cy="480" rx="340" ry="95" fill="url(#redGlow)">
    <animate attributeName="opacity" values="0.7;1;0.7" dur="6s" repeatCount="indefinite" />
  </ellipse>
  <ellipse cx="700" cy="670" rx="220" ry="110" fill="url(#purpleGlow)" />

  <!-- Subtle Radar Circles Behind Hero (ACE Signature Effect) -->
  <circle cx="450" cy="155" r="105" fill="none" stroke="#ffffff" stroke-opacity="0.03" stroke-width="1" />
  <circle cx="450" cy="155" r="145" fill="none" stroke="#ff2a4b" stroke-opacity="0.04" stroke-width="1" stroke-dasharray="4 6" />

  <!-- Twinkling Star Particles -->
  <circle cx="95" cy="115" r="2" fill="#ff2a4b" class="star-1" />
  <circle cx="805" cy="175" r="2.2" fill="#a855f7" class="star-2" />
  <circle cx="740" cy="95" r="1.5" fill="#ffffff" class="star-3" />
  <circle cx="155" cy="235" r="1.5" fill="#c084fc" class="star-2" />
  <circle cx="320" cy="700" r="1.8" fill="#ff4d6d" class="star-1" />

  <!-- HUD Corner Brackets -->
  <path d="M 35 48 L 35 35 L 48 35" fill="none" stroke="#ff2a4b" stroke-width="2" stroke-linecap="round" />
  <path d="M 865 48 L 865 35 L 852 35" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" />
  <path d="M 35 282 L 35 295 L 48 295" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" />
  <path d="M 865 282 L 865 295 L 852 295" fill="none" stroke="#ff2a4b" stroke-width="2" stroke-linecap="round" />

  <!-- HERO HEADER & QUOTES -->
  <text x="457" y="112" text-anchor="middle" class="title" filter="url(#textGlow)">WILDCHU</text>
  <text x="450" y="158" text-anchor="middle" class="role">{MAIN_QUOTE}</text>
  <text x="450" y="198" text-anchor="middle" class="subrole">{SUB_QUOTE}</text>
  <text x="450" y="225" text-anchor="middle" class="techline">{MANTRA_LINE}</text>
  <text x="450" y="260" text-anchor="middle" class="link">github.com/wildchu</text>

  <line x1="40" y1="320" x2="860" y2="320" class="divider" />

  <!-- TECH STACK PILLS -->
  <g transform="translate(72, 345)">
    <rect x="0" y="0" width="76" height="32" rx="16" fill="#0d1017" stroke="#3b1728" stroke-width="1.2" />
    <text x="38" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">PHP</text>
    <rect x="88" y="0" width="94" height="32" rx="16" fill="#0d1017" stroke="#2e1a47" stroke-width="1.2" />
    <text x="135" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">Python</text>
    <rect x="194" y="0" width="80" height="32" rx="16" fill="#0d1017" stroke="#3b1728" stroke-width="1.2" />
    <text x="234" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">C++</text>
    <rect x="286" y="0" width="110" height="32" rx="16" fill="#0d1017" stroke="#222738" stroke-width="1.2" />
    <text x="341" y="20" text-anchor="middle" class="pill-text" fill="#f8fafc">JavaScript</text>
    <rect x="408" y="0" width="90" height="32" rx="16" fill="#0d1017" stroke="#2e1a47" stroke-width="1.2" />
    <text x="453" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">MySQL</text>
    <rect x="510" y="0" width="112" height="32" rx="16" fill="#0d1017" stroke="#3b1728" stroke-width="1.2" />
    <text x="566" y="20" text-anchor="middle" class="pill-text" fill="#ff4d6d">PostgreSQL</text>
    <rect x="634" y="0" width="118" height="32" rx="16" fill="#0d1017" stroke="#2e1a47" stroke-width="1.2" />
    <text x="693" y="20" text-anchor="middle" class="pill-text" fill="#c084fc">Automation</text>
  </g>

  <line x1="40" y1="405" x2="860" y2="405" class="divider" />

  <!-- LIVE STATS COUNTER -->
  <g transform="translate(0, 465)">
    <text x="165" y="0" text-anchor="middle" class="stat-num" filter="url(#textGlow)">{stars}</text>
    <text x="165" y="24" text-anchor="middle" class="stat-lbl" fill="#f59e0b">STARS</text>
    <line x1="260" y1="-28" x2="260" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="355" y="0" text-anchor="middle" class="stat-num" filter="url(#textGlow)">{forks}</text>
    <text x="355" y="24" text-anchor="middle" class="stat-lbl" fill="#c084fc">FORKS</text>
    <line x1="450" y1="-28" x2="450" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="545" y="0" text-anchor="middle" class="stat-num" filter="url(#textGlow)">{repos}</text>
    <text x="545" y="24" text-anchor="middle" class="stat-lbl" fill="#38bdf8">REPOS</text>
    <line x1="640" y1="-28" x2="640" y2="30" stroke="#181c26" stroke-dasharray="3,3" />

    <text x="735" y="0" text-anchor="middle" class="stat-num" filter="url(#textGlow)">{commits}</text>
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
