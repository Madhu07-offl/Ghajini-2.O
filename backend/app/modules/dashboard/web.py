from fastapi.responses import HTMLResponse

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ghajini 2.0 - Caregiver Dashboard & AI Companion</title>
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
    .badge-intent { background: #EDE9FE; color: #6D28D9; border: 1px solid #C4B5FD; font-size: 12px; padding: 3px 8px; border-radius: 6px; }
    .badge-mood { background: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; font-size: 12px; padding: 3px 8px; border-radius: 6px; }
    .badge-grounded { background: #DCFCE7; color: #166534; border: 1px solid #86EFAC; font-size: 12px; padding: 3px 8px; border-radius: 6px; }
    .container { max-width: 1200px; margin: 28px auto; padding: 0 20px; }
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
    @media (max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }
    .card { background: var(--card-bg); border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E2E8F0; margin-bottom: 24px; }
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
    .btn-pill { padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; border: 1px solid #CBD5E1; background: #F8FAFC; cursor: pointer; }
    .btn-pill:hover { background: #E2E8F0; }
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
    .test-answer { margin-top: 14px; padding: 18px; border-radius: 12px; background: #F1F5F9; font-size: 16px; font-weight: 600; min-height: 52px; line-height: 1.5; }
    /* Companion chat style */
    .companion-reply-box { margin-top: 16px; padding: 20px; border-radius: 14px; background: #F0FDF4; border: 1.5px solid #BBF7D0; }
    .companion-reply-text { font-size: 22px; font-weight: 700; color: #166534; line-height: 1.4; margin-bottom: 12px; }
    .companion-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .person-card { display: flex; align-items: center; gap: 14px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin-top: 14px; }
    .person-avatar { width: 52px; height: 52px; border-radius: 50%; background: #DBEAFE; color: #1E3A8A; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 20px; }
  </style>
</head>
<body>

  <header>
    <div class="header-title">
      <h1>Ghajini 2.0 — Patient AI Companion</h1>
      <p>Caregiver Command Center & Live Memory Companion</p>
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

    <!-- Row 2: LIVE PATIENT AI COMPANION INTERFACE -->
    <div class="card" style="border: 2px solid #3B82F6;">
      <div class="card-header">
        <div class="card-title" style="font-size: 20px; color: #1E3A8A;">
          <span>🤖 Patient AI Companion (Live Pipeline /v1/companion/message)</span>
        </div>
        <div style="display: flex; gap: 8px;">
          <select id="comp-lang-select" class="btn-pill" style="padding: 6px 12px;">
            <option value="en">English (en-IN)</option>
            <option value="hi" selected>Hindi (hi-IN)</option>
            <option value="pa">Punjabi (pa-IN)</option>
          </select>
          <button class="btn btn-outline" onclick="pollProactive()">Poll Proactive (/proactive)</button>
        </div>
      </div>

      <p style="color: var(--text-muted); font-size: 15px; margin-bottom: 12px;">
        Talk directly to Ghajini using the rule-based intent router, memory retrieval, mood reassurance, and anti-hallucination guardrail:
      </p>

      <!-- Quick prompts -->
      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
        <span style="font-size: 13px; font-weight: 700; color: var(--text-muted); align-self: center;">Quick test:</span>
        <button class="btn-pill" onclick="setCompPrompt('Who is Priya?')">Who is Priya?</button>
        <button class="btn-pill" onclick="setCompPrompt('What day is it today?')">What day is it?</button>
        <button class="btn-pill" onclick="setCompPrompt('Did I take my morning medicine?')">Did I take my medicine?</button>
        <button class="btn-pill" onclick="setCompPrompt('What do I do today?')">What do I do today?</button>
        <button class="btn-pill" onclick="setCompPrompt('Madad karo main gir gayi')">🚨 Help / Emergency (Hindi)</button>
        <button class="btn-pill" onclick="setCompPrompt('Call my daughter')">📞 Call Family</button>
      </div>

      <div class="test-box">
        <input type="text" id="comp-input" class="test-input" placeholder="Say or type something to Ghajini... (e.g. Who is Priya? / Dawai kab leni hai?)">
        <button class="btn btn-primary" onclick="sendCompanionMessage()">Talk to Ghajini</button>
      </div>

      <!-- Live Companion Response Box -->
      <div class="companion-reply-box" id="comp-reply-container" style="display: none;">
        <div class="companion-reply-text" id="comp-reply-text">Ghajini's reply will appear here...</div>
        <div class="companion-meta" id="comp-meta">
          <!-- Filled dynamically -->
        </div>
        <div id="comp-person-card"></div>
      </div>
    </div>

    <!-- Row 3: Daily Summary & Weekly History -->
    <div class="grid-2">
      <!-- Daily Factual Summary -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Today's Factual Activity Summary</div>
          <button class="btn btn-outline" onclick="loadDashboard()">Refresh</button>
        </div>
        <div class="daily-box" id="daily-summary-text">Loading today's recorded activities...</div>
      </div>

      <!-- Weekly Pattern -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">Weekly Dose Pattern</div>
          <div style="font-size: 13px; font-weight: 700;">
            <span style="color: var(--success);">&#9632; Taken</span> &nbsp;
            <span style="color: var(--danger);">&#9632; Missed</span>
          </div>
        </div>
        <div class="chart-container" id="chart-bars"></div>
      </div>
    </div>

    <!-- Row 4: Repeated Questions & Teach the Companion -->
    <div class="grid-2">
      <!-- Top Repeated Questions -->
      <div class="card">
        <div class="card-title" style="margin-bottom: 16px;">Top Repeated Questions (Logged for Review)</div>
        <div id="questions-list">
          <div class="question-item"><span class="question-text">Loading questions...</span></div>
        </div>
      </div>

      <!-- Teach the Companion -->
      <div class="card">
        <div class="card-title" style="margin-bottom: 10px;">Teach the Companion (Caregiver Knowledge Form)</div>
        <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 12px;">
          Add a new personal fact or routine in plain text. Text is sanitized against prompt injections and embedded into FAISS immediately:
        </p>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <input type="text" id="teach-input" class="test-input" placeholder="e.g. Priya visits every Diwali with grandson Kabir.">
          <button class="btn btn-success" onclick="teachMemory()">Teach & Embed Memory</button>
        </div>
        <div id="teach-status" style="margin-top: 10px; font-size: 14px; font-weight: 600;"></div>
      </div>
    </div>

    <!-- Row 5: Demo Controls -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 10px;">Live Demo Control Center</div>
      <p style="color: var(--text-muted); font-size: 15px;">Execute live demonstration commands directly against the backend:</p>
      <div class="actions-grid">
        <button class="btn btn-primary" onclick="resetDemo()">Reset Demo Data</button>
        <button class="btn btn-success" onclick="triggerReminder()">Trigger Reminder Now</button>
        <button class="btn btn-danger" onclick="triggerSOS()">Trigger SOS Alert</button>
        <button class="btn btn-primary" style="background: #166534;" onclick="triggerCallCaregiver()">Call Caregiver (+91 7604934874)</button>
        <a href="/v1/privacy/export" class="btn btn-outline" style="text-decoration: none; justify-content: center;">Export Personal Data (ZIP)</a>
      </div>
    </div>

  </div>

  <script>
    async function loadDashboard() {
      try {
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

        // Fetch Daily Summary
        const dailyRes = await fetch('/v1/dashboard/daily-summary');
        const dailyData = await dailyRes.json();
        document.getElementById('daily-summary-text').innerText = dailyData.summary;

      } catch (e) {
        console.error(e);
      }
    }

    function setCompPrompt(text) {
      document.getElementById('comp-input').value = text;
      sendCompanionMessage();
    }

    async function sendCompanionMessage() {
      const text = document.getElementById('comp-input').value.trim();
      if (!text) return;
      const lang = document.getElementById('comp-lang-select').value;
      const container = document.getElementById('comp-reply-container');
      const replyEl = document.getElementById('comp-reply-text');
      const metaEl = document.getElementById('comp-meta');
      const cardEl = document.getElementById('comp-person-card');

      container.style.display = 'block';
      replyEl.innerText = 'Ghajini is thinking...';
      metaEl.innerHTML = '';
      cardEl.innerHTML = '';

      try {
        const res = await fetch('/v1/companion/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, text: text, lang: lang, source: 'text' })
        });
        const data = await res.json();

        replyEl.innerText = data.reply;
        metaEl.innerHTML = `
          <span class="badge-intent">Intent: ${data.intent}</span>
          <span class="badge-mood">Mood: ${data.mood}</span>
          <span class="badge-grounded">${data.grounded ? 'Grounded: Stored Facts' : 'Ungrounded Fallback'}</span>
          <span style="font-size: 12px; color: var(--text-muted);">Lang: ${data.lang.toUpperCase()}</span>
        `;

        if (data.actions && data.actions.length > 0) {
          data.actions.forEach(act => {
            metaEl.innerHTML += `<span style="background: #FEE2E2; color: #991B1B; font-weight: 700; font-size: 12px; padding: 3px 8px; border-radius: 6px;">Action: ${act}</span>`;
          });
        }

        if (data.person) {
          cardEl.innerHTML = `
            <div class="person-card">
              <div class="person-avatar">${data.person.name.charAt(0)}</div>
              <div>
                <div style="font-weight: 700; font-size: 16px;">${data.person.name} (${data.person.relationship})</div>
                <div style="font-size: 13px; color: var(--text-muted);">${data.person.notes || ''}</div>
              </div>
            </div>
          `;
        }

        loadDashboard();
      } catch (e) {
        replyEl.innerText = 'I am not sure. Shall I call your family?';
        console.error(e);
      }
    }

    async function pollProactive() {
      try {
        const res = await fetch('/v1/companion/proactive');
        const data = await res.json();
        if (data.has_message) {
          alert(`[Proactive Companion ${data.message.type.toUpperCase()}]\n\n${data.message.message}`);
        } else {
          alert('No proactive message due at this time (or currently in quiet hours).');
        }
      } catch (e) {
        alert('Proactive check error: ' + e);
      }
    }

    async function teachMemory() {
      const text = document.getElementById('teach-input').value.trim();
      if (!text) return;
      const statusEl = document.getElementById('teach-status');
      statusEl.style.color = '#1E3A8A';
      statusEl.innerText = 'Sanitizing and embedding into FAISS...';

      try {
        const res = await fetch('/v1/companion/teach', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, text: text, category: 'personal' })
        });
        const data = await res.json();
        statusEl.style.color = '#166534';
        statusEl.innerText = `Success! Embedded memory id=${data.id}: "${data.text}"`;
        document.getElementById('teach-input').value = '';
      } catch (e) {
        statusEl.style.color = '#DC2626';
        statusEl.innerText = 'Error saving memory: ' + e;
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

    async function triggerCallCaregiver() {
      try {
        const res = await fetch('/v1/calls/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: 1,
            reason: 'Dashboard direct call test',
            source: 'sos',
            lang: 'en'
          })
        });
        const data = await res.json();
        if (data.allowed) {
          alert(`📞 Calling ${data.contact.name} (${data.contact.phone})\n\nPatient Speech: "${data.patient_message}"\n\nCaregiver Briefing:\n${data.caregiver_briefing}`);
          window.open(`tel:${data.contact.phone}`);
          loadDashboard();
        } else {
          alert(`Call Paused: ${data.block_reason}`);
        }
      } catch (e) {
        alert('Call request failed: ' + e);
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
