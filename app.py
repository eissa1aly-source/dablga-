import gradio as gr
import requests
import os

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

def fetch_translations():
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return "❌ Supabase credentials not configured"
    try:
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/translations?order=created_at.desc&limit=10',
            headers=headers, timeout=10
        )
        if response.status_code != 200:
            return f"❌ Error: {response.status_code}"
        data = response.json()
        if not data:
            return "📭 No translations found"
        result = "## 📝 Latest Translations\n\n"
        for item in data:
            title = item.get('video_title', 'No title')[:50]
            created = item.get('created_at', '')[:16]
            result += f"**{title}**\n🕐 {created}\n\n---\n\n"
        return result
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

def run_workflow(video_url):
    if not N8N_WEBHOOK_URL:
        return "❌ Webhook not configured"
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'videoUrl': video_url or ''},
            timeout=60
        )
        if response.status_code == 200:
            return f"✅ Workflow started!\n📹 {video_url or 'Default'}"
        return f"❌ Error: {response.status_code}"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

with gr.Blocks(title="N8N Automation", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# ⚙️ N8N Automation Dashboard")
    with gr.Row():
        with gr.Column(scale=2):
            video_input = gr.Textbox(label="YouTube URL", placeholder="https://www.youtube.com/watch?v=...")
            run_btn = gr.Button("🚀 Run", variant="primary")
            run_output = gr.Textbox(label="Result", lines=5)
    with gr.Row():
        refresh_btn = gr.Button("🔄 Refresh")
        status_output = gr.Markdown("Click Refresh to load data")
    run_btn.click(fn=run_workflow, inputs=video_input, outputs=run_output)
    refresh_btn.click(fn=fetch_translations, outputs=status_output)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
