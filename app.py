import gradio as gr
import requests
import os
import traceback

# ============================================================
# 🔐 جلب المفاتيح من متغيرات البيئة (Secrets)
# ============================================================

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
N8N_WEBHOOK_URL = os.environ.get('N8N_WEBHOOK_URL')

# ============================================================
# 📥 جلب الترجمات من Supabase
# ============================================================

def fetch_translations():
    """
    جلب آخر 10 ترجمات من Supabase وعرضها في الواجهة
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return "❌ Supabase credentials not configured. Please add SUPABASE_URL and SUPABASE_ANON_KEY to Secrets."
    
    try:
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/translations?order=created_at.desc&limit=10',
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            return f"❌ Supabase error: {response.status_code} - {response.text[:100]}"
        
        data = response.json()
        
        if not data:
            return "📭 No translations found yet. Run the workflow to create one."
        
        # تنسيق النتائج
        result = "## 📝 Latest Translations\n\n"
        for item in data:
            title = item.get('video_title', 'No title')[:50]
            created = item.get('created_at', '')[:16]
            video_id = item.get('video_id', '')
            
            result += f"**{title}**\n"
            result += f"🕐 {created}\n"
            if video_id:
                result += f"🔗 [Watch](https://www.youtube.com/watch?v={video_id})\n"
            result += "\n---\n\n"
        
        return result
        
    except requests.exceptions.Timeout:
        return "⏱️ Connection timeout - please try again"
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error - please check your internet"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

# ============================================================
# ▶️ تشغيل الـ Workflow عبر Webhook
# ============================================================

def run_workflow(video_url):
    """
    تشغيل الـ Workflow عن طريق إرسال طلب إلى Webhook n8n
    """
    # التحقق من صحة الرابط
    if not video_url or not video_url.strip():
        return "❌ Please enter a YouTube URL"
    
    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        return "❌ Please enter a valid YouTube URL"
    
    if not N8N_WEBHOOK_URL:
        return "❌ N8N Webhook not configured. Please add N8N_WEBHOOK_URL to Secrets."
    
    try:
        # إرسال الطلب إلى Webhook
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'videoUrl': video_url.strip()},
            timeout=120  # زيادة المهلة إلى 120 ثانية
        )
        
        if response.status_code == 200:
            return f"✅ Workflow started successfully!\n\n📹 Video: {video_url}\n\n⏳ The translation will be saved to Supabase shortly."
        elif response.status_code == 404:
            return "❌ Webhook not found. Please check your N8N Webhook URL."
        elif response.status_code == 500:
            return "❌ Server error. The video might be unavailable or private. Please try another video."
        else:
            return f"❌ Error: {response.status_code}\n\n{response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Request timeout - the workflow took too long to respond"
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error - cannot reach the webhook"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}\n\n{traceback.format_exc()[:200]}"

# ============================================================
# 📋 اختبار الاتصال بـ Supabase
# ============================================================

def test_supabase():
    """
    اختبار الاتصال بـ Supabase
    """
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return "❌ Supabase credentials not configured"
    
    try:
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
            'Content-Type': 'application/json'
        }
        response = requests.get(
            f'{SUPABASE_URL}/rest/v1/translations?limit=1',
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            return "✅ Supabase connection successful!"
        else:
            return f"❌ Supabase error: {response.status_code}"
            
    except Exception as e:
        return f"❌ Connection error: {str(e)[:100]}"

# ============================================================
# 🎨 إنشاء الواجهة (Gradio)
# ============================================================

with gr.Blocks(
    title="N8N Automation Dashboard",
    theme=gr.themes.Soft(),
    css="""
        .gradio-container { max-width: 900px; margin: auto; }
        .markdown-text { font-size: 14px; }
    """
) as demo:
    
    gr.Markdown("""
    # ⚙️ N8N Automation Dashboard
    
    **Control your video translation workflow**
    - Enter a YouTube URL and click **Run** to start the translation
    - Click **Refresh** to see the latest translations from Supabase
    """)
    
    # صف العلوي: تشغيل الـ Workflow
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### ▶️ Run Workflow")
            video_input = gr.Textbox(
                label="YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                lines=1
            )
            with gr.Row():
                run_btn = gr.Button("🚀 Run", variant="primary")
                test_btn = gr.Button("🔍 Test Supabase", variant="secondary", size="sm")
            
            run_output = gr.Textbox(label="Result", lines=6, interactive=False)
            test_output = gr.Textbox(label="Supabase Test", lines=2, interactive=False)
    
    # صف سفلي: عرض الترجمات
    with gr.Row():
        with gr.Column(scale=3):
            gr.Markdown("### 📝 Latest Translations")
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
            status_output = gr.Markdown("Click **Refresh** to load data", elem_classes="markdown-text")
    
    # ربط الأزرار
    run_btn.click(
        fn=run_workflow,
        inputs=video_input,
        outputs=run_output
    )
    
    test_btn.click(
        fn=test_supabase,
        outputs=test_output
    )
    
    refresh_btn.click(
        fn=fetch_translations,
        outputs=status_output
    )
    
    # تحميل البيانات تلقائياً عند فتح الصفحة
    demo.load(
        fn=fetch_translations,
        outputs=status_output
    )

# ============================================================
# ▶️ تشغيل التطبيق
# ============================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False
    )
