#!/usr/bin/env python3
"""Generate F1 visualization HTML files from pre-processed JSON data."""
import json, os, sys

DRIVERS = {
    "1": {"tla": "NOR", "team": "McLaren", "color": "#FF8000"},
    "3": {"tla": "VER", "team": "Red Bull", "color": "#4781D7"},
    "5": {"tla": "BOR", "team": "Audi", "color": "#F50537"},
    "6": {"tla": "HAD", "team": "Red Bull", "color": "#4781D7"},
    "10": {"tla": "GAS", "team": "Alpine", "color": "#00A1E8"},
    "11": {"tla": "PER", "team": "Cadillac", "color": "#909090"},
    "12": {"tla": "ANT", "team": "Mercedes", "color": "#27F4D2"},
    "14": {"tla": "ALO", "team": "Aston Martin", "color": "#229971"},
    "16": {"tla": "LEC", "team": "Ferrari", "color": "#ED1131"},
    "18": {"tla": "STR", "team": "Aston Martin", "color": "#229971"},
    "23": {"tla": "ALB", "team": "Williams", "color": "#1868DB"},
    "27": {"tla": "HUL", "team": "Audi", "color": "#F50537"},
    "30": {"tla": "LAW", "team": "RB", "color": "#6C98FF"},
    "31": {"tla": "OCO", "team": "Haas", "color": "#9C9FA2"},
    "41": {"tla": "LIN", "team": "RB", "color": "#6C98FF"},
    "43": {"tla": "COL", "team": "Alpine", "color": "#00A1E8"},
    "44": {"tla": "HAM", "team": "Ferrari", "color": "#ED1131"},
    "55": {"tla": "SAI", "team": "Williams", "color": "#1868DB"},
    "63": {"tla": "RUS", "team": "Mercedes", "color": "#27F4D2"},
    "77": {"tla": "BOT", "team": "Cadillac", "color": "#909090"},
    "81": {"tla": "PIA", "team": "McLaren", "color": "#FF8000"},
    "87": {"tla": "BEA", "team": "Haas", "color": "#9C9FA2"},
}

DRIVERS_JS = json.dumps(DRIVERS, separators=(',', ':'))

