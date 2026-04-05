import streamlit as st
import json
import time
from orchestrator.graph import run_incident_analysis

st.set_page_config(
    page_title="DevOps Incident Analysis Suite",
    page_icon="🚨",
    layout="wide"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #FF4B4B;
        text-align: center;
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="main-header">🚨 DevOps Incident Analysis Suite</div>',
    unsafe_allow_html=True
)
st.markdown("---")

with st.sidebar:
    st.title("Control Panel")
    st.markdown("### Powered by")
    st.markdown("- 🤖 Claude Sonnet 4.5")
    st.markdown("- 🔗 LangGraph")
    st.markdown("- 📊 5 Specialized Agents")
    st.markdown("---")
    st.markdown("### Agent Pipeline")
    for agent in [
        "1️⃣ Log Classifier",
        "2️⃣ Remediation Agent",
        "3️⃣ Notification Agent",
        "4️⃣ Cookbook Synthesizer",
        "5️⃣ JIRA Ticket Agent"
    ]:
        st.markdown(f"- {agent}")
    st.markdown("---")
    st.markdown("### How to use")
    st.markdown("1. Upload or paste logs")
    st.markdown("2. Click Analyze")
    st.markdown("3. View results per agent")


def sev_color(sev):
    return {
        "CRITICAL": "#FF4B4B",
        "HIGH":     "#FF6D00",
        "MEDIUM":   "#FFD600",
        "LOW":      "#00C853"
    }.get(str(sev).upper(), "#888888")


def safe_str(val):
    """Always return a plain string from any value."""
    if val is None:
        return "N/A"
    if isinstance(val, str):
        return val
    if isinstance(val, (dict, list)):
        return json.dumps(val, indent=2)
    return str(val)


def safe_list(val):
    """Always return a list."""
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("["):
            try:
                return json.loads(val)
            except Exception:
                pass
        return [val] if val else []
    return []


tab1, tab2 = st.tabs(["📤 Upload Logs", "📝 Paste Logs"])
log_content = None

with tab1:
    uploaded_file = st.file_uploader(
        "Upload your log file", type=["log", "txt"])
    if uploaded_file:
        log_content = uploaded_file.read().decode("utf-8")
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        with st.expander("Preview log file"):
            st.code(log_content[:2000], language="bash")

with tab2:
    pasted_logs = st.text_area(
        "Paste your logs here", height=200,
        placeholder="Paste your log content here...")
    if pasted_logs:
        log_content = pasted_logs

