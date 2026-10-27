import base64
import os
from fastapi.responses import HTMLResponse

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
LOGO_FILE = os.path.join(STATIC_DIR, "logo.png")
LOGO_B64_FILE = os.path.join(STATIC_DIR, "logo_base64.txt")

_logo_b64 = ""
if os.path.exists(LOGO_B64_FILE):
    try:
        with open(LOGO_B64_FILE, "r") as f:
            _logo_b64 = f.read().strip()
    except Exception:
        pass
elif os.path.exists(LOGO_FILE):
    try:
        with open(LOGO_FILE, "rb") as f:
            _logo_b64 = base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ghajini 2.0 - Memory Companion & CardioLife Care</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,__LOGO_B64__">
  <style>
    :root {
      --primary: #1E3A8A;
      --primary-dark: #0F172A;
      --primary-light: #3B82F6;
      --accent: #F59E0B;
      --success: #10B981;
      --danger: #EF4444;
      --rose: #F43F5E;
      --bg: #F8FAFC;
      --card-bg: #FFFFFF;
      --text: #1E293B;
      --text-muted: #64748B;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
    body { background-color: var(--bg); color: var(--text); padding-bottom: 50px; min-height: 100vh; }

    /* Top Navigation Bar */
    header {
      background: var(--primary-dark);
      color: white;
      padding: 16px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      box-shadow: 0 4px 16px rgba(0,0,0,0.15);
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .brand-logo {
      width: 56px;
      height: 56px;
      object-fit: contain;
      filter: drop-shadow(0 2px 6px rgba(255,255,255,0.2));
      cursor: pointer;
      transition: transform 0.2s;
    }
    .brand-logo:hover { transform: scale(1.08) rotate(3deg); }
    .header-title h1 { font-size: 24px; font-weight: 800; letter-spacing: -0.5px; }
    .header-title p { font-size: 13px; color: #94A3B8; margin-top: 2px; }

    /* Navigation Mode Switcher Tabs */
    .portal-nav {
      display: flex;
      background: rgba(255, 255, 255, 0.1);
      padding: 4px;
      border-radius: 12px;
      border: 1px solid rgba(255, 255, 255, 0.15);
      gap: 4px;
    }
    .nav-tab-btn {
      padding: 8px 18px;
      border-radius: 8px;
      border: none;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;
      background: transparent;
      color: #CBD5E1;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .nav-tab-btn.active {
      background: white;
      color: var(--primary-dark);
      box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    }

    .header-badges { display: flex; gap: 10px; align-items: center; }
    .badge { padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 700; text-transform: uppercase; }
    .badge-success { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid #10B981; }
    .badge-primary { background: rgba(59, 130, 246, 0.25); color: #93C5FD; border: 1px solid #3B82F6; }

    .container { max-width: 1200px; margin: 24px auto; padding: 0 20px; }

    /* Cards & Layout */
    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 24px; }
    @media (max-width: 900px) { .grid-2, .grid-3 { grid-template-columns: 1fr; } }

    .card {
      background: var(--card-bg);
      border-radius: 16px;
      padding: 24px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.04);
      border: 1px solid #E2E8F0;
      margin-bottom: 20px;
    }
    .card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .card-title { font-size: 18px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 8px; }

    /* Buttons */
    .btn {
      padding: 10px 18px;
      border-radius: 10px;
      border: none;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      text-decoration: none;
    }
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

    .stat-number { font-size: 42px; font-weight: 800; line-height: 1; }
    .stat-label { font-size: 14px; color: var(--text-muted); margin-top: 6px; font-weight: 600; }

    /* ECG Canvas Monitor */
    .ecg-box {
      background: #0F172A;
      border-radius: 12px;
      padding: 16px;
      position: relative;
      overflow: hidden;
      margin-top: 14px;
    }
    .ecg-canvas { width: 100%; height: 120px; display: block; }
    .ecg-metrics {
      display: flex;
      justify-content: space-between;
      color: #94A3B8;
      font-size: 13px;
      font-weight: 600;
      margin-top: 10px;
      border-top: 1px solid #334155;
      padding-top: 8px;
    }

    /* Caretaker Login Card */
    .caretaker-profile-bar {
      background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
      color: white;
      border-radius: 14px;
      padding: 18px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      box-shadow: 0 4px 14px rgba(30, 58, 138, 0.2);
    }
    .caretaker-info-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,255,255,0.15);
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 13px;
    }

    /* Daily Summary */
    .daily-box { background: #F0FDF4; border: 1.5px solid #BBF7D0; border-radius: 14px; padding: 20px; color: #166534; font-size: 17px; line-height: 1.5; font-weight: 600; }

    /* Chart */
    .chart-container { height: 160px; display: flex; align-items: flex-end; justify-content: space-between; padding-top: 20px; gap: 12px; }
    .chart-col { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; height: 100%; justify-content: flex-end; }
    .bar-group { display: flex; align-items: flex-end; gap: 4px; height: 110px; }
    .bar { width: 18px; border-radius: 4px 4px 0 0; transition: height 0.3s; }
    .bar-done { background: var(--success); }
    .bar-missed { background: var(--danger); }
    .day-label { font-size: 13px; font-weight: 700; color: var(--text-muted); }

    /* Top Questions */
    .question-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #F8FAFC; border-radius: 10px; margin-bottom: 10px; border: 1px solid #E2E8F0; }
    .question-text { font-size: 15px; font-weight: 600; }
    .question-count { background: #DBEAFE; color: var(--primary); font-size: 13px; font-weight: 800; padding: 4px 10px; border-radius: 12px; }

    /* Test & Companion Inputs */
    .test-box { display: flex; gap: 10px; margin-top: 14px; }
    .test-input { flex: 1; padding: 12px 16px; border: 1.5px solid #CBD5E1; border-radius: 10px; font-size: 16px; }
    .companion-reply-box { margin-top: 16px; padding: 20px; border-radius: 14px; background: #F0FDF4; border: 1.5px solid #BBF7D0; }
    .companion-reply-text { font-size: 22px; font-weight: 700; color: #166534; line-height: 1.4; margin-bottom: 12px; }
    .companion-meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }

    /* ========================================= */
    /* PATIENT PORTAL STYLES (Elderly Friendly)  */
    /* ========================================= */
    .patient-container {
      max-width: 900px;
      margin: 20px auto;
      padding: 0 20px;
      text-align: center;
    }
    .patient-hero {
      background: white;
      border-radius: 24px;
      padding: 32px 24px;
      margin-bottom: 24px;
      box-shadow: 0 6px 20px rgba(0,0,0,0.06);
      border: 2px solid #E2E8F0;
      display: flex;
      flex-direction: column;
      align-items: center;
    }
    .patient-logo {
      width: 140px;
      height: 140px;
      object-fit: contain;
      filter: drop-shadow(0 6px 14px rgba(0,0,0,0.12));
      animation: gentle-wave 4s ease-in-out infinite;
    }
    @keyframes gentle-wave {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-8px) rotate(2deg); }
    }
    .patient-greeting {
      font-size: 32px;
      font-weight: 800;
      color: #1E293B;
      margin-top: 16px;
      line-height: 1.25;
    }
    .patient-subtitle {
      font-size: 20px;
      color: #64748B;
      margin-top: 8px;
      font-weight: 500;
    }

    /* Huge Accessible Patient Buttons */
    .patient-action-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 10px;
    }
    @media (max-width: 700px) { .patient-action-grid { grid-template-columns: 1fr; } }

    .patient-btn-card {
      background: white;
      border-radius: 20px;
      padding: 28px 20px;
      text-align: center;
      cursor: pointer;
      transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 4px 14px rgba(0,0,0,0.05);
      border: 3px solid transparent;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 12px;
      user-select: none;
    }
    .patient-btn-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .patient-btn-card:active {
      transform: scale(0.98);
    }

    .p-btn-talk { border-color: #3B82F6; background: #EFF6FF; }
    .p-btn-heart { border-color: #F43F5E; background: #FFF1F2; }
    .p-btn-call { border-color: #10B981; background: #F0FDF4; }
    .p-btn-sos { border-color: #EF4444; background: #FEF2F2; }
    .p-btn-meds { border-color: #F59E0B; background: #FFFBEB; }

    .p-btn-icon { font-size: 50px; line-height: 1; }
    .p-btn-title { font-size: 24px; font-weight: 800; color: #1E293B; }
    .p-btn-desc { font-size: 16px; color: #64748B; font-weight: 600; }

    /* Patient Simple Modal */
    .patient-modal-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.7);
      backdrop-filter: blur(4px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 200;
      padding: 20px;
    }
    .patient-modal {
      background: white;
      border-radius: 24px;
      max-width: 650px;
      width: 100%;
      padding: 32px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.25);
      text-align: left;
    }
    .patient-modal-title { font-size: 26px; font-weight: 800; color: #1E293B; margin-bottom: 12px; display: flex; align-items: center; gap: 10px; }
  </style>
</head>
<body>

  <!-- Top Header with Logo and Portal Switcher -->
  <header>
    <div class="header-left">
      <img src="data:image/png;base64,__LOGO_B64__" alt="Ghajini 2.0" class="brand-logo" onclick="switchPortal('patient')">
      <div class="header-title">
        <h1>Ghajini 2.0</h1>
        <p>AI Memory Integrity & CardioLife Care</p>
      </div>
    </div>

    <!-- Portal Switch Tabs -->
    <div class="portal-nav">
      <button class="nav-tab-btn active" id="tab-caretaker" onclick="switchPortal('caretaker')">
        🛡️ Caretaker Command Center
      </button>
      <button class="nav-tab-btn" id="tab-patient" onclick="switchPortal('patient')">
        👤 Patient Portal (Simple)
      </button>
    </div>

    <div class="header-badges">
      <span class="badge badge-success">Backend: Online</span>
      <select id="global-lang" class="btn-pill" onchange="changeLanguage()" style="background: rgba(255,255,255,0.15); color: white; border-color: rgba(255,255,255,0.3);">
        <option value="en" selected style="color: black;">English (EN)</option>
        <option value="hi" style="color: black;">हिन्दी (Hindi)</option>
        <option value="pa" style="color: black;">ਪੰਜਾਬੀ (Punjabi)</option>
      </select>
    </div>
  </header>

  <!-- ======================================================== -->
  <!-- CARETAKER PORTAL                                         -->
  <!-- ======================================================== -->
  <div id="caretaker-view" class="container">

    <!-- Caretaker Profile Banner & Login Switcher -->
    <div class="caretaker-profile-bar" id="caretaker-banner">
      <div>
        <div style="font-size: 20px; font-weight: 800; display: flex; align-items: center; gap: 8px;">
          <span>🛡️ Caretaker:</span>
          <span id="caretaker-display-name">Priya Sharma</span>
          <span style="font-size: 14px; font-weight: 500; opacity: 0.9;">(Daughter & Primary Guardian)</span>
        </div>
        <div style="font-size: 14px; opacity: 0.85; margin-top: 4px;">
          Emergency Phone: <strong id="caretaker-display-phone">+91 7604934874</strong> &bull; Email: <span id="caretaker-display-email">priya.sharma@familycare.in</span>
        </div>
      </div>
      <div style="display: flex; gap: 10px;">
        <button class="btn btn-outline" style="background: white; color: #1E3A8A; font-weight: 700;" onclick="openCaretakerLoginModal()">
          ✏️ Edit Caretaker Info
        </button>
      </div>
    </div>

    <!-- Quick Emergency & Calling Controls (Never Blocked by Cooldown) -->
    <div class="card" style="border: 2px solid #10B981; background: #F0FDF4;">
      <div class="card-header" style="margin-bottom: 8px;">
        <div class="card-title" style="color: #065F46; font-size: 20px;">
          📞 Direct Safe Calling & Emergency Dispatch (SIM Telephony)
        </div>
        <span class="badge badge-success">Zero Twilio &bull; 100% Free</span>
      </div>
      <p style="color: #047857; font-size: 15px; margin-bottom: 16px;">
        Deterministic emergency rules engine places SIM calls directly from patient phone to caregiver. Cooldown is automatically bypassed for manual caregiver requests.
      </p>
      <div style="display: flex; flex-wrap: wrap; gap: 12px;">
        <button class="btn btn-success" style="font-size: 16px; font-weight: 700; padding: 12px 22px;" onclick="triggerCallCaregiver(true)">
          📞 Call Caregiver (+91 7604934874)
        </button>
        <button class="btn btn-outline" style="border-color: #10B981; color: #065F46; font-weight: 700;" onclick="resetCallCooldown()">
          🔄 Reset Call Cooldown & Locks
        </button>
        <button class="btn btn-danger" style="font-size: 16px; font-weight: 700;" onclick="triggerSOS()">
          🚨 Trigger Emergency SOS Alert
        </button>
        <button class="btn btn-outline" style="border-color: #F43F5E; color: #E11D48; font-weight: 700;" onclick="simulateCardiacAlert()">
          ❤️ Simulate Cardiac Alert
        </button>
      </div>
      <div id="call-feedback-box" style="margin-top: 14px; font-size: 15px; font-weight: 600; display: none;"></div>
    </div>

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

    <!-- CardioLife Telemetry & Live ECG Monitor -->
    <div class="card" style="border: 1.5px solid #F43F5E;">
      <div class="card-header">
        <div class="card-title" style="color: #BE123C; font-size: 20px;">
          ❤️ CardioLife Vitals Monitor & Live ECG Stream
        </div>
        <div style="display: flex; gap: 8px;">
          <button class="btn btn-pill" onclick="refreshVitals()">🔄 Refresh Vitals</button>
        </div>
      </div>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
        <div style="background: #FFF1F2; padding: 16px; border-radius: 12px; border: 1px solid #FECDD3;">
          <div style="font-size: 13px; font-weight: 700; color: #9F1239;">HEART RATE</div>
          <div style="font-size: 36px; font-weight: 800; color: #E11D48;" id="vital-hr">74 <span style="font-size: 18px; font-weight: 600;">BPM</span></div>
          <div style="font-size: 13px; color: #9F1239; font-weight: 600;" id="vital-status">Normal Sinus Rhythm</div>
        </div>
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0;">
          <div style="font-size: 13px; font-weight: 700; color: #475569;">BLOOD PRESSURE</div>
          <div style="font-size: 36px; font-weight: 800; color: #1E293B;" id="vital-bp">120/80 <span style="font-size: 18px; font-weight: 600;">mmHg</span></div>
          <div style="font-size: 13px; color: #64748B; font-weight: 600;">Optimal Range</div>
        </div>
        <div style="background: #F8FAFC; padding: 16px; border-radius: 12px; border: 1px solid #E2E8F0;">
          <div style="font-size: 13px; font-weight: 700; color: #475569;">OXYGEN SATURATION</div>
          <div style="font-size: 36px; font-weight: 800; color: #1E293B;" id="vital-spo2">98 <span style="font-size: 18px; font-weight: 600;">%</span></div>
          <div style="font-size: 13px; color: #64748B; font-weight: 600;">SpO2 Healthy</div>
        </div>
      </div>

      <!-- Real-time ECG Trace Canvas -->
      <div class="ecg-box">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span style="color: #34D399; font-size: 12px; font-weight: 700; letter-spacing: 1px;">LIVE LEAD II ECG TRACE</span>
          <span style="color: #94A3B8; font-size: 12px;" id="ecg-time">Live 25mm/s</span>
        </div>
        <canvas id="ecgCanvas" class="ecg-canvas" width="1000" height="120"></canvas>
        <div class="ecg-metrics">
          <span>QRS Duration: 88 ms</span>
          <span>PR Interval: 140 ms</span>
          <span>QTc: 412 ms</span>
          <span style="color: #34D399;">Arrhythmia Filter: ACTIVE</span>
        </div>
      </div>
    </div>

    <!-- Row 2: Live AI Companion Tester -->
    <div class="card" style="border: 2px solid #3B82F6;">
      <div class="card-header">
        <div class="card-title" style="font-size: 20px; color: #1E3A8A;">
          🤖 Test AI Companion (/v1/companion/message)
        </div>
        <div style="display: flex; gap: 8px;">
          <select id="comp-lang-select" class="btn-pill">
            <option value="en">English (en-IN)</option>
            <option value="hi" selected>Hindi (hi-IN)</option>
            <option value="pa">Punjabi (pa-IN)</option>
          </select>
          <button class="btn btn-outline" onclick="pollProactive()">Poll Proactive</button>
        </div>
      </div>

      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px;">
        <span style="font-size: 13px; font-weight: 700; color: var(--text-muted); align-self: center;">Quick Prompts:</span>
        <button class="btn-pill" onclick="setCompPrompt('Who is Priya?')">Who is Priya?</button>
        <button class="btn-pill" onclick="setCompPrompt('What day is it today?')">What day is it?</button>
        <button class="btn-pill" onclick="setCompPrompt('Did I take my morning medicine?')">Did I take my medicine?</button>
        <button class="btn-pill" onclick="setCompPrompt('Madad karo main gir gayi')">🚨 Help (Hindi)</button>
        <button class="btn-pill" onclick="setCompPrompt('How is my heart rate?')">❤️ Heart & Vitals</button>
      </div>

      <div class="test-box">
        <input type="text" id="comp-input" class="test-input" placeholder="Type or ask Ghajini something...">
        <button class="btn btn-primary" onclick="sendCompanionMessage()">Send to Companion</button>
      </div>

      <div class="companion-reply-box" id="comp-reply-container" style="display: none;">
        <div class="companion-reply-text" id="comp-reply-text">Ghajini's reply will appear here...</div>
        <div class="companion-meta" id="comp-meta"></div>
        <div id="comp-person-card"></div>
      </div>
    </div>

    <!-- Row 3: Daily Summary & Weekly History -->
    <div class="grid-2">
      <div class="card">
        <div class="card-header">
          <div class="card-title">Today's Factual Activity Summary</div>
          <button class="btn btn-outline" onclick="loadDashboard()">Refresh</button>
        </div>
        <div class="daily-box" id="daily-summary-text">Loading today's recorded activities...</div>
      </div>

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

    <!-- Row 4: Repeated Questions & Teach Companion -->
    <div class="grid-2">
      <div class="card">
        <div class="card-title" style="margin-bottom: 16px;">Top Repeated Questions (Logged for Caretaker)</div>
        <div id="questions-list">
          <div class="question-item"><span class="question-text">Loading questions...</span></div>
        </div>
      </div>

      <div class="card">
        <div class="card-title" style="margin-bottom: 10px;">Teach Ghajini (Knowledge Embedding)</div>
        <p style="color: var(--text-muted); font-size: 14px; margin-bottom: 12px;">
          Add a new personal fact, routine, or preference. Text is sanitized and embedded into FAISS immediately:
        </p>
        <div style="display: flex; flex-direction: column; gap: 10px;">
          <input type="text" id="teach-input" class="test-input" placeholder="e.g. Priya visits every Sunday with Kabir.">
          <button class="btn btn-success" onclick="teachMemory()">Teach & Embed Memory</button>
        </div>
        <div id="teach-status" style="margin-top: 10px; font-size: 14px; font-weight: 600;"></div>
      </div>
    </div>

    <!-- Row 5: Demo Controls -->
    <div class="card">
      <div class="card-title" style="margin-bottom: 10px;">Demo Controls & Diagnostics</div>
      <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-top: 12px;">
        <button class="btn btn-primary" onclick="resetDemo()">Reset Demo Data</button>
        <button class="btn btn-success" onclick="triggerReminder()">Trigger Medicine Reminder</button>
        <a href="/v1/privacy/export" class="btn btn-outline">Export Personal Data (ZIP)</a>
        <a href="/docs" target="_blank" class="btn btn-outline">FastAPI Docs &rarr;</a>
      </div>
    </div>

  </div>

  <!-- ======================================================== -->
  <!-- PATIENT PORTAL (ULTRA SIMPLE & HIGH CONTRAST)            -->
  <!-- ======================================================== -->
  <div id="patient-view" class="patient-container" style="display: none;">

    <div class="patient-hero">
      <img src="data:image/png;base64,__LOGO_B64__" alt="Ghajini Robot Friend" class="patient-logo">
      <div class="patient-greeting" id="p-greeting">
        नमस्ते! मैं गजिनी हूँ।
      </div>
      <div class="patient-subtitle" id="p-subgreeting">
        आप अपने घर में सुरक्षित हैं। मैं आपके साथ हूँ।
      </div>
    </div>

    <!-- Huge Touch Cards for Elderly User -->
    <div class="patient-action-grid">

      <!-- 1. Talk to Ghajini -->
      <div class="patient-btn-card p-btn-talk" onclick="openPatientTalkModal()">
        <div class="p-btn-icon">🤖</div>
        <div class="p-btn-title" id="p-card-talk-title">गजिनी से बात करें</div>
        <div class="p-btn-desc" id="p-card-talk-desc">मुझसे कोई भी सवाल पूछें</div>
      </div>

      <!-- 2. My Heart & Pulse -->
      <div class="patient-btn-card p-btn-heart" onclick="openPatientHeartModal()">
        <div class="p-btn-icon">❤️</div>
        <div class="p-btn-title" id="p-card-heart-title">मेरा दिल और नब्ज़</div>
        <div class="p-btn-desc" id="p-card-heart-desc">74 BPM &bull; बिल्कुल सामान्य</div>
      </div>

      <!-- 3. Call Caregiver (Priya) -->
      <div class="patient-btn-card p-btn-call" onclick="patientCallCaregiver()">
        <div class="p-btn-icon">📞</div>
        <div class="p-btn-title" id="p-card-call-title">प्रिया को फोन करें</div>
        <div class="p-btn-desc">+91 7604934874 (तुरंत कॉल)</div>
      </div>

      <!-- 4. Emergency SOS -->
      <div class="patient-btn-card p-btn-sos" onclick="patientTriggerSOS()">
        <div class="p-btn-icon">🚨</div>
        <div class="p-btn-title" id="p-card-sos-title">मदद चाहिए / SOS</div>
        <div class="p-btn-desc" id="p-card-sos-desc">परिवार को तुरंत संदेश भेजें</div>
      </div>

    </div>

    <!-- 5. Today's Medicines Card -->
    <div class="card" style="margin-top: 24px; text-align: left; border-radius: 20px; padding: 28px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <div style="font-size: 24px; font-weight: 800; color: #1E293B; display: flex; align-items: center; gap: 10px;">
          <span>💊</span> <span id="p-meds-title">आज की दवाइयां</span>
        </div>
        <span class="badge badge-success" style="font-size: 14px; padding: 6px 14px;">सब सही चल रहा है</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 12px;" id="p-meds-list">
        <div style="display: flex; justify-content: space-between; align-items: center; background: #F0FDF4; border: 1.5px solid #BBF7D0; padding: 16px 20px; border-radius: 14px;">
          <div>
            <div style="font-size: 20px; font-weight: 700; color: #166534;">सुबह 8:00 बजे - डोनेपेज़िल (Donepezil 5mg)</div>
            <div style="font-size: 15px; color: #15803D;">नाश्ते के बाद &bull; ली जा चुकी है ✅</div>
          </div>
          <span style="font-size: 28px;">✅</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; background: #FFFBEB; border: 1.5px solid #FDE68A; padding: 16px 20px; border-radius: 14px;">
          <div>
            <div style="font-size: 20px; font-weight: 700; color: #92400E;">रात 8:00 बजे - ब्लड प्रेशर की गोली</div>
            <div style="font-size: 15px; color: #B45309;">रात के खाने के बाद (बाकी है)</div>
          </div>
          <button class="btn btn-success" style="font-size: 16px; padding: 8px 18px;" onclick="alert('शाबाश! रात की दवाई दर्ज कर ली गई है।')">ली मैंने ✅</button>
        </div>
      </div>
    </div>

  </div>

  <!-- ======================================================== -->
  <!-- MODALS                                                   -->
  <!-- ======================================================== -->

  <!-- Caretaker Login & Info Modal -->
  <div class="patient-modal-overlay" id="caretaker-login-modal">
    <div class="patient-modal">
      <div class="patient-modal-title">
        <span>🛡️</span> Caretaker Information & Login
      </div>
      <p style="color: #64748B; font-size: 15px; margin-bottom: 20px;">
        Enter caretaker credentials and contact information for automated safety alerts and call escalation:
      </p>
      <form onsubmit="saveCaretakerInfo(event)" style="display: flex; flex-direction: column; gap: 14px;">
        <div>
          <label style="font-size: 14px; font-weight: 700; color: #334155; display: block; margin-bottom: 6px;">Full Name</label>
          <input type="text" id="ct-input-name" class="test-input" required value="Priya Sharma" style="width: 100%;">
        </div>
        <div>
          <label style="font-size: 14px; font-weight: 700; color: #334155; display: block; margin-bottom: 6px;">Email Address</label>
          <input type="email" id="ct-input-email" class="test-input" required value="priya.sharma@familycare.in" style="width: 100%;">
        </div>
        <div>
          <label style="font-size: 14px; font-weight: 700; color: #334155; display: block; margin-bottom: 6px;">Primary Phone Number (for SIM calls)</label>
          <input type="tel" id="ct-input-phone" class="test-input" required value="+91 7604934874" style="width: 100%;">
        </div>
        <div>
          <label style="font-size: 14px; font-weight: 700; color: #334155; display: block; margin-bottom: 6px;">Relationship to Patient</label>
          <select id="ct-input-rel" class="test-input" style="width: 100%;">
            <option value="Daughter & Primary Guardian" selected>Daughter & Primary Guardian</option>
            <option value="Son">Son</option>
            <option value="Spouse">Spouse</option>
            <option value="Doctor">Doctor</option>
            <option value="Visiting Nurse">Visiting Nurse</option>
          </select>
        </div>
        <div>
          <label style="font-size: 14px; font-weight: 700; color: #334155; display: block; margin-bottom: 6px;">Access PIN / Password</label>
          <input type="password" id="ct-input-pin" class="test-input" value="1234" style="width: 100%;">
        </div>
        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 10px;">
          <button type="button" class="btn btn-outline" onclick="closeCaretakerLoginModal()">Cancel</button>
          <button type="submit" class="btn btn-primary">Save & Connect</button>
        </div>
      </form>
    </div>
  </div>

  <!-- Patient Talk Modal -->
  <div class="patient-modal-overlay" id="patient-talk-modal">
    <div class="patient-modal">
      <div class="patient-modal-title">
        <span>🤖</span> <span id="p-talk-title">गजिनी से बात करें</span>
      </div>
      <p style="color: #64748B; font-size: 18px; margin-bottom: 16px;" id="p-talk-sub">
        नीचे दिए गए बटन दबाएं या अपना सवाल पूछें:
      </p>

      <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 20px;">
        <button class="btn btn-outline" style="font-size: 18px; padding: 14px 18px; text-align: left;" onclick="patientAskPrompt('Who is Priya?')">
          🌸 प्रिया कौन है? (Who is Priya?)
        </button>
        <button class="btn btn-outline" style="font-size: 18px; padding: 14px 18px; text-align: left;" onclick="patientAskPrompt('What day is it today?')">
          📅 आज कौन सा दिन है? (What day is it?)
        </button>
        <button class="btn btn-outline" style="font-size: 18px; padding: 14px 18px; text-align: left;" onclick="patientAskPrompt('Did I take my morning medicine?')">
          💊 क्या मैंने सुबह की दवाई ले ली?
        </button>
      </div>

      <div class="test-box">
        <input type="text" id="patient-talk-input" class="test-input" style="font-size: 20px; padding: 16px;" placeholder="यहाँ पूछें...">
        <button class="btn btn-primary" style="font-size: 18px; padding: 14px 24px;" onclick="patientSendText()">पूछें</button>
      </div>

      <div class="companion-reply-box" id="patient-reply-box" style="display: none; margin-top: 20px;">
        <div class="companion-reply-text" id="patient-reply-text" style="font-size: 24px;"></div>
      </div>

      <div style="margin-top: 24px; text-align: right;">
        <button class="btn btn-outline" style="font-size: 16px;" onclick="closePatientTalkModal()">बंद करें (Close)</button>
      </div>
    </div>
  </div>

  <!-- Patient Heart Modal -->
  <div class="patient-modal-overlay" id="patient-heart-modal">
    <div class="patient-modal" style="text-align: center;">
      <div style="font-size: 64px; animation: gentle-pulse 1.2s infinite;">❤️</div>
      <div style="font-size: 32px; font-weight: 800; color: #1E293B; margin-top: 10px;" id="p-heart-bpm-text">
        74 BPM
      </div>
      <div style="font-size: 22px; font-weight: 700; color: #10B981; margin-top: 6px;" id="p-heart-status-text">
        आपकी धड़कन बिल्कुल स्वस्थ और स्थिर है
      </div>
      <p style="color: #64748B; font-size: 18px; margin-top: 12px; line-height: 1.5;" id="p-heart-desc-text">
        चिंता की कोई बात नहीं है। आप आराम से बैठें और गहरी सांस लें। प्रिया को आपकी हर धड़कन की जानकारी मिल रही है।
      </p>
      <div style="margin-top: 28px;">
        <button class="btn btn-primary" style="font-size: 18px; padding: 12px 30px;" onclick="closePatientHeartModal()">
          ठीक है (I Feel Good)
        </button>
      </div>
    </div>
  </div>

  <style>
    @keyframes gentle-pulse {
      0% { transform: scale(1); }
      50% { transform: scale(1.18); }
      100% { transform: scale(1); }
    }
  </style>

  <script>
    // State
    let activePortal = 'caretaker';
    let currentLang = 'hi';
    let ecgAnimationId = null;

    // Language Content Maps
    const LANG_DATA = {
      en: {
        greeting: "Hello! I am Ghajini.",
        subgreeting: "You are safe at home with your loved ones. I am right here with you.",
        talkTitle: "Talk to Ghajini",
        talkDesc: "Ask me any question",
        heartTitle: "My Heart & Pulse",
        heartDesc: "74 BPM • Normal and Steady",
        callTitle: "Call Priya",
        sosTitle: "Need Help / SOS",
        sosDesc: "Notify family immediately",
        medsTitle: "Today's Medicines",
        heartModalStatus: "Your heart is beating calm and steady",
        heartModalDesc: "Everything is peaceful and well. Priya has your vitals and you are completely safe."
      },
      hi: {
        greeting: "नमस्ते! मैं गजिनी हूँ।",
        subgreeting: "आप अपने घर में सुरक्षित हैं। मैं आपके साथ हूँ।",
        talkTitle: "गजिनी से बात करें",
        talkDesc: "मुझसे कोई भी सवाल पूछें",
        heartTitle: "मेरा दिल और नब्ज़",
        heartDesc: "74 BPM • बिल्कुल सामान्य",
        callTitle: "प्रिया को फोन करें",
        sosTitle: "मदद चाहिए / SOS",
        sosDesc: "परिवार को तुरंत संदेश भेजें",
        medsTitle: "आज की दवाइयां",
        heartModalStatus: "आपकी धड़कन बिल्कुल स्वस्थ और स्थिर है",
        heartModalDesc: "चिंता की कोई बात नहीं है। आप आराम से बैठें। प्रिया को आपकी हर धड़कन की जानकारी मिल रही है।"
      },
      pa: {
        greeting: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਗਜਨੀ ਹਾਂ।",
        subgreeting: "ਤੁਸੀਂ ਆਪਣੇ ਘਰ ਵਿੱਚ ਬਿਲਕੁਲ ਸੁਰੱਖਿਅਤ ਹੋ। ਮੈਂ ਤੁਹਾਡੇ ਨਾਲ ਹਾਂ।",
        talkTitle: "ਗਜਨੀ ਨਾਲ ਗੱਲ ਕਰੋ",
        talkDesc: "ਮੈਨੂੰ ਕੋਈ ਵੀ ਸਵਾਲ ਪੁੱਛੋ",
        heartTitle: "ਮੇਰਾ ਦਿਲ ਅਤੇ ਨਬਜ਼",
        heartDesc: "74 BPM • ਬਿਲਕੁਲ ਸਹੀ",
        callTitle: "ਪ੍ਰਿਆ ਨੂੰ ਫੋਨ ਕਰੋ",
        sosTitle: "ਮਦਦ ਚਾਹੀਦੀ ਹੈ / SOS",
        sosDesc: "ਪਰਿਵਾਰ ਨੂੰ ਤੁਰੰਤ ਸੁਨੇਹਾ ਭੇਜੋ",
        medsTitle: "ਅੱਜ ਦੀਆਂ ਦਵਾਈਆਂ",
        heartModalStatus: "ਤੁਹਾਡੇ ਦਿਲ ਦੀ ਧੜਕਣ ਬਿਲਕੁਲ ਠੀਕ ਹੈ",
        heartModalDesc: "ਫਿਕਰ ਦੀ ਕੋਈ ਗੱਲ ਨਹੀਂ। ਪ੍ਰਿਆ ਤੁਹਾਡੇ ਨਾਲ ਹੈ।"
      }
    };

    // Portal Switcher
    function switchPortal(portal) {
      activePortal = portal;
      const ctView = document.getElementById('caretaker-view');
      const ptView = document.getElementById('patient-view');
      const ctTab = document.getElementById('tab-caretaker');
      const ptTab = document.getElementById('tab-patient');

      if (portal === 'patient') {
        ctView.style.display = 'none';
        ptView.style.display = 'block';
        ctTab.classList.remove('active');
        ptTab.classList.add('active');
      } else {
        ctView.style.display = 'block';
        ptView.style.display = 'none';
        ctTab.classList.add('active');
        ptTab.classList.remove('active');
        loadDashboard();
      }
    }

    // Language Switcher
    function changeLanguage() {
      const lang = document.getElementById('global-lang').value;
      currentLang = lang;
      document.getElementById('comp-lang-select').value = lang;

      const d = LANG_DATA[lang] || LANG_DATA.en;
      document.getElementById('p-greeting').innerText = d.greeting;
      document.getElementById('p-subgreeting').innerText = d.subgreeting;
      document.getElementById('p-card-talk-title').innerText = d.talkTitle;
      document.getElementById('p-card-talk-desc').innerText = d.talkDesc;
      document.getElementById('p-card-heart-title').innerText = d.heartTitle;
      document.getElementById('p-card-heart-desc').innerText = d.heartDesc;
      document.getElementById('p-card-call-title').innerText = d.callTitle;
      document.getElementById('p-card-sos-title').innerText = d.sosTitle;
      document.getElementById('p-card-sos-desc').innerText = d.sosDesc;
      document.getElementById('p-meds-title').innerText = d.medsTitle;
      document.getElementById('p-heart-status-text').innerText = d.heartModalStatus;
      document.getElementById('p-heart-desc-text').innerText = d.heartModalDesc;
    }

    // Caretaker Info in LocalStorage
    function loadSavedCaretakerInfo() {
      try {
        const saved = JSON.parse(localStorage.getItem('ghajini_caretaker_info') || '{}');
        if (saved.name) {
          document.getElementById('caretaker-display-name').innerText = saved.name;
          document.getElementById('caretaker-display-phone').innerText = saved.phone || '+91 7604934874';
          document.getElementById('caretaker-display-email').innerText = saved.email || 'priya.sharma@familycare.in';
          document.getElementById('ct-input-name').value = saved.name;
          document.getElementById('ct-input-phone').value = saved.phone || '+91 7604934874';
          document.getElementById('ct-input-email').value = saved.email || '';
          if (saved.rel) document.getElementById('ct-input-rel').value = saved.rel;
        }
      } catch (e) {
        console.error(e);
      }
    }

    function openCaretakerLoginModal() {
      document.getElementById('caretaker-login-modal').style.display = 'flex';
    }
    function closeCaretakerLoginModal() {
      document.getElementById('caretaker-login-modal').style.display = 'none';
    }
    function saveCaretakerInfo(e) {
      e.preventDefault();
      const info = {
        name: document.getElementById('ct-input-name').value.trim(),
        email: document.getElementById('ct-input-email').value.trim(),
        phone: document.getElementById('ct-input-phone').value.trim(),
        rel: document.getElementById('ct-input-rel').value,
      };
      localStorage.setItem('ghajini_caretaker_info', JSON.stringify(info));
      document.getElementById('caretaker-display-name').innerText = info.name;
      document.getElementById('caretaker-display-phone').innerText = info.phone;
      document.getElementById('caretaker-display-email').innerText = info.email;
      closeCaretakerLoginModal();
      alert('Caretaker Profile Updated & Connected Successfully!');
    }

    // Dashboard Data Loading
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

        // Daily Summary
        const dailyRes = await fetch('/v1/dashboard/daily-summary');
        const dailyData = await dailyRes.json();
        document.getElementById('daily-summary-text').innerText = dailyData.summary;

        // Fetch Live Vitals
        refreshVitals();

      } catch (e) {
        console.error(e);
      }
    }

    // Vitals & CardioLife
    async function refreshVitals() {
      try {
        const res = await fetch('/v1/cardiolife/current?patient_id=1');
        const data = await res.json();
        document.getElementById('vital-hr').innerHTML = `${data.heart_rate_bpm} <span style="font-size: 18px; font-weight: 600;">BPM</span>`;
        document.getElementById('vital-status').innerText = data.status.replace('_', ' ').toUpperCase();
        document.getElementById('vital-bp').innerHTML = `${data.blood_pressure_systolic}/${data.blood_pressure_diastolic} <span style="font-size: 18px; font-weight: 600;">mmHg</span>`;
        document.getElementById('vital-spo2').innerHTML = `${data.oxygen_saturation} <span style="font-size: 18px; font-weight: 600;">%</span>`;
        document.getElementById('p-card-heart-desc').innerText = `${data.heart_rate_bpm} BPM • ${data.status.replace('_', ' ')}`;
        document.getElementById('p-heart-bpm-text').innerText = `${data.heart_rate_bpm} BPM`;
      } catch (e) {
        console.error(e);
      }
    }

    // Live ECG Canvas Animation
    function initECGAnimation() {
      const canvas = document.getElementById('ecgCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      let offset = 0;

      function renderFrame() {
        const w = canvas.width;
        const h = canvas.height;
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(0, 0, w, h);

        // Draw grid
        ctx.strokeStyle = '#1E293B';
        ctx.lineWidth = 1;
        for (let x = 0; x < w; x += 40) {
          ctx.beginPath();
          ctx.moveTo(x, 0);
          ctx.lineTo(x, h);
          ctx.stroke();
        }
        for (let y = 0; y < h; y += 30) {
          ctx.beginPath();
          ctx.moveTo(0, y);
          ctx.lineTo(w, y);
          ctx.stroke();
        }

        // Draw ECG trace
        ctx.strokeStyle = '#34D399';
        ctx.lineWidth = 2.5;
        ctx.shadowColor = '#34D399';
        ctx.shadowBlur = 8;
        ctx.beginPath();

        const mid = h / 2;
        for (let x = 0; x < w; x++) {
          const t = (x + offset) % 180;
          let y = mid;
          if (t > 40 && t < 55) {
            // P wave
            y = mid - 8 * Math.sin(((t - 40) / 15) * Math.PI);
          } else if (t >= 70 && t < 74) {
            // Q wave
            y = mid + 6;
          } else if (t >= 74 && t < 84) {
            // R spike
            y = mid - 44 * Math.sin(((t - 74) / 10) * Math.PI);
          } else if (t >= 84 && t < 90) {
            // S wave
            y = mid + 12;
          } else if (t >= 110 && t < 140) {
            // T wave
            y = mid - 14 * Math.sin(((t - 110) / 30) * Math.PI);
          }
          if (x === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        offset = (offset + 3) % 180;
        ecgAnimationId = requestAnimationFrame(renderFrame);
      }

      if (ecgAnimationId) cancelAnimationFrame(ecgAnimationId);
      renderFrame();
    }

    // Direct Call with Bypass Cooldown
    async function triggerCallCaregiver(bypass = true) {
      const fb = document.getElementById('call-feedback-box');
      fb.style.display = 'block';
      fb.style.color = '#1E3A8A';
      fb.innerText = 'Initiating SIM telephony call to caregiver...';

      try {
        const res = await fetch('/v1/calls/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: 1,
            reason: 'Manual caretaker interface trigger',
            source: 'manual',
            lang: currentLang,
            bypass_cooldown: bypass
          })
        });
        const data = await res.json();
        if (data.allowed) {
          fb.style.color = '#065F46';
          fb.innerHTML = `✅ <strong>Calling ${data.contact.name} (${data.contact.phone})</strong><br>Spoken to Patient: "${data.patient_message}"<br>Caregiver Telegram: ${data.caregiver_briefing.replace(/\\n/g, ' ')}`;
          window.open(`tel:${data.contact.phone}`);
          loadDashboard();
        } else {
          fb.style.color = '#DC2626';
          fb.innerHTML = `⚠️ <strong>Call Paused:</strong> ${data.block_reason} <button class="btn btn-pill" style="margin-left: 8px;" onclick="resetCallCooldown()">Click to Reset Cooldown</button>`;
        }
      } catch (e) {
        fb.style.color = '#DC2626';
        fb.innerText = 'Call error: ' + e;
      }
    }

    // Reset Call Cooldown Endpoint
    async function resetCallCooldown() {
      try {
        const res = await fetch('/v1/calls/reset-cooldown?patient_id=1', { method: 'POST' });
        const data = await res.json();
        const fb = document.getElementById('call-feedback-box');
        fb.style.display = 'block';
        fb.style.color = '#065F46';
        fb.innerText = '✅ Call cool-down and throttle locks reset successfully! You can call immediately.';
        alert('Cooldown Reset: Unlimited calls can now be placed.');
      } catch (e) {
        alert('Reset error: ' + e);
      }
    }

    // Patient Portal Calls
    function patientCallCaregiver() {
      triggerCallCaregiver(true);
    }

    async function patientTriggerSOS() {
      try {
        const res = await fetch('/v1/alerts/help', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, note: 'Patient pressed Help / SOS on simple touch portal' })
        });
        alert('🚨 आपातकालीन सूचना भेज दी गई है!\n\nEmergency alert dispatched to Priya and doctor.');
        triggerCallCaregiver(true);
      } catch (e) {
        alert('SOS error: ' + e);
      }
    }

    // Patient Modal Handlers
    function openPatientTalkModal() {
      document.getElementById('patient-talk-modal').style.display = 'flex';
      document.getElementById('patient-talk-input').value = '';
      document.getElementById('patient-reply-box').style.display = 'none';
    }
    function closePatientTalkModal() {
      document.getElementById('patient-talk-modal').style.display = 'none';
    }

    function openPatientHeartModal() {
      refreshVitals();
      document.getElementById('patient-heart-modal').style.display = 'flex';
    }
    function closePatientHeartModal() {
      document.getElementById('patient-heart-modal').style.display = 'none';
    }

    function patientAskPrompt(text) {
      document.getElementById('patient-talk-input').value = text;
      patientSendText();
    }

    async function patientSendText() {
      const text = document.getElementById('patient-talk-input').value.trim();
      if (!text) return;
      const replyBox = document.getElementById('patient-reply-box');
      const replyText = document.getElementById('patient-reply-text');
      replyBox.style.display = 'block';
      replyText.innerText = 'गजिनी सोच रही है... (Thinking...)';

      try {
        const res = await fetch('/v1/companion/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, text: text, lang: currentLang, source: 'text' })
        });
        const data = await res.json();
        replyText.innerText = data.reply;
      } catch (e) {
        replyText.innerText = 'मुझे पूरा यकीन नहीं है। क्या मैं प्रिया को फोन करूँ?';
      }
    }

    // Caretaker AI Companion Tester
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
            <div class="person-card" style="display: flex; align-items: center; gap: 14px; background: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 12px 16px; margin-top: 14px;">
              <div style="width: 50px; height: 50px; border-radius: 50%; background: #DBEAFE; color: #1E3A8A; font-weight: 800; display: flex; align-items: center; justify-content: center; font-size: 20px;">${data.person.name.charAt(0)}</div>
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
        alert('Emergency Alert Dispatched: Your family has been notified.');
        loadDashboard();
      } catch (e) {
        alert('SOS failed: ' + e);
      }
    }

    async function simulateCardiacAlert() {
      try {
        const res = await fetch('/v1/cardiolife/simulate?scenario=critical_tachycardia', { method: 'POST' });
        const data = await res.json();
        alert(`❤️ CardioLife Cardiac Alert Dispatched!\n\nHeart Rate: ${data.heart_rate_bpm} BPM (${data.status})\nSystolic/Diastolic: ${data.blood_pressure_systolic}/${data.blood_pressure_diastolic}\nSpO2: ${data.oxygen_saturation}%\n\nCaregiver alert notification logged in DB & dispatched!`);
        loadDashboard();
      } catch (e) {
        alert('Simulation failed: ' + e);
      }
    }

    // Startup initialization
    window.addEventListener('DOMContentLoaded', () => {
      loadSavedCaretakerInfo();
      loadDashboard();
      initECGAnimation();
      changeLanguage();
    });
  </script>
</body>
</html>
"""


def get_dashboard_html() -> HTMLResponse:
    html = DASHBOARD_TEMPLATE.replace("__LOGO_B64__", _logo_b64)
    return HTMLResponse(content=html, status_code=200)