COMPOUND_COLORS = {
    "SOFT": "#FF3333", "MEDIUM": "#FFD700", "HARD": "#C0C0C0",
    "INTERMEDIATE": "#00CC00", "WET": "#3366FF", "UNKNOWN": "#666"
}

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def wrap_html(title, flag, css, js):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#1a1a2e;color:#e0e0e0;min-height:100vh;padding:1rem}}
h1{{font-size:1.5rem;margin-bottom:1rem;text-align:center}}
h2{{font-size:1.1rem;margin:1.5rem 0 .8rem;color:#00d4ff}}
a{{color:#00d4ff;text-decoration:none}}
a:hover{{text-decoration:underline}}
.back{{display:inline-block;margin-bottom:1rem;font-size:.9rem}}
{css}
</style>
</head>
<body>
<a class="back" href="index.html">← Back</a>
<h1>{flag} {title}</h1>
<div id="app"></div>
<script>
const DRIVERS={DRIVERS_JS};
(function(){{{js}}})();
</script>
</body>
</html>'''

def gen_pitstops(data_dir, flag, title):
    data = load_json(f"{data_dir}/pitstops.json")
    if not data:
        return None
    
    # Extract pit stops per driver
    stops = {}
    for num, driver_data in data.items():
        if num == '_deleted' or not isinstance(driver_data, dict):
            continue
        laps = driver_data.get('Laps', {})
        if isinstance(laps, dict):
            for lap_num, lap_data in laps.items():
                pit = lap_data.get('PitOutTime', '')
                if pit and isinstance(pit, str) and pit != '':
                    if num not in stops:
                        stops[num] = []
                    # Try to get duration
                    dur = lap_data.get('Duration', '')
                    stops[num].append({'lap': int(lap_num), 'time': pit, 'duration': dur})
    
    data_js = json.dumps(stops, separators=(',', ':'))
    
    css = '''
.bar-row{display:flex;align-items:center;margin:.3rem 0}
.bar-label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.85rem}
.bar-track{flex:1;background:#2a2a4a;border-radius:4px;height:24px;position:relative}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:.75rem;font-weight:600;min-width:30px}
.stats{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}
.stat{background:#16213e;border-radius:8px;padding:1rem;text-align:center;flex:1;min-width:120px}
.stat .val{font-size:1.8rem;font-weight:700;color:#00d4ff}
.stat .label{font-size:.75rem;color:#888;margin-top:.3rem}
'''
    
    js = f'''
const DATA={data_js};
const drivers=[];
for(const[num,entries]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  entries.forEach(e=>drivers.push({{num,tla:d.tla,team:d.team,color:d.color,lap:e.lap,time:e.time,duration:e.duration}}));
}}
drivers.sort((a,b)=>a.lap-b.lap);
const app=document.getElementById('app');
let html='<div class="stats">';
html+=`<div class="stat"><div class="val">${{drivers.length}}</div><div class="label">Total Pit Stops</div></div>`;
const teams={{}};
drivers.forEach(d=>{{if(!teams[d.team])teams[d.team]={{name:d.team,color:d.color,count:0}};teams[d.team].count++}});
html+=`<div class="stat"><div class="val">${{Object.keys(teams).length}}</div><div class="label">Teams Pitting</div></div>`;
html+='</div>';
html+='<h2>Pit Stop Timeline</h2>';
drivers.forEach(d=>{{
  const pct=((d.lap)/(58))*100;
  html+=`<div class="bar-row"><span class="bar-label">${{d.tla}}</span><div class="bar-track"><div class="bar-fill" style="width:${{Math.max(pct,2)}}%;background:${{d.color}}">Lap ${{d.lap}}</div></div></div>`;
}});
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_weather(data_dir, flag, title):
    data = load_json(f"{data_dir}/weather.json")
    if not data:
        return None
    data_js = json.dumps(data[:50], separators=(',', ':'))  # limit
    
    css = '''
canvas{width:100%;height:300px;display:block;margin:1rem 0}
.stat{display:inline-block;background:#16213e;border-radius:8px;padding:.5rem 1rem;margin:.3rem}
.stat .val{font-size:1.2rem;font-weight:700;color:#00d4ff}
'''
    
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
if(!DATA.length){{app.innerHTML='<p>No weather data</p>';return;}}
const temps=DATA.map(d=>parseFloat(d.AirTemp||0)).filter(v=>!isNaN(v));
const tracks=DATA.map(d=>parseFloat(d.TrackTemp||0)).filter(v=>!isNaN(v));
const humid=DATA.map(d=>parseFloat(d.Humidity||0)).filter(v=>!isNaN(v));
html='<div>';
if(temps.length)html+=`<span class="stat">Air: <span class="val">${{Math.min(...temps).toFixed(1)}}–${{Math.max(...temps).toFixed(1)}}°C</span></span>`;
if(tracks.length)html+=`<span class="stat">Track: <span class="val">${{Math.min(...tracks).toFixed(1)}}–${{Math.max(...tracks).toFixed(1)}}°C</span></span>`;
if(humid.length)html+=`<span class="stat">Humidity: <span class="val">${{Math.min(...humid).toFixed(0)}}–${{Math.max(...humid).toFixed(0)}}%</span></span>`;
html+='</div>';
// Simple canvas chart
html+='<h2>Temperature</h2><canvas id="chart"></canvas>';
app.innerHTML=html;
const c=document.getElementById('chart');
const ctx=c.getContext('2d');
const dpr=window.devicePixelRatio||1;
c.width=c.parentElement.clientWidth*dpr;c.height=300*dpr;c.style.height='300px';
const W=c.width/dpr,H=c.height/dpr;ctx.scale(dpr,dpr);
ctx.clearRect(0,0,W,H);
const all=[...temps,...tracks];
const mn=Math.min(...all)-2,mx=Math.max(...all)+2;
function drawLine(data,color){{
  ctx.beginPath();ctx.strokeStyle=color;ctx.lineWidth=2;
  data.forEach((v,i)=>{{const x=i/(data.length-1)*W;const y=H-(v-mn)/(mx-mn)*H;if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y)}});
  ctx.stroke();
}}
if(temps.length)drawLine(temps,'#FF6B6B');
if(tracks.length)drawLine(tracks,'#4ECDC4');
'''
    return wrap_html(title, flag, css, js)

def gen_overtakes(data_dir, flag, title):
    data = load_json(f"{data_dir}/overtakes.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.bar-row{display:flex;align-items:center;margin:.3rem 0}
.bar-label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.85rem}
.bar-track{flex:1;background:#2a2a4a;border-radius:4px;height:24px;position:relative;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:.8rem;font-weight:600;color:#000;min-width:24px}
.king{{background:#16213e;border-radius:12px;padding:1.5rem;text-align:center;margin:1rem 0;border:2px solid #FFD700}}
.king .emoji{{font-size:3rem}}
.king .name{{font-size:1.5rem;font-weight:700;margin:.5rem 0}}
.stats{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}}
.stat{{background:#16213e;border-radius:8px;padding:1rem;text-align:center;flex:1;min-width:120px}}
.stat .val{{font-size:1.8rem;font-weight:700;color:#00d4ff}}
.stat .label{{font-size:.75rem;color:#888;margin-top:.3rem}}
'''
    
    js = f'''
const DATA={data_js};
const drivers=[];
for(const[num,entries]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  const total=entries.reduce((s,e)=>s+e.count,0);
  drivers.push({{num,tla:d.tla,team:d.team,color:d.color,entries,total}});
}}
drivers.sort((a,b)=>b.total-a.total);
const totalOT=drivers.reduce((s,d)=>s+d.total,0);
const king=drivers[0];
let html='';
if(king)html+=`<div class="king"><div class="emoji">👑</div><div class="name" style="color:${{king.color}}">${{king.tla}}</div><div>${{king.team}} · ${{king.total}} overtakes</div></div>`;
html+='<div class="stats">';
html+=`<div class="stat"><div class="val">${{totalOT}}</div><div class="label">Total Overtakes</div></div>`;
html+=`<div class="stat"><div class="val">${{(totalOT/drivers.length).toFixed(1)}}</div><div class="label">Avg per Driver</div></div>`;
html+=`<div class="stat"><div class="val">${{drivers.length}}</div><div class="label">Drivers</div></div>`;
html+='</div>';
html+='<h2>All Drivers</h2>';
const maxT=drivers[0]?.total||1;
drivers.forEach(d=>{{
  const pct=d.total/maxT*100;
  html+=`<div class="bar-row"><span class="bar-label">${{d.tla}}</span><div class="bar-track"><div class="bar-fill" style="width:${{pct}}%;background:${{d.color}}">${{d.total}}</div></div></div>`;
}});
document.getElementById('app').innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_track_map(data_dir, flag, title):
    data = load_json(f"{data_dir}/track.json")
    if not data:
        return None
    # Subsample more aggressively for embed
    track = data.get('track', [])
    step = max(1, len(track) // 800)
    sub = track[::step]
    embed = {'track': sub, 'cars': data.get('cars', {})}
    data_js = json.dumps(embed, separators=(',', ':'))
    
    css = 'canvas{width:100%;height:500px;display:block;background:#0d0d1a;border-radius:8px;margin:1rem 0}'
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
const c=document.createElement('canvas');c.id='map';app.appendChild(c);
const ctx=c.getContext('2d');
const dpr=window.devicePixelRatio||1;
const w=c.parentElement.clientWidth;c.width=w*dpr;c.height=500*dpr;c.style.height='500px';
const W=c.width/dpr,H=c.height/dpr;ctx.scale(dpr,dpr);
const pts=DATA.track;
if(!pts.length){{ctx.fillStyle='#888';ctx.fillText('No track data',W/2-50,H/2);return;}}
const xs=pts.map(p=>p.x),ys=pts.map(p=>p.y);
const xMin=Math.min(...xs),xMax=Math.max(...xs),yMin=Math.min(...ys),yMax=Math.max(...ys);
const pad=40;const xRange=xMax-xMin||1;const yRange=yMax-yMin||1;
const scale=Math.min((W-2*pad)/xRange,(H-2*pad)/yRange);
const ox=pad+((W-2*pad)-xRange*scale)/2;
const oy=pad+((H-2*pad)-yRange*scale)/2;
function tx(x){{return ox+(x-xMin)*scale}}
function ty(y){{return oy+(yMax-y)*scale}}
// Draw track
ctx.beginPath();ctx.strokeStyle='#444';ctx.lineWidth=6;ctx.lineJoin='round';
pts.forEach((p,i)=>{{if(!i)ctx.moveTo(tx(p.x),ty(p.y));else ctx.lineTo(tx(p.x),ty(p.y))}});
ctx.closePath();ctx.stroke();
ctx.strokeStyle='#666';ctx.lineWidth=2;ctx.stroke();
// Draw cars
for(const[num,pos]of Object.entries(DATA.cars)){{
  const d=DRIVERS[num];if(!d)continue;
  const x=tx(pos.x),y=ty(pos.y);
  ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.fillStyle=d.color;ctx.fill();
  ctx.fillStyle='#fff';ctx.font='bold 9px sans-serif';ctx.textAlign='center';ctx.fillText(d.tla,x,y-12);
}}
'''
    return wrap_html(title, flag, css, js)

def gen_race_control(data_dir, flag, title):
    data = load_json(f"{data_dir}/race_control.json")
    if not data:
        return None
    # Limit messages
    msgs = data[:100]
    data_js = json.dumps(msgs, separators=(',', ':'))
    
    css = '''
.filters{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}
.filter-btn{background:#2a2a4a;border:1px solid #3a3a5a;color:#aaa;padding:.4rem .8rem;border-radius:6px;cursor:pointer;font-size:.8rem}
.filter-btn.active{background:#00d4ff;color:#000;border-color:#00d4ff}
.msg{{background:#16213e;border-radius:8px;padding:.8rem 1rem;margin:.4rem 0;border-left:4px solid #444;font-size:.85rem}}
.msg.Flag{border-left-color:#FFD700}.msg.SafetyCar{border-left-color:#FF4444}
.msg.Penalty{border-left-color:#FF6B6B}.msg.DRS{border-left-color:#00CC00}
.msg .lap{{color:#00d4ff;font-weight:600;margin-right:.5rem}}
.msg .cat{{color:#888;font-size:.75rem;margin-left:.5rem}}
'''
    js = f'''
const DATA={data_js};
const cats=[...new Set(DATA.map(m=>m.Category||'Other'))].sort();
let activeFilter='all';
const app=document.getElementById('app');
let html='<div class="filters"><button class="filter-btn active" onclick="setFilter(\\'all\\')">All ('+DATA.length+')</button>';
cats.forEach(c=>{{
  const cnt=DATA.filter(m=>(m.Category||'Other')===c).length;
  html+=`<button class="filter-btn" onclick="setFilter('${{c}}')">${{c}} (${{cnt}})</button>`;
}});
html+='</div><div id="msgs"></div>';
app.innerHTML=html;
function setFilter(f){{
  activeFilter=f;
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.toggle('active',b.textContent.startsWith(f==='all'?'All':f)));
  const filtered=f==='all'?DATA:DATA.filter(m=>(m.Category||'Other')===f);
  let mh='';
  filtered.forEach(m=>{{
    const cat=m.Category||'Other';
    mh+=`<div class="msg ${{cat}}">${{m.Lap?'<span class="lap">Lap '+m.Lap+'</span>':''}}${{m.Message||m.message||''}}<span class="cat">${{cat}}</span></div>`;
  }});
  document.getElementById('msgs').innerHTML=mh;
}}
setFilter('all');
'''
    return wrap_html(title, flag, css, js)

def gen_championship(data_dir, flag, title):
    data = load_json(f"{data_dir}/championship.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.bar-row{display:flex;align-items:center;margin:.3rem 0}
.bar-label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.85rem}
.bar-track{flex:1;background:#2a2a4a;border-radius:4px;height:24px;position:relative;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:.8rem;font-weight:600;color:#000;min-width:24px}
.leader{background:#16213e;border-radius:12px;padding:1.5rem;text-align:center;margin:1rem 0}
.leader .val{font-size:2.5rem;font-weight:700}
'''
    
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
const drv=DATA.drivers||{{}};
const sorted=Object.entries(drv).sort((a,b)=>b[1]-a[1]);
const leader=sorted[0];
const d=DRIVERS[leader?.[0]];
let html='';
if(d)html+=`<div class="leader"><div>Championship Leader</div><div class="val" style="color:${{d.color}}">${{d.tla}}</div><div>${{d.team}} · ${{leader[1]}} pts</div></div>`;
html+='<h2>Driver Standings</h2>';
const maxPts=leader?.[1]||1;
sorted.forEach(([num,pts])=>{{
  const dr=DRIVERS[num];
  if(!dr)return;
  const pct=pts/maxPts*100;
  html+=`<div class="bar-row"><span class="bar-label">${{dr.tla}}</span><div class="bar-track"><div class="bar-fill" style="width:${{pct}}%;background:${{dr.color}}">${{pts}}</div></div></div>`;
}});
const teams=DATA.teams||{{}};
html+='<h2>Constructor Standings</h2>';
const teamColors={{'Mercedes':'#27F4D2','Ferrari':'#ED1131','McLaren Mercedes':'#FF8000','Red Bull Racing Red Bull Ford':'#4781D7','Haas Ferrari':'#9C9FA2','Racing Bulls Red Bull Ford':'#6C98FF','Audi':'#F50537','Alpine Mercedes':'#00A1E8','Atlassian Williams Mercedes':'#1868DB','Aston Martin Aramco Honda':'#229971','Cadillac Ferrari':'#909090'}};
const tSorted=Object.entries(teams).sort((a,b)=>b[1]-a[1]);
const maxTeam=tSorted[0]?.[1]||1;
tSorted.forEach(([name,pts])=>{{
  const color=teamColors[name]||'#666';
  const pct=pts/maxTeam*100;
  html+=`<div class="bar-row"><span class="bar-label" style="font-size:.7rem">${{name.split(' ')[0]}}</span><div class="bar-track"><div class="bar-fill" style="width:${{pct}}%;background:${{color}}">${{pts}}</div></div></div>`;
}});
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_sector_analysis(data_dir, flag, title):
    data = load_json(f"{data_dir}/timing_stats.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.fastest{background:#16213e;border-radius:12px;padding:1.5rem;text-align:center;margin:1rem 0}
.fastest .val{font-size:2rem;font-weight:700;color:#00d4ff}
.sector-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin:1rem 0}
.sector-card{background:#16213e;border-radius:8px;padding:1rem}
.sector-card h3{color:#FFD700;font-size:.9rem;margin-bottom:.5rem}
.rank{display:flex;justify-content:space-between;padding:.2rem 0;font-size:.85rem;border-bottom:1px solid #2a2a4a}
.rank .pos{color:#888;width:20px}.rank .time{font-weight:600}
.medal-1{color:#FFD700}.medal-2{color:#C0C0C0}.medal-3{color:#CD7F32}
'''
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
// Find fastest lap
let fastest=null;
for(const[num,info]of Object.entries(DATA)){{
  const bl=info.PersonalBestLapTime;
  if(bl&&bl.Value&&(!fastest||bl.Position<fastest.Position))fastest={{num,...bl,driver:DRIVERS[num]}};
}}
let html='';
if(fastest&&fastest.driver)html+=`<div class="fastest"><div>Fastest Lap</div><div class="val">${{fastest.Value}}</div><div style="color:${{fastest.driver.color}}">${{fastest.driver.tla}} (${{fastest.driver.team}}) · Lap ${{fastest.Lap||'?'}}</div></div>`;
// Sectors
html+='<div class="sector-grid">';
for(let s=0;s<3;s++){{
  html+=`<div class="sector-card"><h3>Sector ${{s+1}}</h3>`;
  const entries=[];
  for(const[num,info]of Object.entries(DATA)){{
    const bs=info.BestSectors?.[s];
    if(bs&&bs.Value)entries.push({{num,pos:bs.Position||99,value:bs.Value,driver:DRIVERS[num]}});
  }}
  entries.sort((a,b)=>a.pos-b.pos);
  entries.slice(0,5).forEach((e,i)=>{{
    const mc=i<3?['medal-1','medal-2','medal-3'][i]:'';
    html+=`<div class="rank"><span class="pos ${{mc}}">P${{i+1}}</span><span style="color:${{e.driver?.color||'#fff'}}">${{e.driver?.tla||'?'}}</span><span class="time">${{e.value}}</span></div>`;
  }});
  html+='</div>';
}}
html+='</div>';
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_driver_progress(data_dir, flag, title):
    data = load_json(f"{data_dir}/driver_progress.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.grid{display:flex;flex-wrap:wrap;gap:.4rem;margin:1rem 0}
.grid-btn{background:#2a2a4a;border:1px solid #3a3a5a;color:#aaa;padding:.3rem .6rem;border-radius:6px;cursor:pointer;font-size:.75rem}
.grid-btn.active{border-color:#00d4ff;color:#00d4ff}
.card{background:#16213e;border-radius:12px;padding:1rem;margin:1rem 0;display:flex;gap:1.5rem;flex-wrap:wrap}
.card-item .val{font-size:1.5rem;font-weight:700;color:#00d4ff}
.card-item .label{font-size:.75rem;color:#888}
canvas{width:100%;height:300px;display:block;margin:1rem 0}
.changes{margin:1rem 0;font-size:.85rem}
.change{padding:.3rem 0;border-bottom:1px solid #2a2a4a}
.change .up{color:#4ECDC4}.change .down{color:#FF6B6B}
'''
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
const drivers=[];
for(const[num,progress]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  const first=progress[0]?.pos,last=progress[progress.length-1]?.pos;
  drivers.push({{num,...d,progress,first,last,gained:first-last}});
}}
drivers.sort((a,b)=>a.last-b.last);
let html='<div class="grid">';
drivers.forEach((d,i)=>{{
  html+=`<button class="grid-btn" onclick="select('${{d.num}}')" id="btn-${{d.num}}" style="border-color:${{d.color}}">${{d.tla}} P${{d.last}}</button>`;
}});
html+='</div><div id="detail"></div>';
app.innerHTML=html;
window.select=function(num){{
  document.querySelectorAll('.grid-btn').forEach(b=>b.classList.remove('active'));
  const btn=document.getElementById('btn-'+num);if(btn)btn.classList.add('active');
  const d=drivers.find(d=>d.num===num);if(!d)return;
  let h=`<div class="card"><div class="card-item"><div class="val" style="color:${{d.color}}">${{d.tla}}</div><div class="label">${{d.team}}</div></div>`;
  h+=`<div class="card-item"><div class="val">P${{d.first}} → P${{d.last}}</div><div class="label">${{d.gained>0?'+':''}}${{d.gained}} positions</div></div>`;
  const best=Math.min(...d.progress.map(p=>p.pos));
  h+=`<div class="card-item"><div class="val">P${{best}}</div><div class="label">Best Position</div></div></div>`;
  h+='<div class="changes">';
  for(let i=1;i<d.progress.length;i++){{
    const prev=d.progress[i-1].pos,cur=d.progress[i].pos;
    if(prev!==cur){{
      const cls=cur<prev?'up':'down';
      const arrow=cur<prev?'↑':'↓';
      h+=`<div class="change"><span class="${{cls}}">${{arrow}} P${{prev}}→P${{cur}}</span> ${{d.progress[i].ts}}</div>`;
    }}
  }}
  h+='</div>';
  document.getElementById('detail').innerHTML=h;
}};
if(drivers.length)select(drivers[0].num);
'''
    return wrap_html(title, flag, css, js)

def gen_lap_chart(data_dir, flag, title):
    data = load_json(f"{data_dir}/lap_positions.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
canvas{width:100%;height:400px;display:block;background:#0d0d1a;border-radius:8px;margin:1rem 0}
.legend{display:flex;flex-wrap:wrap;gap:.5rem;margin:1rem 0}
.leg-item{display:flex;align-items:center;gap:.3rem;font-size:.75rem;cursor:pointer;padding:.2rem .5rem;border-radius:4px;border:1px solid transparent}
.leg-item.active{border-color:#fff}
.leg-dot{width:10px;height:10px;border-radius:50%}
.stats{{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}}
.stat{{background:#16213e;border-radius:8px;padding:.8rem;text-align:center;flex:1;min-width:120px}}
.stat .val{{font-size:1.5rem;font-weight:700;color:#00d4ff}}
.stat .label{{font-size:.75rem;color:#888}}
'''
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
const drivers=[];
for(const[num,laps]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  const maxLap=Math.max(...Object.keys(laps).map(Number));
  const first=laps[1]||0,last=laps[maxLap]||0;
  drivers.push({{num,...d,laps,maxLap,first,last,gained:first-last}});
}}
const maxLap=Math.max(...drivers.map(d=>d.maxLap));
const totalDrivers=drivers.length;
// Stats
let html='<div class="stats">';
const mostGained=[...drivers].sort((a,b)=>b.gained-a.gained)[0];
const mostLost=[...drivers].sort((a,b)=>a.gained-b.gained)[0];
html+=`<div class="stat"><div class="val">${{maxLap}}</div><div class="label">Laps</div></div>`;
if(mostGained)html+=`<div class="stat"><div class="val" style="color:${{mostGained.color}}">${{mostGained.tla}} +${{mostGained.gained}}</div><div class="label">Most Gained</div></div>`;
if(mostLost)html+=`<div class="stat"><div class="val" style="color:${{mostLost.color}}">${{mostLost.tla}} ${{mostLost.gained}}</div><div class="label">Most Lost</div></div>`;
html+='</div>';
// Legend
html+='<div class="legend">';
drivers.forEach(d=>{{
  html+=`<div class="leg-item" onclick="toggle('${{d.num}}')" id="leg-${{d.num}}"><span class="leg-dot" style="background:${{d.color}}"></span>${{d.tla}}</div>`;
}});
html+='</div><canvas id="chart"></canvas>';
app.innerHTML=html;
// Draw
const c=document.getElementById('chart');
const ctx=c.getContext('2d');
const dpr=window.devicePixelRatio||1;
c.width=c.parentElement.clientWidth*dpr;c.height=400*dpr;c.style.height='400px';
const W=c.width/dpr,H=c.height/dpr;ctx.scale(dpr,dpr);
const padT=10,padB=30,padL=40,padR=10;
const cW=W-padL-padR,cH=H-padT-padB;
const active=new Set(drivers.map(d=>d.num));
window.toggle=function(num){{
  if(active.has(num))active.delete(num);else active.add(num);
  const el=document.getElementById('leg-'+num);
  if(el)el.classList.toggle('active',active.has(num));
  draw();
}};
draw();
function draw(){{
  ctx.clearRect(0,0,W,H);
  // Grid
  ctx.strokeStyle='#2a2a4a';ctx.lineWidth=1;
  for(let i=1;i<=totalDrivers;i++){{
    const y=padT+cH-(i-1)/(totalDrivers-1)*cH;
    ctx.beginPath();ctx.moveTo(padL,y);ctx.lineTo(W-padR,y);ctx.stroke();
    ctx.fillStyle='#666';ctx.font='10px sans-serif';ctx.textAlign='right';ctx.fillText('P'+i,padL-5,y+3);
  }}
  // Laps
  ctx.textAlign='center';
  for(let l=1;l<=maxLap;l+=Math.ceil(maxLap/10)){{
    const x=padL+(l/maxLap)*cW;
    ctx.fillStyle='#666';ctx.fillText('L'+l,x,H-5);
  }}
  // Lines
  drivers.forEach(d=>{{
    if(!active.has(d.num))return;
    ctx.beginPath();ctx.strokeStyle=d.color;ctx.lineWidth=2;ctx.globalAlpha=.8;
    for(let l=1;l<=d.maxLap;l++){{
      const pos=d.laps[l];if(!pos)continue;
      const x=padL+(l/maxLap)*cW;
      const y=padT+cH-((pos-1)/(totalDrivers-1))*cH;
      if(l===1)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }}
    ctx.stroke();ctx.globalAlpha=1;
  }});
}}
'''
    return wrap_html(title, flag, css, js)

def gen_pit_lane(data_dir, flag, title):
    data = load_json(f"{data_dir}/pit_lane.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.fastest{background:#16213e;border-radius:12px;padding:1.5rem;text-align:center;margin:1rem 0}
.fastest .val{font-size:2rem;font-weight:700;color:#FFD700}
.bar-row{display:flex;align-items:center;margin:.3rem 0}
.bar-label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.85rem}
.bar-track{flex:1;background:#2a2a4a;border-radius:4px;height:24px;position:relative;overflow:hidden}
.bar-fill{height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:.8rem;font-weight:600;color:#000}
'''
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
// Find fastest
let fastest=null;
const all=[];
for(const[num,entries]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  entries.forEach(e=>{{
    const dur=parseFloat(e.duration);
    if(!isNaN(dur)){{
      all.push({{num,...d,duration:dur,lap:e.lap}});
      if(!fastest||dur<fastest.duration)fastest={{num,...d,duration:dur,lap:e.lap}};
    }}
  }});
}}
let html='';
if(fastest)html+=`<div class="fastest"><div>🏆 Fastest Pit Stop</div><div class="val" style="color:${{fastest.color}}">${{fastest.duration}}s</div><div>${{fastest.tla}} (${{fastest.team}}) · Lap ${{fastest.lap}}</div></div>`;
html+='<h2>All Pit Stops by Duration</h2>';
all.sort((a,b)=>a.duration-b.duration);
const maxDur=all[all.length-1]?.duration||1;
all.forEach(d=>{{
  const pct=d.duration/maxDur*100;
  html+=`<div class="bar-row"><span class="bar-label">${{d.tla}}</span><div class="bar-track"><div class="bar-fill" style="width:${{pct}}%;background:${{d.color}}">${{d.duration}}s</div></div></div>`;
}});
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_tyre_timeline(data_dir, flag, title):
    data = load_json(f"{data_dir}/tyre_changes.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    compound_colors_js = json.dumps(COMPOUND_COLORS, separators=(',', ':'))
    
    css = '''
.gantt-row{display:flex;align-items:center;margin:.3rem 0;height:24px}
.gantt-label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.75rem}
.gantt-track{flex:1;background:#2a2a4a;border-radius:4px;height:16px;position:relative;overflow:hidden}
.gantt-fill{height:100%;position:absolute;border-radius:2px}
.stats{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}
.stat{background:#16213e;border-radius:8px;padding:.8rem;text-align:center;flex:1;min-width:120px}
.stat .val{font-size:1.5rem;font-weight:700;color:#00d4ff}
.stat .label{font-size:.75rem;color:#888}
'''
    js = f'''
const DATA={data_js};
const COLORS={compound_colors_js};
const app=document.getElementById('app');
// Find time range
let tMin=Infinity,tMax=-Infinity;
for(const[num,changes]of Object.entries(DATA)){{
  changes.forEach(c=>{{
    const parts=c.ts.split(':');
    const secs=parseInt(parts[0])*3600+parseInt(parts[1])*60+parseFloat(parts[2]);
    if(secs<tMin)tMin=secs;if(secs>tMax)tMax=secs;
  }});
}}
const tRange=tMax-tMin||1;
let html='<div class="stats">';
const strategies=new Set();
for(const[num,changes]of Object.entries(DATA)){{
  const comps=changes.map(c=>c.Compound).filter(c=>c&&c!=='UNKNOWN').join('→');
  if(comps)strategies.add(comps);
}}
html+=`<div class="stat"><div class="val">${{Object.keys(DATA).length}}</div><div class="label">Drivers</div></div>`;
html+=`<div class="stat"><div class="val">${{strategies.size}}</div><div class="label">Strategies</div></div>`;
html+='</div>';
html+='<h2>Tyre Compounds Timeline</h2>';
// Sort by finishing position (use first compound as start)
const sortedDrivers=Object.entries(DATA).sort((a,b)=>{{
  const da=DRIVERS[a[0]],db=DRIVERS[b[0]];
  return (da?.tla||'').localeCompare(db?.tla||'');
}});
sortedDrivers.forEach(([num,changes])=>{{
  const d=DRIVERS[num];if(!d)return;
  html+=`<div class="gantt-row"><span class="gantt-label">${{d.tla}}</span><div class="gantt-track">`;
  let prevT=tMin;
  changes.forEach((c,i)=>{{
    const parts=c.ts.split(':');
    const secs=parseInt(parts[0])*3600+parseInt(parts[1])*60+parseFloat(parts[2]);
    const left=((prevT-tMin)/tRange)*100;
    const width=((secs-prevT)/tRange)*100;
    const color=COLORS[c.Compound]||'#666';
    if(width>0)html+=`<div class="gantt-fill" style="left:${{left}}%;width:${{width}}%;background:${{color}}" title="${{c.Compound}}"></div>`;
    prevT=secs;
  }});
  // Last segment to end
  const left=((prevT-tMin)/tRange)*100;
  const width=((tMax-prevT)/tRange)*100;
  const lastComp=changes[changes.length-1]?.Compound||'UNKNOWN';
  const color=COLORS[lastComp]||'#666';
  if(width>0)html+=`<div class="gantt-fill" style="left:${{left}}%;width:${{width}}%;background:${{color}}" title="${{lastComp}}"></div>`;
  html+='</div></div>';
}});
// Legend
html+='<div style="display:flex;gap:1rem;margin-top:1rem">';
for(const[name,color]of Object.entries(COLORS)){{
  if(name==='UNKNOWN')continue;
  html+=`<span style="display:flex;align-items:center;gap:.3rem"><span style="width:12px;height:12px;border-radius:3px;background:${{color}};display:inline-block"></span>${{name}}</span>`;
}}
html+='</div>';
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_tyre_strategy(data_dir, flag, title):
    data = load_json(f"{data_dir}/tyre_stints.json")
    if not data:
        return None
    data_js = json.dumps(data, separators=(',', ':'))
    
    css = '''
.row{display:flex;align-items:center;margin:.3rem 0}
.label{width:50px;text-align:right;margin-right:.8rem;font-weight:600;font-size:.85rem}
.track{flex:1;display:flex;height:28px;border-radius:4px;overflow:hidden}
.compound{display:flex;align-items:center;justify-content:center;font-size:.7rem;font-weight:600;color:#000;min-width:20px}
.legend{display:flex;gap:1rem;margin-top:1rem}
.leg{display:flex;align-items:center;gap:.3rem;font-size:.8rem}
.dot{width:12px;height:12px;border-radius:3px;display:inline-block}
'''
    
    js = f'''
const DATA={data_js};
const COLORS={{"SOFT":"#FF3333","MEDIUM":"#FFD700","HARD":"#C0C0C0","INTERMEDIATE":"#00CC00","WET":"#3366FF","UNKNOWN":"#666"}};
const app=document.getElementById('app');
let html='';
for(const[num,stints]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  const stintArr=Object.values(stints).sort((a,b)=>(a.Stint||0)-(b.Stint||0));
  const totalLaps=stintArr.reduce((s,st)=>s+(st.TotalLaps||0),0)||1;
  html+=`<div class="row"><span class="label">${{d.tla}}</span><div class="track">`;
  stintArr.forEach(st=>{{
    const pct=(st.TotalLaps||0)/totalLaps*100;
    const color=COLORS[st.Compound]||'#666';
    html+=`<div class="compound" style="width:${{pct}}%;background:${{color}}" title="${{st.Compound}} ${{st.TotalLaps}}L">${{st.Compound?.[0]||'?'}}</div>`;
  }});
  html+='</div></div>';
}}
html+='<div class="legend">';
Object.entries(COLORS).forEach(([name,color])=>{{
  if(name==='UNKNOWN')return;
  html+=`<span class="leg"><span class="dot" style="background:${{color}}"></span>${{name}}</span>`;
}});
html+='</div>';
app.innerHTML=html;
'''
    return wrap_html(title, flag, css, js)

def gen_laptimes(data_dir, flag, title):
    data = load_json(f"{data_dir}/timing.json")
    if not data:
        return None
    # Extract lap times, limit data
    laptimes = {}
    for num, driver_data in data.items():
        if not isinstance(driver_data, dict):
            continue
        laps = driver_data.get('Laps', {})
        if isinstance(laps, dict):
            lt = {}
            for lap_num, lap_data in laps.items():
                lt_val = lap_data.get('LapTime', '')
                if isinstance(lt_val, dict):
                    lt[lap_num] = lt_val.get('Value', '')
                elif isinstance(lt_val, str) and lt_val:
                    lt[lap_num] = lt_val
            if lt:
                laptimes[num] = lt
    data_js = json.dumps(laptimes, separators=(',', ':'))
    
    css = '''
canvas{width:100%;height:350px;display:block;margin:1rem 0}
.filters{display:flex;flex-wrap:wrap;gap:.3rem;margin:1rem 0}
.fbtn{background:#2a2a4a;border:1px solid #3a3a5a;color:#aaa;padding:.3rem .6rem;border-radius:6px;cursor:pointer;font-size:.7rem}
.fbtn.active{background:#00d4ff;color:#000;border-color:#00d4ff}
'''
    js = f'''
const DATA={data_js};
const app=document.getElementById('app');
const drivers=[];
for(const[num,laps]of Object.entries(DATA)){{
  const d=DRIVERS[num];if(!d)continue;
  const entries=Object.entries(laps).map(([l,t])=>({{lap:+l,time:t}})).sort((a,b)=>a.lap-b.lap);
  drivers.push({{num,...d,entries}});
}}
let html='<div class="filters">';
drivers.forEach(d=>{{
  html+=`<button class="fbtn active" onclick="tog('${{d.num}}')" id="f-${{d.num}}" style="border-color:${{d.color}}">${{d.tla}}</button>`;
}});
html+='</div><canvas id="c"></canvas>';
app.innerHTML=html;
const active=new Set(drivers.map(d=>d.num));
window.tog=function(n){{if(active.has(n))active.delete(n);else active.add(n);document.getElementById('f-'+n).classList.toggle('active');draw()}};
function parseTime(s){{
  if(!s||typeof s!=='string')return null;
  const m=s.match(/(?:(\\d+):)?(\\d+)\\.(\\d+)/);if(!m)return null;
  return(parseInt(m[1]||0)*60+parseInt(m[2]))*1000+parseInt(m[3].padEnd(3,'0'));
}}
const maxLap=Math.max(...drivers.flatMap(d=>d.entries.map(e=>e.lap)));
draw();
function draw(){{
  const c=document.getElementById('c');const ctx=c.getContext('2d');
  const dpr=window.devicePixelRatio||1;
  c.width=c.parentElement.clientWidth*dpr;c.height=350*dpr;c.style.height='350px';
  const W=c.width/dpr,H=c.height/dpr;ctx.scale(dpr,dpr);ctx.clearRect(0,0,W,H);
  const pad={{t:10,b:30,l:50,r:10}};const cW=W-pad.l-pad.r,cH=H-pad.t-pad.b;
  let allMs=[];
  drivers.forEach(d=>{{if(!active.has(d.num))return;d.entries.forEach(e=>{{const ms=parseTime(e.time);if(ms)allMs.push(ms)}})}});
  if(!allMs.length)return;
  const mn=Math.min(...allMs),mx=Math.max(...allMs);
  drivers.forEach(d=>{{
    if(!active.has(d.num))return;
    ctx.beginPath();ctx.strokeStyle=d.color;ctx.lineWidth=1.5;
    d.entries.forEach((e,i)=>{{
      const ms=parseTime(e.time);if(!ms)return;
      const x=pad.l+(e.lap/maxLap)*cW;
      const y=pad.t+((ms-mn)/(mx-mn))*cH;
      if(!i)ctx.moveTo(x,y);else ctx.lineTo(x,y);
    }});
    ctx.stroke();
  }});
}}
'''
    return wrap_html(title, flag, css, js)

def gen_positions(data_dir, flag, title):
    # Reuse lap_chart logic
    return gen_lap_chart(data_dir, flag, title)

def gen_telemetry_na(flag, title):
    css = '.na{text-align:center;padding:4rem 1rem;color:#888}.na .icon{font-size:4rem;margin-bottom:1rem}'
    js = '''document.getElementById('app').innerHTML='<div class="na"><div class="icon">📊</div><h2>Telemetry data not available for this session</h2><p>Detailed telemetry overlay is only available for the Japanese Grand Prix 2026.</p></div>';'''
    return wrap_html(title, flag, css, js)

def gen_index(flag, gp_name, circuit, date, laps, subdir):
    """Generate index page for a GP."""
    pages = [
        ('pitstops.html', '🏎️', 'Pit Stop Analysis', 'Stop times and strategies'),
        ('tyre-strategy.html', '🛞', 'Tyre Strategy', 'Compound usage and stint breakdown'),
        ('weather.html', '🌤️', 'Weather Conditions', 'Track temperature, wind, and rain data'),
        ('positions.html', '🐍', 'Position Changes', 'Position progression chart'),
        ('laptimes.html', '⏱️', 'Lap Times', 'Lap-by-lap pace comparison'),
        ('race-control.html', '🏴', 'Race Control', 'Flags, penalties, and race director notes'),
        ('telemetry.html', '📊', 'Telemetry Overlay', 'Speed, throttle, brake comparison'),
        ('track-map.html', '🗺️', 'Track Map', 'Circuit layout with driver positions'),
        ('championship.html', '🏆', 'Championship', 'Standings after this race'),
        ('sector-analysis.html', '🏎️', 'Sector & Speed', 'Fastest sectors, speed traps, personal bests'),
        ('driver-progress.html', '📊', 'Driver Progress', 'Individual driver position changes'),
        ('overtakes.html', '🔄', 'Overtake Analysis', 'Who overtook whom'),
        ('lap-chart.html', '📈', 'Lap Chart', 'Full position chart across all laps'),
        ('pit-lane.html', '🏗️', 'Pit Lane', 'Pit stop duration analysis'),
        ('tyre-timeline.html', '🛞', 'Tyre Timeline', 'Compound Gantt chart and stint lengths'),
    ]
    
    cards = ''
    for href, icon, name, desc in pages:
        cards += f'''<a class="card" href="{href}">
    <div class="icon">{icon}</div>
    <h3>{name}</h3>
    <p class="desc">{desc}</p>
    <span class="link">View →</span>
  </a>\n  '''
    
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🏎️ Box-Box — {gp_name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#1a1a2e;color:#e0e0e0;min-height:100vh}}
header{{text-align:center;padding:2rem 1rem 1rem}}
header h1{{font-size:2rem;background:linear-gradient(135deg,#00d4ff,#7b2ff7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:.3rem 0}}
header p{{color:#888;font-size:.9rem}}
.race-info{{text-align:center;padding:1rem;margin:1rem auto;max-width:500px;background:#16213e;border-radius:12px;border:1px solid #2a2a4a}}
.race-info h2{{color:#00d4ff;font-size:1.2rem;margin-bottom:.3rem}}
.race-info p{{color:#aaa;font-size:.85rem}}
.back{{display:block;text-align:center;margin:1rem}}
.back a{{color:#00d4ff;text-decoration:none}}
.grid{{display:grid;grid-template-columns:1fr;gap:1rem;padding:1.5rem;max-width:1100px;margin:0 auto}}
@media(min-width:600px){{.grid{{grid-template-columns:repeat(2,1fr)}}}}
@media(min-width:960px){{.grid{{grid-template-columns:repeat(3,1fr)}}}}
.card{{background:#16213e;border-radius:12px;padding:1.5rem 1rem;text-decoration:none;color:inherit;display:flex;flex-direction:column;align-items:center;text-align:center;border:2px solid transparent;transition:transform .25s,box-shadow .25s,border-color .25s}}
.card:hover{{transform:translateY(-4px);box-shadow:0 8px 32px rgba(0,212,255,.15);border-color:#00d4ff}}
.card .icon{{font-size:2.2rem;margin-bottom:.5rem}}
.card h3{{font-size:1rem;margin-bottom:.3rem;color:#f0f0f0}}
.card .desc{{color:#888;font-size:.8rem;margin-bottom:.5rem}}
.card .link{{color:#00d4ff;font-size:.85rem;font-weight:600}}
footer{{text-align:center;padding:1.5rem;color:#555;font-size:.75rem;border-top:1px solid #2a2a4a;margin-top:2rem}}
</style>
</head>
<body>
<header>
  <h1>Box-Box</h1>
  <p><a href="/viz/index.html" style="color:#00d4ff;text-decoration:none">← All Races</a></p>
</header>
<div class="race-info">
  <h2>{flag} {gp_name}</h2>
  <p>{circuit} · {date} · {laps} laps</p>
</div>
<div class="grid">
  {cards}
</div>
<footer>Box-Box · Data from Formula 1 Live Timing API</footer>
</body>
</html>'''

# === MAIN ===
if len(sys.argv) < 4:
    print("Usage: generate.py <data_dir> <output_dir> <flag> <gp_name> <circuit> <date> <laps>")
    sys.exit(1)

data_dir = sys.argv[1]
out_dir = sys.argv[2]
flag = sys.argv[3]
gp_name = sys.argv[4]
circuit = sys.argv[5]
date = sys.argv[6]
laps = sys.argv[7]

os.makedirs(out_dir, exist_ok=True)

generators = {
    'pitstops.html': lambda: gen_pitstops(data_dir, flag, f"{gp_name} — Pit Stop Analysis"),
    'tyre-strategy.html': lambda: gen_tyre_strategy(data_dir, flag, f"{gp_name} — Tyre Strategy"),
    'weather.html': lambda: gen_weather(data_dir, flag, f"{gp_name} — Weather Conditions"),
    'positions.html': lambda: gen_positions(data_dir, flag, f"{gp_name} — Position Changes"),
    'laptimes.html': lambda: gen_laptimes(data_dir, flag, f"{gp_name} — Lap Times"),
    'race-control.html': lambda: gen_race_control(data_dir, flag, f"{gp_name} — Race Control"),
    'track-map.html': lambda: gen_track_map(data_dir, flag, f"{gp_name} — Track Map"),
    'championship.html': lambda: gen_championship(data_dir, flag, f"{gp_name} — Championship"),
    'sector-analysis.html': lambda: gen_sector_analysis(data_dir, flag, f"{gp_name} — Sector & Speed"),
    'driver-progress.html': lambda: gen_driver_progress(data_dir, flag, f"{gp_name} — Driver Progress"),
    'overtakes.html': lambda: gen_overtakes(data_dir, flag, f"{gp_name} — Overtake Analysis"),
    'lap-chart.html': lambda: gen_lap_chart(data_dir, flag, f"{gp_name} — Lap Chart"),
    'pit-lane.html': lambda: gen_pit_lane(data_dir, flag, f"{gp_name} — Pit Lane"),
    'tyre-timeline.html': lambda: gen_tyre_timeline(data_dir, flag, f"{gp_name} — Tyre Timeline"),
    'telemetry.html': lambda: gen_telemetry_na(flag, f"{gp_name} — Telemetry"),
}

# Generate all pages
created = 0
for name, gen_fn in generators.items():
    try:
        html = gen_fn()
        if html:
            with open(f"{out_dir}/{name}", 'w') as f:
                f.write(html)
            size = os.path.getsize(f"{out_dir}/{name}")
            print(f"  ✅ {name} ({size//1024}KB)")
            created += 1
        else:
            print(f"  ⚠️  {name} — no data")
    except Exception as e:
        print(f"  ❌ {name} — {e}")

# Generate index
idx = gen_index(flag, gp_name, circuit, date, laps, out_dir)
with open(f"{out_dir}/index.html", 'w') as f:
    f.write(idx)
print(f"  ✅ index.html")
created += 1

print(f"\n🏁 Created {created} files in {out_dir}")