if log_content:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        analyze_button = st.button(
            "🚀 Analyze Incident", use_container_width=True, type="primary")

    if analyze_button:
        st.markdown("---")
        st.markdown("## 🔄 Agent Pipeline Running...")

        progress_bar = st.progress(0)
        status_text  = st.empty()
        agent_statuses = {
            "Log Classifier":       st.empty(),
            "Remediation Agent":    st.empty(),
            "Notification Agent":   st.empty(),
            "Cookbook Synthesizer": st.empty(),
            "JIRA Ticket Agent":    st.empty()
        }
        for name, ph in agent_statuses.items():
            ph.info(f"⏳ {name} — waiting...")

        status_text.text("Starting analysis pipeline...")
        progress_bar.progress(10)
        agent_statuses["Log Classifier"].warning("🔄 Log Classifier — running...")

        try:
            with st.spinner("Running all 5 agents via LangGraph orchestrator..."):
                t0     = time.time()
                result = run_incident_analysis(log_content)
                t1     = time.time()

            progress_bar.progress(100)
            for name, ph in agent_statuses.items():
                ph.success(f"✅ {name} — done")
            status_text.success(f"✅ Analysis complete in {round(t1-t0, 2)} seconds!")

            st.markdown("---")
            st.markdown("## 📊 Analysis Results")

            classified   = result.get("classified_logs", {}) or {}
            remediation  = result.get("remediation", {})     or {}
            notification = result.get("notification", {})    or {}
            cookbook     = result.get("cookbook", {})        or {}
            jira         = result.get("jira_tickets", {})    or {}

            issues   = safe_list(classified.get("issues", []))
            critical = len([i for i in issues if isinstance(i, dict) and i.get("severity") == "CRITICAL"])
            high     = len([i for i in issues if isinstance(i, dict) and i.get("severity") == "HIGH"])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Issues",      len(issues))
            c2.metric("Critical",          critical)
            c3.metric("High",              high)
            c4.metric("Services Affected", len(safe_list(classified.get("affected_services", []))))

            st.markdown("---")

            # ── AGENT 1 ──────────────────────────────────────────────────────
            with st.expander("🔍 Agent 1 — Log Classifier", expanded=True):
                st.markdown(f"**Summary:** {safe_str(classified.get('summary'))}")
                st.markdown(f"**Time Range:** {safe_str(classified.get('time_range'))}")
                services = safe_list(classified.get("affected_services", []))
                st.markdown(f"**Affected Services:** {', '.join(services)}")
                st.markdown("### Issues Detected")
                for issue in issues:
                    if not isinstance(issue, dict):
                        continue
                    sev   = issue.get("severity", "LOW")
                    color = sev_color(sev)
                    st.markdown(f"""
<div style="background:#1E1E1E; border-left:5px solid {color};
            border-radius:8px; padding:1rem; margin:0.5rem 0;">
    <span style="background:{color}; color:black; font-weight:bold;
                 font-size:0.8rem; padding:2px 10px; border-radius:20px;">
        {sev}
    </span>
    <h4 style="color:white; margin:0.5rem 0 0.3rem;">{safe_str(issue.get('title'))}</h4>
    <p style="color:#aaa; margin:0; font-size:0.9rem;">
        Service: <code>{safe_str(issue.get('affected_service'))}</code>
    </p>
    <p style="color:#ddd; margin:0.4rem 0 0; font-size:0.9rem;">
        {safe_str(issue.get('description'))}
    </p>
</div>
                    """, unsafe_allow_html=True)

            # ── AGENT 2 ──────────────────────────────────────────────────────
            with st.expander("🔧 Agent 2 — Remediation Plan", expanded=True):

                st.markdown(f"""
<div style="background:#0d1f0d; border-left:5px solid #00C853;
            border-radius:8px; padding:1rem 1.5rem; margin-bottom:1.5rem;">
    <p style="color:#00C853; font-size:0.75rem; margin:0 0 4px;
               text-transform:uppercase; letter-spacing:1px;">
        Overall Recommendation
    </p>
    <p style="color:white; font-size:1rem; margin:0;">
        {safe_str(remediation.get('overall_recommendation'))}
    </p>
</div>
                """, unsafe_allow_html=True)

                priority = safe_list(remediation.get("priority_order", []))
                if priority:
                    st.markdown("#### 🎯 Priority Order")
                    cols = st.columns(len(priority))
                    for i, (col, issue_id) in enumerate(zip(cols, priority)):
                        with col:
                            st.markdown(f"""
<div style="background:#1E1E1E; border-radius:8px; padding:0.6rem;
            text-align:center; border:1px solid #333;">
    <span style="color:#FF4B4B; font-weight:bold;">#{i+1}</span><br/>
    <span style="color:white; font-size:0.85rem;">{safe_str(issue_id)}</span>
</div>
                            """, unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)

                remediations = safe_list(remediation.get("remediations", []))
                for rem in remediations:
                    if not isinstance(rem, dict):
                        continue
                    sev   = rem.get("severity", "LOW")
                    color = sev_color(sev)

                    # Header
                    st.markdown(f"""
<div style="background:#1E1E1E; border-radius:10px; border-left:5px solid {color};
            padding:1rem 1.5rem; margin:1rem 0 0.5rem;">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="color:{color}; font-weight:bold; font-size:0.8rem;
                     background:{color}22; padding:3px 10px; border-radius:20px;">
            {sev}
        </span>
        <span style="color:#888; font-size:0.8rem;">
            ⏱ {safe_str(rem.get('estimated_time'))}
        </span>
    </div>
    <h3 style="color:white; margin:0.5rem 0 0;">{safe_str(rem.get('title'))}</h3>
</div>
                    """, unsafe_allow_html=True)

                    # 3 info cards
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"""
<div style="background:#12121f; border-radius:8px; padding:1rem;
            border:1px solid #333; min-height:100px;">
    <p style="color:#888; font-size:0.72rem; margin:0 0 6px;
               text-transform:uppercase; letter-spacing:1px;">Root Cause</p>
    <p style="color:#fff; font-size:0.88rem; margin:0; line-height:1.5;">
        {safe_str(rem.get('root_cause'))}
    </p>
</div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
<div style="background:#0d1f0d; border-radius:8px; padding:1rem;
            border:1px solid #1a3a1a; min-height:100px;">
    <p style="color:#00C853; font-size:0.72rem; margin:0 0 6px;
               text-transform:uppercase; letter-spacing:1px;">Immediate Action</p>
    <p style="color:#fff; font-size:0.88rem; margin:0; line-height:1.5;">
        {safe_str(rem.get('immediate_action'))}
    </p>
</div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown(f"""
<div style="background:#1a1200; border-radius:8px; padding:1rem;
            border:1px solid #3a2a00; min-height:100px;">
    <p style="color:#FFD600; font-size:0.72rem; margin:0 0 6px;
               text-transform:uppercase; letter-spacing:1px;">Prevention</p>
    <p style="color:#fff; font-size:0.88rem; margin:0; line-height:1.5;">
        {safe_str(rem.get('prevention'))}
    </p>
