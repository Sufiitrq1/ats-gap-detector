"""
Renders the gap analysis into an HTML email and sends it via Resend.
"""
import os
import resend

resend.api_key = os.environ["RESEND_API_KEY"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "onboarding@resend.dev")


def _skill_list_html(items, key_name, label_field, color):
    if not items:
        return f"<p style='color:#888;font-size:14px;'>None</p>"
    rows = ""
    for item in items:
        extra = item.get(label_field, "")
        rows += f"""
        <div style="border-left:3px solid {color};padding:8px 14px;margin-bottom:8px;background:#fafafa;">
          <strong style="font-size:14px;">{item.get('skill','')}</strong>
          <div style="font-size:13px;color:#555;margin-top:2px;">{extra}</div>
        </div>"""
    return rows


def render_email_html(role_title: str, seniority: str, gap_report: dict) -> str:
    score = gap_report.get("match_score", 0)
    summary = gap_report.get("summary", "")

    have_html = _skill_list_html(gap_report.get("have", []), "have", "evidence", "#22c55e")
    weak_html = _skill_list_html(gap_report.get("weak", []), "weak", "fix", "#eab308")
    missing_html = _skill_list_html(gap_report.get("missing", []), "missing", "how_to_close_gap", "#ef4444")

    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:600px;margin:0 auto;color:#111;">
      <h2 style="margin-bottom:4px;">ATS Gap Report: {role_title}</h2>
      <p style="color:#666;margin-top:0;">Seniority: {seniority}</p>

      <div style="background:#111;color:#fff;padding:16px 20px;border-radius:8px;margin:16px 0;">
        <div style="font-size:32px;font-weight:700;">{score}/100</div>
        <div style="font-size:14px;opacity:0.85;">Match score</div>
      </div>

      <p style="font-size:15px;line-height:1.5;">{summary}</p>

      <h3 style="color:#22c55e;margin-top:28px;">✅ You've got this covered</h3>
      {have_html}

      <h3 style="color:#eab308;margin-top:28px;">⚠️ On your resume, but weak</h3>
      {weak_html}

      <h3 style="color:#ef4444;margin-top:28px;">❌ Missing — here's what to do</h3>
      {missing_html}

      <p style="margin-top:32px;font-size:12px;color:#999;">Generated automatically — treat as a starting point, not gospel.</p>
    </div>
    """


def send_report_email(to_email: str, role_title: str, seniority: str, gap_report: dict) -> str:
    html = render_email_html(role_title, seniority, gap_report)
    params = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": f"Your ATS Gap Report: {role_title} ({gap_report.get('match_score', 0)}% match)",
        "html": html,
    }
    result = resend.Emails.send(params)
    return result.get("id", "")
