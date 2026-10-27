from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ghajini 2.0 - Caregiver Dashboard</title>
  <style>
    :root {
      --primary: #1E3A8A;
      --primary-dark: #0F172A;
      --accent: #F59E0B;
      --success: #10B981;
      --danger: #EF4444;
      --bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --text: #1E293B;
      --text-muted: #64748B;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding-bottom: 40px; }
    header { background: var(--primary-dark); color: white; padding: 20px 32px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .header-title h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.5px; }
    .header-title p { font-size: 14px; color: #94A3B8; margin-top: 4px; }
    .header-badges { display: flex; gap: 10px; align-items: center; }
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 700; text-transform: uppercase; }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; }
    .badge-primary { background: rgba(30, 58, 138, 0.4); color: #93C5FD; border: 1px solid #3B82F6; }
    .container { max-width: 1200px; margin: 28px auto; padding: 0 20px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
    @media (max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }
    .card { background: var(--card-bg); border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E2E8F0; }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .card-title { font-size: 18px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 8px; }
    .btn { padding: 10px 18px; border-radius: 10px; border: none; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; }
    .btn-primary { background: var(--primary); color: white; }
    .btn-primary:hover { background: #1D4ED8; }
    .btn-success { background: var(--success); color: white; }
    .btn-success:hover { background: #059669; }
    .btn-danger { background: var(--danger); color: white; }
    .btn-danger:hover { background: #DC2626; }
    .btn-outline { background: white; border: 1.5px solid #CBD5E1; color: var(--text); }
    .btn-outline:hover { background: #F1F5F9; }
    .stat-number { font-size: 44px; font-weight: 800; line-height: 1; }
    .stat-label { font-size: 14px; color: var(--text-muted); margin-top: 6px; font-weight: 600; }
    /* Daily Summary */
    .daily-box { background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 14px; padding: 20px; color: #166534; font-size: 18px; line-height: 1.5; font-weight: 600; }
    /* Chart */
    .chart-container { height: 160px; display: flex; align-items: flex-end; justify-content: space-between; padding-top: 20px; gap: 12px; }
    .chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; height: 100%; justify-content: flex-end; }
    .bar-group { display: flex; align-items: flex-end; gap: 4px; height: 110px; }
    .bar { width: 18px; border-radius: 4px 4px 0 0; transition: height 0.3s; }
    .bar-done { background: var(--success); }
    .bar-missed { background: var(--danger); }
    .day-label { font-size: 13px; font-weight: 700; color: var(--text-muted); }
    /* Question list */
    .question-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #F8FAFC; border-radius: 10px; margin-bottom: 10px; border: 1px solid #E2E8F0; }
    .question-text { font-size: 16px; font-weight: 600; }
    .question-count { background: #DBEAFE; color: var(--primary); font-size: 13px; font-weight: 800; padding: 4px 10px; border-radius: 12px; }
    /* Action Bar */
    .actions-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 14px; margin-top: 16px; }
    /* Test box */
    .test-box { display: flex; gap: 10px; margin-top: 14px; }
    .test-input { flex: 1; padding: 12px 16px; border: 1.5px solid #CBD5E1; border-radius: 10px; font-size: 16px; }
    .test-answer { margin-top: 14px; padding: 16px; border-radius: 10px; background: #F1F5F9; font-size: 16px; font-weight: 600; min-height: 48px; }
  </style>
</head>
<body>

  <header>
    <div class="header-title">
      <h1>Ghajini 2.0 — Caregiver Dashboard</h1>
      <p>AI Memory Companion for Alzheimer's Patients</p>
    </div>
    <div class="header-badges">
      <span class="badge badge-success">Backend: Online</span>
      <span class="badge badge-primary">Patient: Primary Patient</span>
      <a href="/docs" target="_blank" class="btn btn-outline" style="padding: 6px 12px; font-size: 13px; color: white; border-color: rgba(255,255,255,0.3); background: transparent;">API Docs &rarr;</a>
    </div>
  </header>

  <div class="container">

    <!-- Row 1: KPI Stats -->
    <div class="grid-3">
      <div class="card">
        <div class="card-title">Medication Adherence</div>
        <div class="stat-number" id="adherence-val" style="color: var(--success);">--%</div>
        <div class="stat-label" id="adherence-sub">7-Day Completion Rate</div>
      </div>
      <div class="card">
        <div class="card-title">Face Recognitions Today</div>
        <div class="stat-number" id="recog-val" style="color: var(--primary);">--</div>
        <div class="stat-label">Consented family & doctors seen</div>
      </div>
      <div class="card">
        <div class="card-title">Active Caregiver Alerts</div>
        <div class="stat-number" id="alerts-val" style="color: var(--danger);">--</div>
        <div class="stat-label">Assistance & SOS triggers</div>
      </div>
    </div>

    <!-- Row 2: Daily Factual Summary -->
    <div class="card" style="margin-bottom: 24px;">
      <div class="card-header">
        <div class="card-title">
          <span>Today's Factual Activity Summary</span>
        </div>
        <button class="btn btn-outline" onclick="loadDashboard()">Refresh Live</button>
      </div>
      <div class="daily-box" id="daily-summary-text">
        Loading today's recorded activities...
      </div>
    </div>

    <!-- Row 3: Weekly Pattern & Repeated Questions -->
    <div class="grid-2" style="margin-bottom: 24px;">
      
      <!-- Weekly Bar Chart -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Weekly Dose Pattern (Last 7 Days)</div>
          <div style="font-size: 13px; font-weight: 700;">
            <span style="color: var(--success);">&#9632; Taken</span> &nbsp;
            <span style="color: var(--danger);">&#9632; Missed</span>
          </div>
        </div>
        <div class="chart-container" id="chart-bars">
          <!-- Filled dynamically -->
        </div>
      </div>

      <!-- Top Repeated Questions -->
      <div class="card">
        <div class="card-title" style="margin-bottom: 16px;">Top Repeated Questions</div>
        <div id="questions-list">
          <div class="question-item"><span class="question-text">Loading questions...</span></div>
        </div>
      </div>

    </div>

    <!-- Row 4: Live Demo Control Center & Memory Testing -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 10px;">Live Demo Control Center</div>
      <p style="color: var(--text-muted); font-size: 15px;">Execute live demonstration commands directly against the FastAPI backend:</p>
      
      <div class="actions-grid">
        <button class="btn btn-primary" onclick="resetDemo()">Reset Demo Data</button>
        <button class="btn btn-success" onclick="triggerReminder()">Trigger Reminder Now</button>
        <button class="btn btn-danger" onclick="triggerSOS()">Trigger SOS Alert</button>
        <a href="/v1/privacy/export" class="btn btn-outline" style="text-decoration: none; justify-content: center;">Export Personal Data (ZIP)</a>
      </div>

      <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid #E2E8F0;">
        <div class="card-title" style="font-size: 16px;">Test Memory Question Retrieval (/v1/ask):</div>
        <div class="test-box">
          <input type="text" id="ask-input" class="test-input" placeholder="e.g. Where does Priya live? / Dawai kab leni hai?">
          <button class="btn btn-primary" onclick="askQuestion()">Ask Ghajini</button>
        </div>
        <div class="test-answer" id="ask-answer">Answer will appear here grounded strictly in stored semantic memories...</div>
      </div>

    </div>

  </div>

  <script>
    async function loadDashboard() {
      try {
        // 1. Fetch Summary
        const res = await fetch('/v1/dashboard/summary');
        const data = await res.json();

        document.getElementById('adherence-val').innerText = data.adherence_pct.toFixed(1) + '%';
        document.getElementById('adherence-sub').innerText = `${data.done_count} doses taken, ${data.missed_count} missed`;
        document.getElementById('recog-val').innerText = data.recognitions_today;
        document.getElementById('alerts-val').innerText = data.alerts_count;

        // Render Bar Chart
        const chartEl = document.getElementById('chart-bars');
        chartEl.innerHTML = '';
        const maxDoses = Math.max(...data.weekly_history.map(d => d.done + d.missed), 1);

        data.weekly_history.forEach(day => {
          const col = document.createElement('div');
          col.className = 'chart-col';
          const doneH = Math.max(6, (day.done / maxDoses) * 90);
          const missedH = (day.missed / maxDoses) * 90;

          col.innerHTML = `
            <div class="bar-group">
              <div class="bar bar-done" style="height: ${doneH}px;" title="${day.day}: ${day.done} taken"></div>
              ${day.missed > 0 ? `<div class="bar bar-missed" style="height: ${missedH}px;" title="${day.day}: ${day.missed} missed"></div>` : ''}
            </div>
            <div class="day-label">${day.day}</div>
          `;
          chartEl.appendChild(col);
        });

        // Render Top Questions
        const qList = document.getElementById('questions-list');
        qList.innerHTML = '';
        if (data.top_questions.length === 0) {
          qList.innerHTML = '<div class="question-item"><span class="question-text">No recorded questions yet.</span></div>';
        } else {
          data.top_questions.forEach(q => {
            const item = document.createElement('div');
            item.className = 'question-item';
            item.innerHTML = `
              <span class="question-text">${q.question}</span>
              <span class="question-count">${q.count}x asked</span>
            `;
            qList.appendChild(item);
          });
        }

        // 2. Fetch Daily Summary
        const dailyRes = await fetch('/v1/dashboard/daily-summary');
        const dailyData = await dailyRes.json();
        document.getElementById('daily-summary-text').innerText = dailyData.summary;

      } catch (e) {
        console.error(e);
      }
    }

    async function resetDemo() {
      if (!confirm('Reset demo data to 3 people, 10 memories, 2 reminders, and 1 place?')) return;
      try {
        const res = await fetch('/v1/demo/reset', { method: 'POST' });
        const data = await res.json();
        alert('Demo Reset Complete: ' + data.message);
        loadDashboard();
      } catch (e) {
        alert('Reset failed: ' + e);
      }
    }

    async function triggerReminder() {
      try {
        const res = await fetch('/v1/demo/trigger-reminder', { method: 'POST' });
        const data = await res.json();
        alert(`Reminder Triggered: "${data.title}" is now due!`);
        loadDashboard();
      } catch (e) {
        alert('Trigger failed: ' + e);
      }
    }

    async function triggerSOS() {
      try {
        const res = await fetch('/v1/alerts/help', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, note: 'Web Dashboard SOS trigger' })
        });
        const data = await res.json();
        alert('Emergency Alert Dispatched: Your family has been notified.');
        loadDashboard();
      } catch (e) {
        alert('SOS failed: ' + e);
      }
    }

    async function askQuestion() {
      const q = document.getElementById('ask-input').value.trim();
      if (!q) return;
      const ansEl = document.getElementById('ask-answer');
      ansEl.innerText = 'Searching memories and generating answer...';

      try {
        const res = await fetch('/v1/ask', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: q, lang: 'en' })
        });
        const data = await res.json();
        ansEl.innerText = (data.grounded ? '💡 ' : '❓ ') + data.answer;
        ansEl.style.color = data.grounded ? '#166534' : '#92400E';
        ansEl.style.background = data.grounded ? '#F0FDF4' : '#FEF3C7';
        loadDashboard();
      } catch (e) {
        ansEl.innerText = 'Error querying memories: ' + e;
      }
    }

    // Load on start
    loadDashboard();
  </script>
</body>
</html>
"""


def get_dashboard_html() -> HTMLResponse:
    return HTMLResponse(content=DASHBOARD_HTML, status_code=200)