</div>
                        """, unsafe_allow_html=True)

                    st.markdown("<br/>", unsafe_allow_html=True)

                    # Steps
                    steps = safe_list(rem.get("steps", []))
                    if steps:
                        st.markdown("##### 📋 Step-by-Step Fix")
                        for i, step in enumerate(steps):
                            step_text = step if isinstance(step, str) else safe_str(step.get("action")) if isinstance(step, dict) else str(step)
                            st.markdown(f"""
<div style="display:flex; align-items:flex-start; gap:12px;
            margin:6px 0; padding:10px; background:#1a1a1a; border-radius:8px;">
    <span style="background:{color}; color:black; font-weight:bold;
                 font-size:0.8rem; min-width:26px; height:26px;
                 border-radius:50%; display:flex; align-items:center;
                 justify-content:center; flex-shrink:0;">
        {i+1}
    </span>
    <span style="color:#ddd; font-size:0.9rem; padding-top:3px; line-height:1.5;">
        {step_text}
    </span>
</div>
                            """, unsafe_allow_html=True)

                    # Commands
                    commands = safe_list(rem.get("commands", []))
                    if commands:
                        st.markdown("##### ⌨️ Commands to Run")
                        st.code("\n".join([safe_str(c) for c in commands]), language="bash")

                    st.markdown("---")

            # ── AGENT 3 ──────────────────────────────────────────────────────
            with st.expander("📨 Agent 3 — Slack Notification", expanded=True):
                status = notification.get("status", "unknown")
                if status == "sent":
                    st.success("✅ Slack message sent successfully!")
                elif status == "mocked":
                    st.info("🔄 Mock mode — message would be sent to Slack")
                else:
                    st.error(f"❌ Error: {notification.get('error')}")
                st.markdown(f"**Message:** {safe_str(notification.get('message'))}")
                st.markdown("**Slack Blocks Preview:**")
                st.json(notification.get("blocks", []))

            # ── AGENT 4 ──────────────────────────────────────────────────────
            with st.expander("📚 Agent 4 — Incident Cookbook", expanded=True):

                title      = safe_str(cookbook.get("title", "Incident Cookbook"))
                created_for= safe_str(cookbook.get("created_for", ""))
                cb_type    = safe_str(cookbook.get("incident_type", "N/A"))
                cb_sev     = safe_str(cookbook.get("severity_level", "N/A"))
                pre_checks = safe_list(cookbook.get("pre_checks", []))
                checklist  = safe_list(cookbook.get("checklist", []))
                escalation = safe_list(cookbook.get("escalation_path", []))
                metrics    = safe_list(cookbook.get("key_metrics_to_monitor", []))
                prevention = safe_list(cookbook.get("prevention_measures", []))
                lessons    = safe_str(cookbook.get("lessons_learned", "N/A"))

                color_cb = sev_color(cb_sev)

                # Banner
                st.markdown(f"""
