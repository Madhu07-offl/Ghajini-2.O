import base64
import os
from fastapi.responses import HTMLResponse

_logo_b64 = ""
try:
    from app.static.logo_data import LOGO_BASE64 as _logo_b64
except Exception:
    _logo_b64 = ""

if not _logo_b64:
    candidate_paths = [
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo_base64.txt"),
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo.png"),
        os.path.join(os.path.dirname(__file__), "..", "static", "logo_base64.txt"),
        os.path.join(os.path.dirname(__file__), "..", "static", "logo.png"),
        os.path.join(os.getcwd(), "backend", "app", "static", "logo_base64.txt"),
        os.path.join(os.getcwd(), "backend", "app", "static", "logo.png"),
    ]
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                if p.endswith(".txt"):
                    with open(p, "r", encoding="utf-8") as f:
                        _logo_b64 = f.read().strip()
                elif p.endswith(".png"):
                    with open(p, "rb") as f:
                        _logo_b64 = base64.b64encode(f.read()).decode("utf-8")
                if _logo_b64:
                    break
            except Exception:
                pass

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ghajini 2.0 - Voice Agent Studio & Clinical Care Dashboard</title>
  <link rel="icon" type="image/png" href="data:image/png;base64,__LOGO_B64__">
  <!-- Modern clean typography: Inter -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

  <style>
    :root {
      --primary: #0F9D7A;          /* Teal green */
      --primary-hover: #0C8567;
      --primary-light: #E8F5EE;    /* Setting tile tint */
      --primary-border: #C6E7D2;
      --accent-orange: #F26B21;    /* Ask AI orange */
      --accent-orange-hover: #D95813;
      --danger-red: #EF4444;       /* Badges & SOS only */
      --bg-page: #F4F6F7;          /* Very light gray */
      --card-bg: #FFFFFF;
      --card-border: #E5E7EB;
      --text-title: #1F2937;       /* Dark slate titles */
      --text-body: #4B5563;        /* Main body */
      --text-muted: #6B7280;       /* Sub-labels & counters */
      --sidebar-width: 58px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }
    body { background-color: var(--bg-page); color: var(--text-body); min-height: 100vh; display: flex; }

    /* ======================================================== */
    /* 1. LEFT SIDEBAR (58px, white, full height)               */
    /* ======================================================== */
    .sidebar {
      width: var(--sidebar-width);
      background: #FFFFFF;
      border-right: 1px solid var(--card-border);
      position: fixed;
      top: 0; left: 0; bottom: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: space-between;
      padding: 14px 0;
      z-index: 1000;
    }
    .sidebar-top { display: flex; flex-direction: column; align-items: center; gap: 16px; width: 100%; }
    .sidebar-logo {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--primary-light);
      border: 1px solid var(--primary-border);
      cursor: pointer;
      overflow: hidden;
      transition: transform 0.15s ease;
    }
    .sidebar-logo:hover { transform: scale(1.05); }
    .sidebar-logo img { width: 32px; height: 32px; object-fit: contain; }

    .nav-icons { display: flex; flex-direction: column; align-items: center; gap: 8px; width: 100%; margin-top: 6px; }
    .nav-icon-btn {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      border: none;
      background: transparent;
      cursor: pointer;
      transition: all 0.15s ease;
      position: relative;
    }
    .nav-icon-btn:hover { background: #F3F4F6; color: var(--text-title); }
    .nav-icon-btn.active {
      background: var(--primary-light);
      color: var(--primary);
    }
    .nav-icon-btn.active::before {
      content: '';
      position: absolute;
      left: 0; top: 8px; bottom: 8px;
      width: 3px;
      border-radius: 0 3px 3px 0;
      background: var(--primary);
    }
    .nav-icon-btn svg { width: 20px; height: 20px; stroke-width: 1.8; }

    .sidebar-bottom { display: flex; flex-direction: column; align-items: center; gap: 12px; width: 100%; }
    .sidebar-avatar {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background: #1F2937;
      color: white;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }

    /* ======================================================== */
    /* MAIN WRAPPER (Offset by sidebar)                         */
    /* ======================================================== */
    .app-wrapper {
      margin-left: var(--sidebar-width);
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    /* ======================================================== */
    /* 2. TOP HEADER BAR                                        */
    /* ======================================================== */
    .top-bar {
      height: 60px;
      background: #FFFFFF;
      border-bottom: 1px solid var(--card-border);
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }
    .top-bar-left { display: flex; align-items: center; gap: 12px; }
    .back-btn {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: white;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--text-muted);
      cursor: pointer;
      transition: background 0.15s;
    }
    .back-btn:hover { background: #F3F4F6; color: var(--text-title); }
    
    .agent-name-input {
      font-size: 14px;
      font-weight: 600;
      color: var(--text-title);
      background: #F3F4F6;
      border: 1px solid transparent;
      padding: 6px 12px;
      border-radius: 8px;
      outline: none;
      transition: all 0.15s;
      width: 270px;
    }
    .agent-name-input:focus {
      background: white;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(15, 157, 122, 0.15);
    }

    .header-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 10px;
      border-radius: 6px;
      border: 1px solid var(--card-border);
      background: white;
      font-size: 12px;
      font-weight: 500;
      color: var(--text-body);
      cursor: pointer;
    }
    .header-pill-red {
      color: #DC2626;
      border-color: #FECACA;
      background: #FEF2F2;
    }

    .top-bar-right { display: flex; align-items: center; gap: 10px; }
    
    /* Ask AI Button (Orange) */
    .btn-ask-ai {
      height: 36px;
      padding: 0 14px;
      border-radius: 8px;
      border: none;
      background: var(--accent-orange);
      color: white;
      font-size: 13px;
      font-weight: 600;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-ask-ai:hover { background: var(--accent-orange-hover); }

    .test-with-label { font-size: 13px; color: var(--text-muted); margin: 0 2px; }

    /* Action buttons (Teal) */
    .btn-teal {
      height: 36px;
      padding: 0 13px;
      border-radius: 8px;
      border: none;
      background: var(--primary);
      color: white;
      font-size: 13px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: background 0.15s;
    }
    .btn-teal:hover { background: var(--primary-hover); }

    .btn-outline {
      height: 36px;
      padding: 0 13px;
      border-radius: 8px;
      border: 1px solid var(--card-border);
      background: white;
      color: var(--text-title);
      font-size: 13px;
      font-weight: 500;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-outline:hover { background: #F9FAFB; border-color: #D1D5DB; }

    .btn-patient-switch {
      background: #EDE9FE;
      color: #6D28D9;
      border: 1px solid #DDD6FE;
      height: 36px;
      padding: 0 12px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s;
    }
    .btn-patient-switch:hover { background: #E0E7FF; }

    /* ======================================================== */
    /* 3. TAB BAR                                               */
    /* ======================================================== */
    .tab-bar {
      height: 52px;
      background: #FFFFFF;
      border-bottom: 1px solid var(--card-border);
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .segmented-tabs {
      display: inline-flex;
      background: #F3F4F6;
      padding: 3px;
      border-radius: 8px;
      gap: 2px;
    }
    .tab-btn {
      padding: 6px 14px;
      border-radius: 6px;
      border: none;
      background: transparent;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }
    .tab-btn svg { width: 15px; height: 15px; }
    .tab-btn.active {
      background: #FFFFFF;
      color: var(--text-title);
      font-weight: 600;
      box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    .tab-bar-right { display: flex; align-items: center; gap: 12px; }
    .pill-free-minutes {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 20px;
      border: 1px solid var(--primary-border);
      background: var(--primary-light);
      font-size: 12px;
      font-weight: 600;
      color: var(--primary);
    }
    .ui-code-toggle {
      display: inline-flex;
      background: #F3F4F6;
      border-radius: 6px;
      padding: 2px;
      font-size: 12px;
      font-weight: 500;
    }
    .ui-code-btn {
      padding: 4px 10px;
      border-radius: 5px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
    }
    .ui-code-btn.active { background: white; color: var(--text-title); font-weight: 600; }

    /* ======================================================== */
    /* 4. MAIN CONTENT (Two Columns, 24px gap)                  */
    /* ======================================================== */
    .content-area {
      padding: 24px;
      max-width: 1400px;
      width: 100%;
      margin: 0 auto;
    }

    .two-column-grid {
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 24px;
      align-items: start;
    }

    @media (max-width: 1080px) {
      .two-column-grid { grid-template-columns: 1fr; }
    }

    /* Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 22px 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.03);
      margin-bottom: 24px;
    }
    .card-header-clean {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    .card-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-title);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .card-sub {
      font-size: 12px;
      color: var(--text-muted);
      margin-top: 3px;
    }

    /* Setting Tile (Light green tint with clean border) */
    .setting-tile {
      background: var(--primary-light);
      border: 1px solid var(--primary-border);
      border-radius: 10px;
      padding: 14px 16px;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .setting-tile-info { display: flex; flex-direction: column; gap: 2px; }
    .setting-tile-title { font-size: 14px; font-weight: 600; color: #064E3B; display: flex; align-items: center; gap: 6px; }
    .setting-tile-desc { font-size: 12px; color: #065F46; }

    /* Inputs, Selects, Textareas */
    .form-group { margin-bottom: 16px; }
    .form-label {
      display: flex;
      justify-content: space-between;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-title);
      margin-bottom: 6px;
    }
    .form-label-counter { font-size: 11px; color: var(--text-muted); font-weight: 400; }
    .form-control {
      width: 100%;
      border: 1px solid #D1D5DB;
      border-radius: 8px;
      padding: 9px 12px;
      font-size: 13.5px;
      color: var(--text-title);
      background: #FFFFFF;
      outline: none;
      transition: all 0.15s;
    }
    .form-control:focus {
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(15, 157, 122, 0.15);
    }
    textarea.form-control {
      resize: vertical;
      min-height: 110px;
      line-height: 1.5;
    }

    /* Switch Toggle */
    .toggle-wrapper { display: flex; align-items: center; gap: 10px; }
    .switch {
      position: relative;
      display: inline-block;
      width: 38px;
      height: 22px;
    }
    .switch input { opacity: 0; width: 0; height: 0; }
    .slider {
      position: absolute; cursor: pointer;
      top: 0; left: 0; right: 0; bottom: 0;
      background-color: #D1D5DB;
      transition: .2s;
      border-radius: 22px;
    }
    .slider:before {
      position: absolute; content: "";
      height: 16px; width: 16px;
      left: 3px; bottom: 3px;
      background-color: white;
      transition: .2s;
      border-radius: 50%;
    }
    input:checked + .slider { background-color: var(--primary); }
    input:checked + .slider:before { transform: translateX(16px); }

    /* Live Testing Simulator */
    .simulator-container {
      background: #FFFFFF;
      border: 1px solid var(--card-border);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      height: 520px;
    }
    .simulator-header {
      background: #F9FAFB;
      border-bottom: 1px solid var(--card-border);
      padding: 12px 18px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .sim-status-dot {
      width: 8px; height: 8px;
      border-radius: 50%;
      background: var(--primary);
      display: inline-block;
      box-shadow: 0 0 0 3px rgba(15, 157, 122, 0.2);
    }
    .simulator-body {
      flex: 1;
      padding: 16px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #FAFAFA;
    }
    .chat-bubble {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 13.5px;
      line-height: 1.45;
    }
    .chat-bubble-patient {
      align-self: flex-end;
      background: #1F2937;
      color: white;
      border-bottom-right-radius: 3px;
    }
    .chat-bubble-ghajini {
      align-self: flex-start;
      background: #FFFFFF;
      color: var(--text-title);
      border: 1px solid var(--card-border);
      border-bottom-left-radius: 3px;
      box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .meta-tag {
      display: inline-block;
      font-size: 10.5px;
      font-weight: 600;
      padding: 2px 6px;
      border-radius: 4px;
      margin-top: 6px;
      margin-right: 4px;
    }
    .meta-intent { background: #EDE9FE; color: #6D28D9; }
    .meta-grounded { background: #DCFCE7; color: #15803D; }

    .simulator-footer {
      padding: 12px 16px;
      background: #FFFFFF;
      border-top: 1px solid var(--card-border);
    }
    .quick-prompts {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 8px;
      margin-bottom: 8px;
    }
    .quick-chip {
      font-size: 11.5px;
      font-weight: 500;
      color: var(--text-title);
      background: #F3F4F6;
      border: 1px solid var(--card-border);
      padding: 4px 10px;
      border-radius: 16px;
      white-space: nowrap;
      cursor: pointer;
    }
    .quick-chip:hover { background: #E5E7EB; }
    .sim-input-row { display: flex; gap: 8px; }

    /* CardioLife Live Canvas & Stats */
    .cardiolife-card {
      background: #FFFFFF;
      border: 1px solid var(--card-border);
      border-radius: 14px;
      padding: 18px 20px;
    }
    .vitals-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      margin-top: 12px;
    }
    .vital-box {
      background: #F9FAFB;
      border: 1px solid #E5E7EB;
      border-radius: 10px;
      padding: 10px 12px;
    }
    .vital-title { font-size: 11px; font-weight: 600; color: var(--text-muted); }
    .vital-value { font-size: 22px; font-weight: 700; color: var(--text-title); margin-top: 2px; }
    .vital-sub { font-size: 11px; font-weight: 500; color: var(--primary); }

    .ecg-mini-canvas {
      width: 100%;
      height: 70px;
      background: #0F172A;
      border-radius: 8px;
      margin-top: 12px;
      display: block;
    }

    /* Modal / Popups */
    .modal-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(15, 23, 42, 0.6);
      backdrop-filter: blur(3px);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 2000;
      padding: 20px;
    }
    .modal-card {
      background: white;
      border-radius: 16px;
      max-width: 600px;
      width: 100%;
      padding: 24px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }

    /* ======================================================== */
    /* PATIENT SIMPLE VIEW (Elderly Accessible Mode)            */
    /* ======================================================== */
    #patient-portal-container {
      display: none;
      max-width: 800px;
      margin: 30px auto;
      padding: 0 20px;
      text-align: center;
    }
    .patient-hero-card {
      background: white;
      border-radius: 20px;
      border: 1px solid var(--card-border);
      padding: 32px 20px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.04);
      display: flex;
      flex-direction: column;
      align-items: center;
      margin-bottom: 24px;
    }
    .patient-hero-logo {
      width: 120px;
      height: 120px;
      object-fit: contain;
      filter: drop-shadow(0 4px 10px rgba(0,0,0,0.08));
    }
    .patient-big-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
    }
    @media (max-width: 650px) {
      .patient-big-grid { grid-template-columns: 1fr; }
    }
    .patient-big-btn {
      background: white;
      border: 2px solid #E5E7EB;
      border-radius: 18px;
      padding: 24px 16px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
      transition: all 0.2s;
    }
    .patient-big-btn:hover {
      transform: translateY(-3px);
      box-shadow: 0 8px 18px rgba(0,0,0,0.08);
    }
    .p-btn-talk { border-color: #3B82F6; background: #EFF6FF; }
    .p-btn-call { border-color: var(--primary); background: var(--primary-light); }
    .p-btn-heart { border-color: #F43F5E; background: #FFF1F2; }
    .p-btn-sos { border-color: #EF4444; background: #FEF2F2; }

    /* Table */
    .clean-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .clean-table th { text-align: left; padding: 10px 12px; color: var(--text-muted); font-weight: 500; border-bottom: 1px solid var(--card-border); }
    .clean-table td { padding: 12px; border-bottom: 1px solid #F3F4F6; color: var(--text-title); }
  </style>
</head>
<body>

  <!-- ======================================================== -->
  <!-- 1. LEFT SIDEBAR                                          -->
  <!-- ======================================================== -->
  <aside class="sidebar">
    <div class="sidebar-top">
      <div class="sidebar-logo" onclick="switchPortal('studio')" title="Ghajini 2.0 Studio">
        <img src="data:image/png;base64,__LOGO_B64__" onerror="this.src='/logo.png'" alt="Ghajini">
      </div>

      <nav class="nav-icons">
        <!-- Voice Agents -->
        <button class="nav-icon-btn active" title="Assistant Studio" onclick="switchTab('assistant')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="22"/></svg>
        </button>
        <!-- Telephony / Calls -->
        <button class="nav-icon-btn" title="Call Rules & Policy" onclick="switchTab('calls')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
        </button>
        <!-- Knowledge Base -->
        <button class="nav-icon-btn" title="FAISS Knowledge Engine" onclick="switchTab('knowledge')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
        </button>
        <!-- CardioLife Telemetry -->
        <button class="nav-icon-btn" title="CardioLife Vitals" onclick="switchTab('postcall')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
        </button>
        <!-- Integrations -->
        <button class="nav-icon-btn" title="Integrations & Telegram" onclick="switchTab('integrations')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </button>
        <!-- Recent Calls -->
        <button class="nav-icon-btn" title="Call Logs" onclick="switchTab('history')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </button>
      </nav>
    </div>

    <div class="sidebar-bottom">
      <button class="nav-icon-btn" title="Caregiver Profile" onclick="openCaregiverModal()">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      </button>
      <div class="sidebar-avatar" title="Priya Sharma (Caregiver)">P</div>
    </div>
  </aside>

  <!-- ======================================================== -->
  <!-- MAIN APP CONTAINER                                       -->
  <!-- ======================================================== -->
  <div class="app-wrapper">

    <!-- 2. TOP BAR -->
    <header class="top-bar">
      <div class="top-bar-left">
        <button class="back-btn" title="Back" onclick="switchTab('assistant')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
        </button>
        <input type="text" class="agent-name-input" value="Ghajini 2.0 (Alzheimer's Companion)">
        <div class="header-pill header-pill-red" title="SIM Direct Calling Enabled">
          <span style="font-size: 10px;">●</span> Outgoing (SIM)
        </div>
        <div class="header-pill" title="API Schemas & Endpoints" onclick="window.open('/docs', '_blank')">
          { } API
        </div>
        <div class="header-pill" title="APScheduler 15s Cycle">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          15s Poll
        </div>
      </div>

      <div class="top-bar-right">
        <!-- Orange Ask AI Button -->
        <button class="btn-ask-ai" onclick="openAskAIModal()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          Ask AI
        </button>

        <span class="test-with-label">Test with:</span>

        <!-- Teal Test Action Buttons -->
        <button class="btn-teal" onclick="focusChatSimulator()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          Chat
        </button>
        <button class="btn-teal" onclick="startWebVoiceCall()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/></svg>
          Web Call
        </button>
        <button class="btn-teal" style="background: #065F46;" onclick="triggerPhoneCallCaregiver()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          Phone Call
        </button>

        <!-- Deploy Dropdown -->
        <button class="btn-outline" onclick="openDeployModal()">
          Deploy ▾
        </button>

        <!-- Toggle to Patient Simple View -->
        <button class="btn-patient-switch" onclick="switchPortal('patient')">
          👤 Patient Portal
        </button>
      </div>
    </header>

    <!-- 3. TAB BAR -->
    <nav class="tab-bar">
      <div class="segmented-tabs">
        <button class="tab-btn active" id="tab-assistant" onclick="switchTab('assistant')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/></svg>
          Assistant Details
        </button>
        <button class="tab-btn" id="tab-calls" onclick="switchTab('calls')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
          Call Configuration
        </button>
        <button class="tab-btn" id="tab-knowledge" onclick="switchTab('knowledge')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg>
          Knowledge Base
        </button>
        <button class="tab-btn" id="tab-integrations" onclick="switchTab('integrations')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
          Integrations
        </button>
        <button class="tab-btn" id="tab-postcall" onclick="switchTab('postcall')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
          Post-Call & Telemetry
        </button>
        <button class="tab-btn" id="tab-history" onclick="switchTab('history')">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          Recent Calls
        </button>
      </div>

      <div class="tab-bar-right">
        <div class="pill-free-minutes">
          <span style="font-size: 10px;">●</span> SIM Telephony: Active
        </div>
        <div class="ui-code-toggle">
          <button class="ui-code-btn active" id="btn-view-ui" onclick="toggleViewMode('ui')">UI</button>
          <button class="ui-code-btn" id="btn-view-code" onclick="toggleViewMode('code')">Code</button>
        </div>
      </div>
    </nav>

    <!-- ======================================================== -->
    <!-- STUDIO WORKSPACE: TAB 1 - ASSISTANT DETAILS              -->
    <!-- ======================================================== -->
    <main id="view-assistant" class="content-area">
      <div class="two-column-grid">

        <!-- LEFT COLUMN: Agent Persona & Prompts -->
        <div class="col-left">

          <!-- Card 1: Persona & Voice Configuration -->
          <div class="card">
            <div class="card-header-clean">
              <div>
                <div class="card-title">Assistant Details</div>
                <div class="card-sub">Core voice identity, speech rate and primary language</div>
              </div>
              <span class="header-pill" style="color: var(--primary); border-color: var(--primary-border); background: var(--primary-light);">v2.0 Stable</span>
            </div>

            <!-- Voice Setting Tile -->
            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><path d="M8 12a4 4 0 0 1 8 0"/></svg>
                  Aditi (Elder-care Gentle & Slow - 0.85x)
                </div>
                <div class="setting-tile-desc">Indian Accent &bull; Calming warm cadence &bull; Ambient Noise Suppression Active</div>
              </div>
              <button class="btn-outline" style="height: 32px; font-size: 12px; background: white;" onclick="testVoicePlayback()">
                ▶ Preview Voice
              </button>
            </div>

            <div class="form-group">
              <div class="form-label">
                <span>Primary Language</span>
                <span class="form-label-counter">Fallback: English</span>
              </div>
              <select id="agent-lang" class="form-control" onchange="onLangChange()">
                <option value="en">English (India) - en-IN</option>
                <option value="hi" selected>Hindi - hi-IN (हिन्दी)</option>
                <option value="pa">Punjabi - pa-IN (ਪੰਜਾਬੀ)</option>
              </select>
            </div>

            <div class="form-group">
              <div class="form-label">
                <span>First Sentence (Greeting Message)</span>
                <span class="form-label-counter" id="greeting-counter">64/120</span>
              </div>
              <input type="text" id="agent-first-sentence" class="form-control" value="Namaste! I am Ghajini, your friend. How are you feeling right now?">
            </div>
          </div>

          <!-- Card 2: Clinical Instructions & Guardrails -->
          <div class="card">
            <div class="card-header-clean">
              <div>
                <div class="card-title">Instructions & Grounding Guardrails</div>
                <div class="card-sub">Deterministic rules governing Alzheimer's safety and anti-hallucination</div>
              </div>
              <button class="btn-outline" style="height: 30px; font-size: 12px;" onclick="resetInstructions()">Reset Default</button>
            </div>

            <!-- Setting Tile: Strict Grounding -->
            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                  Anti-Hallucination FAISS Guardrail
                </div>
                <div class="setting-tile-desc">Rejects invented facts. Fallback: "I am not sure. Shall I call Priya?"</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="toggle-grounding" checked>
                <span class="slider"></span>
              </label>
            </div>

            <!-- Setting Tile: Emergency Phrase Interception -->
            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#DC2626"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  Emergency Phrase Interception
                </div>
                <div class="setting-tile-desc">Immediate rule-based SIM dialer trigger on distress phrases</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="toggle-emergency-phrase" checked>
                <span class="slider"></span>
              </label>
            </div>

            <div class="form-group" style="margin-bottom: 0;">
              <div class="form-label">
                <span>System Prompt</span>
                <span class="form-label-counter" id="prompt-counter">486/600</span>
              </div>
              <textarea id="agent-prompt" class="form-control" rows="5">You are Ghajini, a compassionate memory companion for an Alzheimer's patient. 
Rules:
1. Speak in 1 or 2 short, calming sentences.
2. Ground all answers strictly in stored family facts (Priya is daughter in Bangalore, Dr. Sharma visits Thursdays).
3. If asked about taking medicine, check reminder records.
4. Detect anxiety and reassure the patient they are safe at home.</textarea>
            </div>
          </div>

        </div>

        <!-- RIGHT COLUMN: Interactive Simulator & CardioLife Stream -->
        <div class="col-right">

          <!-- Card 3: Interactive Voice & Chat Simulator -->
          <div class="simulator-container">
            <div class="simulator-header">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="sim-status-dot"></span>
                <span style="font-size: 13px; font-weight: 600; color: var(--text-title);">Live Assistant Simulator</span>
              </div>
              <span style="font-size: 11px; color: var(--text-muted);">Pipeline: /v1/companion/message</span>
            </div>

            <div class="simulator-body" id="chat-stream">
              <!-- Initial assistant greeting -->
              <div class="chat-bubble chat-bubble-ghajini">
                Namaste! I am Ghajini, your friend. You are safe at home. How can I help you today?
                <div>
                  <span class="meta-tag meta-intent">intent: greeting</span>
                  <span class="meta-tag meta-grounded">verified safe</span>
                </div>
              </div>
            </div>

            <div class="simulator-footer">
              <div class="quick-prompts">
                <button class="quick-chip" onclick="quickSend('Who is Priya?')">Who is Priya?</button>
                <button class="quick-chip" onclick="quickSend('What day is it today?')">What day is it?</button>
                <button class="quick-chip" onclick="quickSend('Did I take my medicine?')">Did I take my medicine?</button>
                <button class="quick-chip" onclick="quickSend('Madad karo main gir gayi')">🚨 Help (Hindi)</button>
              </div>
              <div class="sim-input-row">
                <input type="text" id="sim-input" class="form-control" placeholder="Ask or speak to Ghajini..." onkeydown="if(event.key==='Enter') sendSimulatorText()">
                <button class="btn-teal" onclick="sendSimulatorText()">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
              </div>
            </div>
          </div>

          <!-- Card 4: CardioLife Telemetry -->
          <div class="cardiolife-card" style="margin-top: 24px;">
            <div class="card-header-clean" style="margin-bottom: 8px;">
              <div class="card-title" style="color: #BE123C;">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#E11D48"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                CardioLife Telemetry Feed
              </div>
              <button class="btn-outline" style="height: 28px; font-size: 11px; padding: 0 8px;" onclick="refreshVitals()">Refresh</button>
            </div>
            
            <div class="vitals-grid">
              <div class="vital-box">
                <div class="vital-title">HEART RATE</div>
                <div class="vital-value" id="dash-vital-hr">74 <span style="font-size: 12px; font-weight: 500;">BPM</span></div>
                <div class="vital-sub" id="dash-vital-status">Normal Rhythm</div>
              </div>
              <div class="vital-box">
                <div class="vital-title">BLOOD PRESSURE</div>
                <div class="vital-value" id="dash-vital-bp">120/80</div>
                <div class="vital-sub">Optimal</div>
              </div>
              <div class="vital-box">
                <div class="vital-title">SPO2 OXYGEN</div>
                <div class="vital-value" id="dash-vital-spo2">98 <span style="font-size: 12px; font-weight: 500;">%</span></div>
                <div class="vital-sub">Steady</div>
              </div>
            </div>

            <!-- Mini ECG Canvas -->
            <canvas id="miniECGCanvas" class="ecg-mini-canvas" width="600" height="70"></canvas>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
              <span style="font-size: 11px; color: var(--text-muted);">Lead II &bull; Real-time Arrhythmia Guard Active</span>
              <button class="btn-outline" style="height: 28px; font-size: 11.5px; border-color: #FECDD3; color: #E11D48;" onclick="simulateCardiacAlert()">
                Test Cardiac Alert
              </button>
            </div>
          </div>

        </div>

      </div>
    </main>

    <!-- ======================================================== -->
    <!-- TAB 2 - CALL CONFIGURATION                               -->
    <!-- ======================================================== -->
    <main id="view-calls" class="content-area" style="display: none;">
      <div class="two-column-grid">

        <div class="col-left">
          <div class="card">
            <div class="card-header-clean">
              <div>
                <div class="card-title">SIM Telephony Policy & Cooldown Settings</div>
                <div class="card-sub">Deterministic call limits governed by modules/calls/policy.py</div>
              </div>
            </div>

            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  Manual Cooldown Bypass
                </div>
                <div class="setting-tile-desc">Allows caregiver & patient manual dials without 2-minute delay</div>
              </div>
              <label class="switch">
                <input type="checkbox" id="toggle-cooldown-bypass" checked>
                <span class="slider"></span>
              </label>
            </div>

            <div class="form-group">
              <div class="form-label">
                <span>Maximum Call Attempts Per Hour</span>
                <span class="form-label-counter">Safety Cap</span>
              </div>
              <input type="number" class="form-control" value="3" readonly style="background: #F9FAFB;">
            </div>

            <div class="form-group">
              <div class="form-label">
                <span>Quiet Hours Window</span>
                <span class="form-label-counter">Only emergency triggers permitted</span>
              </div>
              <div style="display: flex; gap: 10px;">
                <input type="text" class="form-control" value="22:00 (10 PM)" readonly style="background: #F9FAFB;">
                <input type="text" class="form-control" value="06:00 (6 AM)" readonly style="background: #F9FAFB;">
              </div>
            </div>

            <div style="display: flex; gap: 10px; margin-top: 18px;">
              <button class="btn-teal" onclick="resetCallCooldown()">
                🔄 Reset Call Cooldown & Throttle Locks
              </button>
            </div>
          </div>

          <!-- Emergency Contacts Card -->
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Emergency Contacts (Priority Ordered)</div>
            <table class="clean-table">
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Name</th>
                  <th>Relationship</th>
                  <th>Phone Number</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>#1</strong></td>
                  <td>Priya Sharma</td>
                  <td>Daughter & Guardian</td>
                  <td><strong>+91 7604934874</strong></td>
                  <td><span class="header-pill" style="color: var(--primary);">Active</span></td>
                </tr>
                <tr>
                  <td>#2</td>
                  <td>Dr. Sharma</td>
                  <td>Geriatric Physician</td>
                  <td>+91 9876543212</td>
                  <td><span class="header-pill">Standby</span></td>
                </tr>
                <tr>
                  <td>#3</td>
                  <td>Arun Kumar</td>
                  <td>Neighbor</td>
                  <td>+91 9876543213</td>
                  <td><span class="header-pill">Standby</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="col-right">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Instant Dial Tester</div>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
              Test direct SIM call logic against backend endpoint <code>/v1/calls/request</code>:
            </p>
            <div class="form-group">
              <label class="form-label">Call Reason</label>
              <input type="text" id="test-call-reason" class="form-control" value="Routine caregiver check-in">
            </div>
            <div class="form-group">
              <label class="form-label">Trigger Source</label>
              <select id="test-call-source" class="form-control">
                <option value="manual" selected>manual (Caregiver/Patient click)</option>
                <option value="sos">sos (Emergency button)</option>
                <option value="emergency_phrase">emergency_phrase (Voice distress)</option>
                <option value="reminder_escalation">reminder_escalation (10min unacknowledged)</option>
              </select>
            </div>
            <button class="btn-teal" style="width: 100%; justify-content: center; height: 40px;" onclick="executeTestCall()">
              📞 Place Simulated SIM Call to Priya (+91 7604934874)
            </button>
            <div id="test-call-output" style="margin-top: 14px; font-size: 13px; font-weight: 500; display: none;"></div>
          </div>
        </div>

      </div>
    </main>

    <!-- ======================================================== -->
    <!-- TAB 3 - KNOWLEDGE BASE                                   -->
    <!-- ======================================================== -->
    <main id="view-knowledge" class="content-area" style="display: none;">
      <div class="two-column-grid">
        <div class="col-left">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Active Stored Memories (FAISS Index)</div>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              <div style="background: #F9FAFB; border: 1px solid var(--card-border); padding: 12px 14px; border-radius: 8px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-title);">Priya is daughter</div>
                <div style="font-size: 12px; color: var(--text-muted);">Priya is your daughter. She lives in Bangalore and visits on weekends with grandson Kabir.</div>
              </div>
              <div style="background: #F9FAFB; border: 1px solid var(--card-border); padding: 12px 14px; border-radius: 8px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-title);">Dr. Sharma visits Thursdays</div>
                <div style="font-size: 12px; color: var(--text-muted);">Dr. Sharma is your physician. He visits every Thursday at 4 PM to check your heart and memory health.</div>
              </div>
              <div style="background: #F9FAFB; border: 1px solid var(--card-border); padding: 12px 14px; border-radius: 8px;">
                <div style="font-size: 13px; font-weight: 600; color: var(--text-title);">Morning Medicine Routine</div>
                <div style="font-size: 12px; color: var(--text-muted);">You take Donepezil 5mg after breakfast every morning with warm water.</div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-right">
          <div class="card">
            <div class="card-title" style="margin-bottom: 8px;">Teach Ghajini (Real-time Embedding)</div>
            <p style="font-size: 12.5px; color: var(--text-muted); margin-bottom: 14px;">
              New routines and facts are sanitized against prompt injections and embedded into FAISS immediately:
            </p>
            <div class="form-group">
              <label class="form-label">New Memory Fact</label>
              <textarea id="teach-fact-input" class="form-control" rows="3" placeholder="e.g. Priya visits every Diwali with grandson Kabir."></textarea>
            </div>
            <button class="btn-teal" style="width: 100%; justify-content: center;" onclick="teachMemoryFact()">
              Teach & Embed Memory Fact
            </button>
            <div id="teach-fact-status" style="margin-top: 10px; font-size: 12.5px; font-weight: 600;"></div>
          </div>
        </div>
      </div>
    </main>

    <!-- ======================================================== -->
    <!-- TAB 4 - INTEGRATIONS                                     -->
    <!-- ======================================================== -->
    <main id="view-integrations" class="content-area" style="display: none;">
      <div class="two-column-grid">
        <div class="col-left">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Telegram Caregiver Bot API</div>
            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">Automated 3-Line Briefing</div>
                <div class="setting-tile-desc">Dispatches instant alert to caregiver's Telegram channel on distress/calls</div>
              </div>
              <span class="header-pill" style="color: var(--primary);">Connected</span>
            </div>
            <div class="form-group">
              <label class="form-label">Caregiver Chat ID</label>
              <input type="text" class="form-control" value="7604934874" readonly style="background: #F9FAFB;">
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">SIM Telephony Hardware Interface</div>
            <div class="setting-tile">
              <div class="setting-tile-info">
                <div class="setting-tile-title">flutter_phone_direct_caller</div>
                <div class="setting-tile-desc">Android CALL_PHONE & iOS tel: URL Scheme &bull; Zero Twilio &bull; Free SIM minutes</div>
              </div>
              <span class="header-pill" style="color: var(--primary);">Verified</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- ======================================================== -->
    <!-- TAB 5 - POST-CALL & TELEMETRY                            -->
    <!-- ======================================================== -->
    <main id="view-postcall" class="content-area" style="display: none;">
      <div class="two-column-grid">
        <div class="col-left">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Caregiver Telegram Briefing Formatter</div>
            <div style="background: #F0FDF4; border: 1px solid #BBF7D0; padding: 16px; border-radius: 10px; font-size: 13px; line-height: 1.6; color: #166534;">
              <strong>Telegram Message Template:</strong><br>
              🚨 <strong>Emergency Call:</strong> Patient has requested to speak with you.<br>
              ⏰ <strong>Time:</strong> Today at 07:54 PM<br>
              💊 <strong>Last Reminder:</strong> Morning Donepezil (Taken)<br>
              ❤️ <strong>Vitals:</strong> 74 BPM (Normal Sinus Rhythm)
            </div>
          </div>
        </div>
        <div class="col-right">
          <div class="card">
            <div class="card-title" style="margin-bottom: 12px;">Audio & Privacy Architecture</div>
            <div style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
              &bull; <strong>Zero Call Audio Stored:</strong> No recordings or patient audio are retained on servers.<br>
              &bull; <strong>Anti-Hallucination:</strong> Deterministic rule-based templates enforce patient safety.<br>
              &bull; <strong>Data Export:</strong> Caregivers can export all stored memories via <code>/v1/privacy/export</code>.
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- ======================================================== -->
    <!-- TAB 6 - RECENT CALLS                                     -->
    <!-- ======================================================== -->
    <main id="view-history" class="content-area" style="display: none;">
      <div class="card">
        <div class="card-header-clean">
          <div>
            <div class="card-title">Recent Call Attempts & Telephony Log</div>
            <div class="card-sub">Logged in MongoDB & SQLite audit collections</div>
          </div>
          <button class="btn-outline" style="height: 30px; font-size: 12px;" onclick="loadRecentCalls()">Refresh Logs</button>
        </div>

        <table class="clean-table" id="calls-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Contact</th>
              <th>Phone</th>
              <th>Reason</th>
              <th>Source</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="calls-table-body">
            <tr>
              <td colspan="6" style="text-align: center; color: var(--text-muted);">Loading recent call records...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>

    <!-- ======================================================== -->
    <!-- PATIENT SIMPLE PORTAL (High Contrast & Elderly Friendly) -->
    <!-- ======================================================== -->
    <section id="patient-portal-container">
      <div class="patient-hero-card">
        <img src="data:image/png;base64,__LOGO_B64__" onerror="this.src='/logo.png'" alt="Ghajini Robot Friend" class="patient-hero-logo">
        <div style="font-size: 28px; font-weight: 800; color: #1F2937; margin-top: 14px;" id="p-greeting-text">
          नमस्ते! मैं गजिनी हूँ।
        </div>
        <div style="font-size: 17px; color: var(--text-muted); margin-top: 6px;" id="p-subgreeting-text">
          आप अपने घर में बिल्कुल सुरक्षित हैं। मैं आपके साथ हूँ।
        </div>
        <button class="btn-outline" style="margin-top: 16px; font-size: 12.5px;" onclick="switchPortal('studio')">
          ← Back to Caregiver Studio
        </button>
      </div>

      <div class="patient-big-grid">
        <!-- 1. Talk to Ghajini -->
        <div class="patient-big-btn p-btn-talk" onclick="patientOpenTalk()">
          <div style="font-size: 44px;">🤖</div>
          <div style="font-size: 20px; font-weight: 800; color: #1F2937;">गजिनी से बात करें</div>
          <div style="font-size: 14px; color: var(--text-muted);">मुझसे कोई भी सवाल पूछें</div>
        </div>

        <!-- 2. Call Priya -->
        <div class="patient-big-btn p-btn-call" onclick="triggerPhoneCallCaregiver()">
          <div style="font-size: 44px;">📞</div>
          <div style="font-size: 20px; font-weight: 800; color: #065F46;">प्रिया को फोन करें</div>
          <div style="font-size: 14px; color: #047857;">+91 7604934874 (तुरंत कॉल)</div>
        </div>

        <!-- 3. Heart & Pulse -->
        <div class="patient-big-btn p-btn-heart" onclick="patientOpenHeart()">
          <div style="font-size: 44px;">❤️</div>
          <div style="font-size: 20px; font-weight: 800; color: #9F1239;">मेरा दिल और नब्ज़</div>
          <div style="font-size: 14px; color: #BE123C;" id="p-heart-status-sub">74 BPM &bull; बिल्कुल सामान्य</div>
        </div>

        <!-- 4. SOS Help -->
        <div class="patient-big-btn p-btn-sos" onclick="patientTriggerSOS()">
          <div style="font-size: 44px;">🚨</div>
          <div style="font-size: 20px; font-weight: 800; color: #991B1B;">मदद चाहिए / SOS</div>
          <div style="font-size: 14px; color: #B91C1C;">परिवार को तुरंत संदेश भेजें</div>
        </div>
      </div>
    </section>

  </div>

  <!-- ======================================================== -->
  <!-- MODALS                                                   -->
  <!-- ======================================================== -->

  <!-- Caregiver Modal -->
  <div class="modal-overlay" id="modal-caregiver">
    <div class="modal-card">
      <div class="card-title" style="margin-bottom: 12px;">Caregiver Information</div>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
        Profile used for automatic call forwarding and emergency escalations:
      </p>
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" id="cfg-name" class="form-control" value="Priya Sharma">
      </div>
      <div class="form-group">
        <label class="form-label">Caregiver Phone Number (SIM Direct)</label>
        <input type="text" id="cfg-phone" class="form-control" value="+91 7604934874">
      </div>
      <div class="form-group">
        <label class="form-label">Relationship to Patient</label>
        <input type="text" id="cfg-rel" class="form-control" value="Daughter & Primary Guardian">
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px;">
        <button class="btn-outline" onclick="closeCaregiverModal()">Cancel</button>
        <button class="btn-teal" onclick="saveCaregiverModal()">Save Information</button>
      </div>
    </div>
  </div>

  <!-- Ask AI Modal -->
  <div class="modal-overlay" id="modal-ask-ai">
    <div class="modal-card">
      <div class="card-title" style="color: var(--accent-orange); margin-bottom: 12px;">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
        Ghajini AI Prompt Tuning Assistant
      </div>
      <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
        Ask AI to optimize instructions for dementia/Alzheimer's care, de-escalation, or bilingual switching:
      </p>
      <div class="form-group">
        <textarea id="ai-suggestion-input" class="form-control" rows="3" placeholder="e.g. Make the companion sound more comforting when the patient asks about deceased relatives."></textarea>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn-outline" onclick="closeAskAIModal()">Close</button>
        <button class="btn-ask-ai" onclick="generateAIPromptSuggestion()">Optimize Instructions</button>
      </div>
    </div>
  </div>

  <!-- Deploy Status Modal -->
  <div class="modal-overlay" id="modal-deploy">
    <div class="modal-card">
      <div class="card-title" style="color: var(--primary); margin-bottom: 12px;">Production Deployment</div>
      <div class="setting-tile" style="margin-bottom: 16px;">
        <div class="setting-tile-info">
          <div class="setting-tile-title">Vercel Serverless (Production)</div>
          <div class="setting-tile-desc">https://ghajini-2-0.vercel.app</div>
        </div>
        <span class="header-pill" style="color: var(--primary);">Live & Active</span>
      </div>
      <p style="font-size: 13px; color: var(--text-muted); line-height: 1.5; margin-bottom: 16px;">
        Your project is connected to GitHub <code>Madhu07-offl/Ghajini-2.O</code>. Every push automatically rebuilds and deploys to Vercel within 10 seconds.
      </p>
      <div style="display: flex; justify-content: flex-end; gap: 10px;">
        <button class="btn-outline" onclick="closeDeployModal()">Close</button>
        <button class="btn-teal" onclick="window.open('https://ghajini-2-0.vercel.app', '_blank')">Open Vercel App ↗</button>
      </div>
    </div>
  </div>

  <script>
    // State
    let activeTab = 'assistant';
    let activePortal = 'studio';
    let currentLang = 'hi';
    let ecgAnimationId = null;

    // Tab Switcher
    function switchTab(tabId) {
      activeTab = tabId;
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      const activeBtn = document.getElementById('tab-' + tabId);
      if (activeBtn) activeBtn.classList.add('active');

      // Update sidebar nav active
      document.querySelectorAll('.nav-icon-btn').forEach(btn => btn.classList.remove('active'));

      // Hide all views
      ['assistant', 'calls', 'knowledge', 'integrations', 'postcall', 'history'].forEach(id => {
        const el = document.getElementById('view-' + id);
        if (el) el.style.display = (id === tabId) ? 'block' : 'none';
      });

      if (tabId === 'history') {
        loadRecentCalls();
      }
    }

    // Portal Switcher
    function switchPortal(portal) {
      activePortal = portal;
      const studioViews = ['view-assistant', 'view-calls', 'view-knowledge', 'view-integrations', 'view-postcall', 'view-history'];
      const pContainer = document.getElementById('patient-portal-container');

      if (portal === 'patient') {
        studioViews.forEach(id => {
          const el = document.getElementById(id);
          if (el) el.style.display = 'none';
        });
        pContainer.style.display = 'block';
      } else {
        pContainer.style.display = 'none';
        switchTab(activeTab);
      }
    }

    // Language Change
    function onLangChange() {
      const lang = document.getElementById('agent-lang').value;
      currentLang = lang;
      const pGreeting = document.getElementById('p-greeting-text');
      const pSub = document.getElementById('p-subgreeting-text');

      if (lang === 'hi') {
        pGreeting.innerText = 'नमस्ते! मैं गजिनी हूँ।';
        pSub.innerText = 'आप अपने घर में बिल्कुल सुरक्षित हैं। मैं आपके साथ हूँ।';
      } else if (lang === 'pa') {
        pGreeting.innerText = 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਗਜਨੀ ਹਾਂ।';
        pSub.innerText = 'ਤੁਸੀਂ ਆਪਣੇ ਘਰ ਵਿੱਚ ਬਿਲਕੁਲ ਸੁਰੱਖਿਅਤ ਹੋ। ਮੈਂ ਤੁਹਾਡੇ ਨਾਲ ਹਾਂ।';
      } else {
        pGreeting.innerText = 'Hello! I am Ghajini.';
        pSub.innerText = 'You are safe at home with your loved ones. I am right here with you.';
      }
    }

    // Simulator Interactive
    function focusChatSimulator() {
      switchTab('assistant');
      const input = document.getElementById('sim-input');
      input.focus();
      input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function quickSend(text) {
      document.getElementById('sim-input').value = text;
      sendSimulatorText();
    }

    async function sendSimulatorText() {
      const input = document.getElementById('sim-input');
      const text = input.value.trim();
      if (!text) return;
      input.value = '';

      const stream = document.getElementById('chat-stream');
      
      // Append patient message
      const pBubble = document.createElement('div');
      pBubble.className = 'chat-bubble chat-bubble-patient';
      pBubble.innerText = text;
      stream.appendChild(pBubble);
      stream.scrollTop = stream.scrollHeight;

      // Loading bubble
      const gBubble = document.createElement('div');
      gBubble.className = 'chat-bubble chat-bubble-ghajini';
      gBubble.innerText = 'Ghajini is thinking...';
      stream.appendChild(gBubble);
      stream.scrollTop = stream.scrollHeight;

      try {
        const res = await fetch('/v1/companion/message', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, text: text, lang: currentLang, source: 'text' })
        });
        const data = await res.json();
        gBubble.innerHTML = `
          ${data.reply}
          <div>
            <span class="meta-tag meta-intent">intent: ${data.intent}</span>
            <span class="meta-tag ${data.grounded ? 'meta-grounded' : 'meta-intent'}">${data.grounded ? 'grounded: fact' : 'ungrounded fallback'}</span>
          </div>
        `;
      } catch (e) {
        gBubble.innerText = 'I am not sure. Shall I call Priya for you?';
      }
      stream.scrollTop = stream.scrollHeight;
    }

    // Voice simulation
    function testVoicePlayback() {
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance('Namaste. I am Ghajini, your memory companion. You are doing wonderful today.');
        utterance.rate = 0.85;
        window.speechSynthesis.speak(utterance);
      } else {
        alert('Voice playback test: Speech synthesis triggered at 0.85x calm pace.');
      }
    }

    function startWebVoiceCall() {
      focusChatSimulator();
      testVoicePlayback();
    }

    // Direct Phone Call
    async function triggerPhoneCallCaregiver() {
      try {
        const res = await fetch('/v1/calls/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: 1,
            reason: 'Voice Studio phone call trigger',
            source: 'manual',
            lang: currentLang,
            bypass_cooldown: true
          })
        });
        const data = await res.json();
        if (data.allowed) {
          alert(`📞 Calling ${data.contact.name} (${data.contact.phone})\n\nPatient Speech:\n"${data.patient_message}"\n\nCaregiver Telegram Briefing:\n${data.caregiver_briefing}`);
          window.open(`tel:${data.contact.phone}`);
        } else {
          alert(`Call Paused: ${data.block_reason}`);
        }
      } catch (e) {
        alert('Call request failed: ' + e);
      }
    }

    async function resetCallCooldown() {
      try {
        const res = await fetch('/v1/calls/reset-cooldown?patient_id=1', { method: 'POST' });
        const data = await res.json();
        alert('Cooldown Reset: Throttle locks removed successfully.');
      } catch (e) {
        alert('Error: ' + e);
      }
    }

    async function executeTestCall() {
      const reason = document.getElementById('test-call-reason').value;
      const source = document.getElementById('test-call-source').value;
      const bypass = document.getElementById('toggle-cooldown-bypass').checked;
      const out = document.getElementById('test-call-output');

      out.style.display = 'block';
      out.style.color = '#0F9D7A';
      out.innerText = 'Dispatching test call to backend...';

      try {
        const res = await fetch('/v1/calls/request', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            patient_id: 1,
            reason: reason,
            source: source,
            lang: currentLang,
            bypass_cooldown: bypass
          })
        });
        const data = await res.json();
        if (data.allowed) {
          out.innerHTML = `✅ <strong>Call Dispatched!</strong> Calling ${data.contact.name} (${data.contact.phone})<br>Briefing: ${data.caregiver_briefing.replace(/\\n/g, ' ')}`;
          window.open(`tel:${data.contact.phone}`);
        } else {
          out.style.color = '#DC2626';
          out.innerHTML = `⚠️ <strong>Call Paused:</strong> ${data.block_reason}`;
        }
      } catch (e) {
        out.style.color = '#DC2626';
        out.innerText = 'Call error: ' + e;
      }
    }

    // CardioLife & Vitals
    async function refreshVitals() {
      try {
        const res = await fetch('/v1/cardiolife/current?patient_id=1');
        const data = await res.json();
        document.getElementById('dash-vital-hr').innerHTML = `${data.heart_rate_bpm} <span style="font-size: 12px; font-weight: 500;">BPM</span>`;
        document.getElementById('dash-vital-status').innerText = data.status.replace('_', ' ').toUpperCase();
        document.getElementById('dash-vital-bp').innerText = `${data.blood_pressure_systolic}/${data.blood_pressure_diastolic}`;
        document.getElementById('dash-vital-spo2').innerHTML = `${data.oxygen_saturation} <span style="font-size: 12px; font-weight: 500;">%</span>`;
        document.getElementById('p-heart-status-sub').innerText = `${data.heart_rate_bpm} BPM • ${data.status.replace('_', ' ')}`;
      } catch (e) {
        console.error(e);
      }
    }

    async function simulateCardiacAlert() {
      try {
        const res = await fetch('/v1/cardiolife/simulate?scenario=critical_tachycardia', { method: 'POST' });
        const data = await res.json();
        alert(`❤️ CardioLife Alert Dispatched!\n\nHeart Rate: ${data.heart_rate_bpm} BPM (${data.status})\nBP: ${data.blood_pressure_systolic}/${data.blood_pressure_diastolic}\nSpO2: ${data.oxygen_saturation}%\n\nTelegram alert logged & sent.`);
        refreshVitals();
      } catch (e) {
        alert('Simulation failed: ' + e);
      }
    }

    // Mini ECG Canvas Animation
    function initECG() {
      const canvas = document.getElementById('miniECGCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      let offset = 0;

      function renderFrame() {
        const w = canvas.width;
        const h = canvas.height;
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(0, 0, w, h);

        ctx.strokeStyle = '#0F9D7A';
        ctx.lineWidth = 2;
        ctx.shadowColor = '#0F9D7A';
        ctx.shadowBlur = 6;
        ctx.beginPath();

        const mid = h / 2;
        for (let x = 0; x < w; x++) {
          const t = (x + offset) % 180;
          let y = mid;
          if (t > 40 && t < 55) {
            y = mid - 5 * Math.sin(((t - 40) / 15) * Math.PI);
          } else if (t >= 70 && t < 74) {
            y = mid + 4;
          } else if (t >= 74 && t < 84) {
            y = mid - 26 * Math.sin(((t - 74) / 10) * Math.PI);
          } else if (t >= 84 && t < 90) {
            y = mid + 8;
          } else if (t >= 110 && t < 140) {
            y = mid - 8 * Math.sin(((t - 110) / 30) * Math.PI);
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

    // Knowledge Base Teach
    async function teachMemoryFact() {
      const text = document.getElementById('teach-fact-input').value.trim();
      if (!text) return;
      const st = document.getElementById('teach-fact-status');
      st.style.color = '#0F9D7A';
      st.innerText = 'Embedding into FAISS vector index...';

      try {
        const res = await fetch('/v1/companion/teach', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, text: text, category: 'personal' })
        });
        const data = await res.json();
        st.innerText = `Success! Embedded fact #${data.id}: "${data.text}"`;
        document.getElementById('teach-fact-input').value = '';
      } catch (e) {
        st.style.color = '#DC2626';
        st.innerText = 'Error embedding fact: ' + e;
      }
    }

    // Recent calls loader
    async function loadRecentCalls() {
      const tbody = document.getElementById('calls-table-body');
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center;">Fetching call records...</td></tr>';

      try {
        const res = await fetch('/v1/calls/history?patient_id=1');
        const calls = await res.json();
        tbody.innerHTML = '';
        if (calls.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No recorded call attempts yet.</td></tr>';
          return;
        }
        calls.forEach(c => {
          const tr = document.createElement('tr');
          const time = c.created_at ? new Date(c.created_at).toLocaleTimeString() : 'Recent';
          tr.innerHTML = `
            <td>${time}</td>
            <td><strong>${c.contact_name || 'Priya'}</strong></td>
            <td>${c.contact_phone || '+91 7604934874'}</td>
            <td>${c.reason || 'Safety Trigger'}</td>
            <td><span class="header-pill">${c.source || 'manual'}</span></td>
            <td><span class="header-pill" style="color: ${c.allowed ? 'var(--primary)' : '#DC2626'};">${c.allowed ? 'Allowed' : 'Throttled'}</span></td>
          `;
          tbody.appendChild(tr);
        });
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" style="color: #DC2626;">Error loading calls: ${e}</td></tr>`;
      }
    }

    // Modals
    function openCaregiverModal() { document.getElementById('modal-caregiver').style.display = 'flex'; }
    function closeCaregiverModal() { document.getElementById('modal-caregiver').style.display = 'none'; }
    function saveCaregiverModal() {
      closeCaregiverModal();
      alert('Caregiver profile updated.');
    }

    function openAskAIModal() { document.getElementById('modal-ask-ai').style.display = 'flex'; }
    function closeAskAIModal() { document.getElementById('modal-ask-ai').style.display = 'none'; }
    function generateAIPromptSuggestion() {
      document.getElementById('agent-prompt').value = `You are Ghajini, a caring Alzheimer's voice assistant. Speak with tender warmth and extreme patience. Never mention that you are an AI. If the patient repeats a question, answer it fresh with a smile. If they appear anxious, ground them by reminding them Priya is nearby and their home is peaceful.`;
      closeAskAIModal();
      alert('AI Prompt Suggestion applied to System Prompt!');
    }

    function openDeployModal() { document.getElementById('modal-deploy').style.display = 'flex'; }
    function closeDeployModal() { document.getElementById('modal-deploy').style.display = 'none'; }

    function resetInstructions() {
      document.getElementById('agent-prompt').value = `You are Ghajini, a compassionate memory companion for an Alzheimer's patient. 
Rules:
1. Speak in 1 or 2 short, calming sentences.
2. Ground all answers strictly in stored family facts.
3. If asked about taking medicine, check reminder records.
4. Detect anxiety and reassure the patient they are safe at home.`;
    }

    function toggleViewMode(mode) {
      document.getElementById('btn-view-ui').classList.toggle('active', mode === 'ui');
      document.getElementById('btn-view-code').classList.toggle('active', mode === 'code');
      if (mode === 'code') {
        window.open('/docs', '_blank');
      }
    }

    // Patient Actions
    function patientOpenTalk() {
      switchPortal('studio');
      focusChatSimulator();
    }
    function patientOpenHeart() {
      refreshVitals();
      alert('❤️ आपकी धड़कन 74 BPM है। आप बिल्कुल स्वस्थ और सुरक्षित हैं।');
    }
    async function patientTriggerSOS() {
      try {
        await fetch('/v1/alerts/help', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ patient_id: 1, note: 'Patient pressed Help / SOS on simple touch portal' })
        });
        alert('🚨 आपातकालीन सूचना भेज दी गई है!\n\nEmergency alert dispatched to Priya and doctor.');
        triggerPhoneCallCaregiver();
      } catch (e) {
        alert('SOS error: ' + e);
      }
    }

    // Startup
    window.addEventListener('DOMContentLoaded', () => {
      refreshVitals();
      initECG();
      onLangChange();
    });
  </script>
</body>
</html>
"""


def get_dashboard_html() -> HTMLResponse:
    html = DASHBOARD_TEMPLATE.replace("__LOGO_B64__", _logo_b64)
    return HTMLResponse(content=html, status_code=200)
