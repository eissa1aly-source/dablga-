import gradio as gr
import requests
import os
import traceback
import base64
import json

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
# 📤 تشغيل الـ Workflow مع فيديو محلي
# ============================================================

def process_local_video(video_file, target_language):
    """
    معالجة فيديو محلي وإرساله إلى n8n Webhook
    """
    if video_file is None:
        return "❌ Please upload a video file first"
    
    if not N8N_WEBHOOK_URL:
        return "❌ N8N Webhook not configured. Please add N8N_WEBHOOK_URL to Secrets."
    
    try:
        # قراءة الفيديو وتحويله إلى base64
        with open(video_file.name, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode('utf-8')
        
        # إرسال الطلب إلى Webhook
        payload = {
            'videoData': video_data,
            'filename': os.path.basename(video_file.name),
            'targetLanguage': target_language,
            'sourceType': 'local'
        }
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 200:
            return f"✅ Video sent to workflow!\n\n📹 File: {os.path.basename(video_file.name)}\n🌍 Target language: {target_language}\n\n⏳ The translation will be processed shortly."
        else:
            return f"❌ Error: {response.status_code}\n\n{response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Request timeout - the workflow took too long to respond"
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error - cannot reach the webhook"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}\n\n{traceback.format_exc()[:200]}"

# ============================================================
# ▶️ تشغيل الـ Workflow مع رابط يوتيوب
# ============================================================

def run_youtube_workflow(video_url):
    """
    تشغيل الـ Workflow عن طريق إرسال طلب إلى Webhook n8n (رابط يوتيوب)
    """
    if not video_url or not video_url.strip():
        return "❌ Please enter a YouTube URL"
    
    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        return "❌ Please enter a valid YouTube URL"
    
    if not N8N_WEBHOOK_URL:
        return "❌ N8N Webhook not configured. Please add N8N_WEBHOOK_URL to Secrets."
    
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'videoUrl': video_url.strip(), 'sourceType': 'youtube'},
            timeout=120
        )
        
        if response.status_code == 200:
            return f"✅ YouTube workflow started successfully!\n\n📹 Video: {video_url}\n\n⏳ The translation will be saved to Supabase shortly."
        elif response.status_code == 500:
            return "❌ Server error. The video might be unavailable or private. Please try another video."
        else:
            return f"❌ Error: {response.status_code}\n\n{response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Request timeout - the workflow took too long to respond"
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error - cannot reach the webhook"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

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
# 🎨 إنشاء الواجهة (Gradio) - تدعم الفيديو المحلي
# ============================================================

with gr.Blocks(
    title="🎬 Video Translation Dashboard",
    theme=gr.themes.Soft(),
    css="""
        .gradio-container { max-width: 950px; margin: auto; }
        .markdown-text { font-size: 14px; }
        .video-upload { border: 2px dashed #6366f1; border-radius: 10px; padding: 20px; }
    """
) as demo:
    
    gr.Markdown("""
    # 🎬 Video Translation Dashboard
    
    **Translate videos from YouTube or your device**
    - Upload a video from your device, or
    - Enter a YouTube URL
    - Click **Translate** to start the translation
    """)
    
    # ============================================================
    # 🔹 قسم الفيديو المحلي
    # ============================================================
    
    with gr.Tab("📱 Local Video"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Video")
                video_input = gr.File(
                    label="Choose a video file",
                    file_types=[".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"],
                    elem_classes="video-upload"
                )
                
                lang_input = gr.Dropdown(
                    choices=[
                        ("Arabic", "ar"),
                        ("English", "en"),
                        ("Spanish", "es"),
                        ("French", "fr"),
                        ("German", "de"),
                        ("Chinese", "zh"),
                        ("Japanese", "ja"),
                        ("Korean", "ko"),
                        ("Russian", "ru"),
                        ("Italian", "it"),
                        ("Portuguese", "pt"),
                        ("Hindi", "hi")
                    ],
                    label="Target Language",
                    value="ar"
                )
                
                with gr.Row():
                    translate_local_btn = gr.Button("🚀 Translate Video", variant="primary", size="lg")
                
                local_output = gr.Textbox(label="Result", lines=6, interactive=False)
    
    # ============================================================
    # 🔹 قسم يوتيوب
    # ============================================================
    
    with gr.Tab("▶️ YouTube"):
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### 📹 YouTube Video")
                youtube_input = gr.Textbox(
                    label="YouTube URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    lines=1
                )
                
                with gr.Row():
                    translate_youtube_btn = gr.Button("🚀 Translate YouTube", variant="primary")
                    test_btn = gr.Button("🔍 Test Supabase", variant="secondary", size="sm")
                
                youtube_output = gr.Textbox(label="Result", lines=6, interactive=False)
                test_output = gr.Textbox(label="Supabase Test", lines=2, interactive=False)
    
    # ============================================================
    # 🔹 عرض الترجمات
    # ============================================================
    
    with gr.Tab("📝 Translations"):
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 📝 Latest Translations")
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                status_output = gr.Markdown("Click **Refresh** to load data", elem_classes="markdown-text")
    
    # ============================================================
    # 🔗 ربط الأزرار
    # ============================================================
    
    # زر ترجمة الفيديو المحلي
    translate_local_btn.click(
        fn=process_local_video,
        inputs=[video_input, lang_input],
        outputs=local_output
    )
    
    # زر ترجمة يوتيوب
    translate_youtube_btn.click(
        fn=run_youtube_workflow,
        inputs=youtube_input,
        outputs=youtube_output
    )
    
    # زر اختبار Supabase
    test_btn.click(
        fn=test_supabase,
        outputs=test_output
    )
    
    # زر تحديث الترجمات
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