<div style="background:#1a1a2e; border-left:5px solid #7C4DFF;
            border-radius:8px; padding:1rem 1.5rem; margin-bottom:1.5rem;">
    <p style="color:#7C4DFF; font-size:0.75rem; margin:0 0 4px;
               text-transform:uppercase; letter-spacing:1px;">Incident Cookbook</p>
    <h2 style="color:white; margin:0 0 4px;">{title}</h2>
    <p style="color:#aaa; margin:0; font-size:0.88rem;">{created_for}</p>
</div>
                """, unsafe_allow_html=True)

                # Meta
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
<div style="background:#1E1E1E; border-radius:8px; padding:1rem;
            text-align:center; border:1px solid #333;">
    <p style="color:#888; font-size:0.72rem; margin:0 0 4px; text-transform:uppercase;">
        Incident Type</p>
    <p style="color:#7C4DFF; font-weight:bold; margin:0; font-size:0.88rem;">
        {cb_type}</p>
</div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
<div style="background:#1E1E1E; border-radius:8px; padding:1rem;
            text-align:center; border:1px solid #333;">
    <p style="color:#888; font-size:0.72rem; margin:0 0 4px; text-transform:uppercase;">
        Severity</p>
    <p style="color:{color_cb}; font-weight:bold; margin:0; font-size:0.95rem;">
        {cb_sev}</p>
</div>
                    """, unsafe_allow_html=True)
                with col3:
                    total_steps = sum(
                        len(safe_list(p.get("steps", [])))
                        for p in checklist if isinstance(p, dict)
                    )
                    st.markdown(f"""
<div style="background:#1E1E1E; border-radius:8px; padding:1rem;
            text-align:center; border:1px solid #333;">
    <p style="color:#888; font-size:0.72rem; margin:0 0 4px; text-transform:uppercase;">
        Total Steps</p>
    <p style="color:#00C853; font-weight:bold; margin:0; font-size:0.95rem;">
        {total_steps} steps</p>
</div>
                    """, unsafe_allow_html=True)

                st.markdown("<br/>", unsafe_allow_html=True)

                # Pre-checks
                if pre_checks:
                    st.markdown("#### 🔎 Pre-Checks Before You Start")
                    for i, check in enumerate(pre_checks):
                        st.markdown(f"""
<div style="display:flex; align-items:flex-start; gap:12px; margin:5px 0;
            padding:10px 14px; background:#12121f; border-radius:8px;
            border:1px solid #2a2a4a;">
    <span style="color:#7C4DFF; font-weight:bold; font-size:0.85rem;
                 min-width:22px; flex-shrink:0;">{i+1}.</span>
    <span style="color:#ddd; font-size:0.9rem; line-height:1.5;">
        {safe_str(check)}
    </span>
</div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)

                # Phases
                phase_colors = {
                    "Detection":     "#378ADD",
                    "Containment":   "#FF6D00",
                    "Resolution":    "#00C853",
                    "Post-Incident": "#7C4DFF"
                }
                phase_icons = {
                    "Detection":     "🔍",
                    "Containment":   "🛡️",
                    "Resolution":    "✅",
                    "Post-Incident": "📝"
                }

                if checklist:
                    st.markdown("#### 📋 Response Checklist")
                    for phase in checklist:
                        if not isinstance(phase, dict):
                            continue
                        phase_name = safe_str(phase.get("phase", "Phase"))
                        p_color    = phase_colors.get(phase_name, "#7C4DFF")
                        p_icon     = phase_icons.get(phase_name, "▶️")

                        st.markdown(f"""
<div style="background:#1E1E1E; border-radius:10px; border-left:5px solid {p_color};
            padding:0.8rem 1.5rem; margin:1rem 0 0.3rem;">
    <h4 style="color:{p_color}; margin:0;">{p_icon} {phase_name} Phase</h4>
</div>
                        """, unsafe_allow_html=True)

                        steps = safe_list(phase.get("steps", []))
                        for step in steps:
                            if not isinstance(step, dict):
                                continue

                            step_num    = safe_str(step.get("step", ""))
                            action      = safe_str(step.get("action", ""))
                            expected    = safe_str(step.get("expected_output", "N/A"))
                            time_est    = safe_str(step.get("time_estimate", "N/A"))
                            command     = safe_str(step.get("command", ""))

                            col1, col2 = st.columns([4, 1])
                            with col1:
                                st.markdown(f"""
<div style="background:#141414; border-radius:8px; padding:12px 16px;
            margin:5px 0; border:1px solid #2a2a2a;">
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
        <span style="background:{p_color}; color:black; font-weight:bold;
                     font-size:0.75rem; width:24px; height:24px; border-radius:50%;
                     display:flex; align-items:center; justify-content:center;
                     flex-shrink:0;">
            {step_num}
        </span>
        <span style="color:white; font-weight:500; font-size:0.95rem;
                     line-height:1.4;">
            {action}
        </span>
    </div>
    <p style="color:#888; font-size:0.8rem; margin:0 0 0 34px; line-height:1.4;">
        ✓ Expected: {expected}
    </p>
</div>
                                """, unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"""
<div style="background:#141414; border-radius:8px; padding:12px;
            margin:5px 0; text-align:center; border:1px solid #2a2a2a;">
    <p style="color:#888; font-size:0.68rem; margin:0 0 4px;">ETA</p>
    <p style="color:{p_color}; font-weight:bold; font-size:0.82rem; margin:0;">
        {time_est}
    </p>
</div>
                                """, unsafe_allow_html=True)

                            if command and command != "N/A":
                                st.code(command, language="bash")

                st.markdown("<br/>", unsafe_allow_html=True)

                # Escalation
                if escalation:
                    st.markdown("#### 🚨 Escalation Path")
                    icons = ["👤", "👥", "🏢", "🔱"]
                    cols  = st.columns(len(escalation))
                    for i, (col, level) in enumerate(zip(cols, escalation)):
                        with col:
                            st.markdown(f"""
<div style="background:#1E1E1E; border-radius:8px; padding:1rem;
            text-align:center; border:1px solid #333;">
    <p style="font-size:1.2rem; margin:0 0 6px;">
        {icons[i] if i < len(icons) else "👤"}
    </p>
    <p style="color:#888; font-size:0.7rem; margin:0 0 4px;">Level {i+1}</p>
    <p style="color:white; font-size:0.85rem; margin:0; line-height:1.4;">
        {safe_str(level)}
    </p>
</div>
                            """, unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)

                # Metrics
                if metrics:
                    st.markdown("#### 📊 Key Metrics to Monitor")
                    cols = st.columns(2)
                    for i, metric in enumerate(metrics):
                        with cols[i % 2]:
                            st.markdown(f"""
<div style="background:#12121f; border-radius:8px; padding:10px 14px;
            margin:4px 0; border:1px solid #2a2a4a;
            display:flex; align-items:center; gap:10px;">
    <span style="color:#7C4DFF; flex-shrink:0;">📈</span>
    <span style="color:#ddd; font-size:0.9rem;">{safe_str(metric)}</span>
</div>
                            """, unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)

                # Prevention
                if prevention:
                    st.markdown("#### 🛡️ Prevention Measures")
                    for measure in prevention:
                        st.markdown(f"""
<div style="background:#0d1f0d; border-radius:8px; padding:10px 14px;
            margin:4px 0; border:1px solid #1a3a1a;
            display:flex; align-items:center; gap:10px;">
    <span style="color:#00C853; flex-shrink:0;">✓</span>
    <span style="color:#ddd; font-size:0.9rem; line-height:1.5;">
        {safe_str(measure)}
    </span>
</div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br/>", unsafe_allow_html=True)

                # Lessons learned — always plain text
                st.markdown(f"""
<div style="background:#1a1200; border-left:5px solid #FFD600;
            border-radius:8px; padding:1rem 1.5rem; margin-top:1rem;">
    <p style="color:#FFD600; font-size:0.75rem; margin:0 0 8px;
               text-transform:uppercase; letter-spacing:1px;">
        💡 Lessons Learned
    </p>
    <p style="color:#ddd; margin:0; font-size:0.95rem; line-height:1.7;">
        {lessons}
    </p>
</div>
                """, unsafe_allow_html=True)

            # ── AGENT 5 ──────────────────────────────────────────────────────
            with st.expander("🎫 Agent 5 — JIRA Tickets", expanded=True):
                jira_status = jira.get("status", "unknown")
                if jira_status == "success":
                    st.success(f"✅ {jira.get('total_created')} JIRA tickets created!")
                elif jira_status == "mocked":
                    st.info(f"🔄 Mock mode — {jira.get('total_created')} tickets would be created")
                else:
                    st.error(f"❌ Error: {safe_str(jira.get('error'))}")

                tickets = safe_list(jira.get("tickets", []))
                for ticket in tickets:
                    if not isinstance(ticket, dict):
                        continue
                    sev   = ticket.get("severity", "LOW")
                    color = sev_color(sev)
                    st.markdown(f"""
<div style="background:#1E1E1E; border-left:5px solid {color};
            border-radius:8px; padding:1rem 1.5rem; margin:0.5rem 0;">
    <div style="display:flex; justify-content:space-between; align-items:center;
                margin-bottom:8px;">
        <span style="color:{color}; font-weight:bold; font-size:0.9rem;">
            🎫 {safe_str(ticket.get('ticket_id'))}
        </span>
        <span style="background:{color}22; color:{color}; font-size:0.75rem;
                     padding:2px 10px; border-radius:20px; font-weight:bold;">
            {sev}
        </span>
    </div>
    <h4 style="color:white; margin:0 0 8px;">{safe_str(ticket.get('title'))}</h4>
    <p style="color:#aaa; font-size:0.85rem; margin:0 0 6px; line-height:1.5;">
        {safe_str(ticket.get('description'))}
    </p>
    <p style="color:#00C853; font-size:0.85rem; margin:0;">
        ⚡ <strong>Action:</strong> {safe_str(ticket.get('immediate_action'))}
    </p>
</div>
                    """, unsafe_allow_html=True)
                    if ticket.get("url") and jira_status == "success":
                        st.markdown(f"[🔗 View in JIRA]({ticket.get('url')})")

            # ── EXPORT ───────────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("## 📥 Export Results")
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "⬇️ Download Full Report (JSON)",
                    data=json.dumps(result, indent=2),
                    file_name="incident_report.json",
                    mime="application/json"
                )
            with col2:
                st.download_button(
                    "⬇️ Download Cookbook (JSON)",
                    data=json.dumps(cookbook, indent=2),
                    file_name="incident_cookbook.json",
                    mime="application/json"
                )

        except Exception as e:
            progress_bar.progress(0)
            st.error(f"❌ Pipeline failed: {str(e)}")
            st.exception(e)

else:
    st.info("👆 Upload a log file or paste logs above to get started")
    st.markdown("### Sample log format:")
    st.code("""
2024-01-15 08:23:11 ERROR [payment-service] Database connection timeout
2024-01-15 08:23:12 CRITICAL [payment-service] Failed to process payment
2024-01-15 08:23:15 ERROR [api-gateway] Upstream service returning 503
    """, language="bash")
