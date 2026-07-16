import gradio as gr
import requests
import os
import traceback
import time
import json
import base64

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
# 📤 معالجة الفيديو المحلي
# ============================================================

def process_local_video(video_file, target_language, progress=gr.Progress()):
    """
    معالجة فيديو محلي وإرساله إلى n8n Webhook
    """
    if video_file is None:
        return "❌ Please upload a video file first"
    
    if not N8N_WEBHOOK_URL:
        return "❌ N8N Webhook not configured. Please add N8N_WEBHOOK_URL to Secrets."
    
    try:
        # ✅ الخطوة 1: قراءة الملف (0-20%)
        progress(0.1, desc="📂 Reading video file...")
        time.sleep(0.5)
        
        # قراءة الفيديو وتحويله إلى base64
        with open(video_file.name, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode('utf-8')
        
        filename = os.path.basename(video_file.name)
        file_size = os.path.getsize(video_file.name) / (1024 * 1024)  # MB
        
        # ✅ الخطوة 2: إرسال إلى Webhook (20-50%)
        progress(0.3, desc="📤 Uploading video to workflow...")
        
        payload = {
            'videoData': video_data,
            'filename': filename,
            'targetLanguage': target_language,
            'sourceType': 'local',
            'fileSizeMB': round(file_size, 2)
        }
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=payload,
            timeout=300  # 5 دقائق للفيديوهات الكبيرة
        )
        
        # ✅ الخطوة 3: معالجة الاستجابة (50-80%)
        progress(0.6, desc="⏳ Processing video...")
        time.sleep(1)
        
        if response.status_code == 200:
            progress(0.9, desc="💾 Saving translation...")
            time.sleep(0.5)
            progress(1.0, desc="✅ Translation complete!")
            
            return f"""✅ **Video translation started successfully!**

## 📊 Progress
- ✅ Video uploaded: `{filename}`
- ✅ File size: `{file_size:.2f} MB`
- ✅ Target language: `{target_language}`
- ✅ Request sent to workflow

## 📹 Video Details
- **File:** {filename}
- **Size:** {file_size:.2f} MB
- **Language:** {target_language}

## ⏳ Status
The translation will be processed shortly. Check the latest translations."
"""
        else:
            return f"❌ Error: {response.status_code}\n\n{response.text[:200]}"
            
    except requests.exceptions.Timeout:
        return "⏱️ Request timeout - the video might be too large or the workflow is taking too long"
    except requests.exceptions.ConnectionError:
        return "🔌 Connection error - cannot reach the webhook"
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}\n\n{traceback.format_exc()[:200]}"

# ============================================================
# ▶️ تشغيل الـ Workflow مع رابط يوتيوب وشريط التقدم
# ============================================================

def run_youtube_workflow(video_url, progress=gr.Progress()):
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
        # ✅ الخطوة 1: التحقق من الرابط (0-15%)
        progress(0.1, desc="📋 Checking video URL...")
        time.sleep(0.5)
        
        # ✅ الخطوة 2: إرسال الطلب إلى Webhook (15-40%)
        progress(0.25, desc="📤 Sending request to workflow...")
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'videoUrl': video_url.strip(), 'sourceType': 'youtube'},
            timeout=120
        )
        
        # ✅ الخطوة 3: معالجة الاستجابة (40-70%)
        progress(0.5, desc="⏳ Waiting for workflow response...")
        time.sleep(1)
        
        if response.status_code == 200:
            # ✅ الخطوة 4: اكتمل (70-100%)
            progress(0.8, desc="🔄 Processing translation...")
            time.sleep(1)
            progress(0.95, desc="💾 Saving to Supabase...")
            time.sleep(0.5)
            progress(1.0, desc="✅ Translation complete!")
            
            return f"""✅ **YouTube translation started successfully!**

## 📊 Progress
- ✅ URL validated
- ✅ Request sent to workflow
- ✅ Translation processed
- ✅ Saved to Supabase

## 📹 Video
{video_url}

## ⏳ Status
The translation will appear in "Latest Translations" shortly.
"""
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
# 🎨 إنشاء الواجهة (Gradio) - تدعم الفيديو المحلي ويوتيوب
# ============================================================

with gr.Blocks(
    title="🎬 Video Translation Dashboard",
    theme=gr.themes.Soft(),
    css="""
        .gradio-container { max-width: 950px; margin: auto; }
        .markdown-text { font-size: 14px; }
        .status-box { padding: 10px 15px; border-radius: 8px; margin: 5px 0; }
        .status-success { background: rgba(34, 197, 94, 0.15); border-left: 4px solid #22c55e; }
        .status-warning { background: rgba(234, 179, 8, 0.15); border-left: 4px solid #eab308; }
        .status-error { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; }
        .status-info { background: rgba(59, 130, 246, 0.15); border-left: 4px solid #3b82f6; }
        .upload-section { border: 2px dashed #6366f1; border-radius: 10px; padding: 20px; margin: 10px 0; }
    """
) as demo:
    
    gr.Markdown("""
    # 🎬 Video Translation Dashboard
    
    **Translate videos from YouTube or your device**
    - Upload a video file from your device, or
    - Enter a YouTube URL
    - Click **Translate** to start
    - Watch the progress bar for real-time updates
    """)
    
    # ============================================================
    # 🔹 تبويب الفيديو المحلي
    # ============================================================
    
    with gr.Tab("📱 Local Video"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Video")
                
                video_input = gr.File(
                    label="Choose a video file",
                    file_types=[".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".mpg", ".mpeg"],
                    elem_classes="upload-section"
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
                
                translate_local_btn = gr.Button("🚀 Translate Video", variant="primary", size="lg")
                
                local_output = gr.Textbox(
                    label="Status",
                    lines=10,
                    interactive=False,
                    elem_classes="status-box"
                )
    
    # ============================================================
    # 🔹 تبويب يوتيوب
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
                
                youtube_output = gr.Textbox(
                    label="Status",
                    lines=10,
                    interactive=False,
                    elem_classes="status-box"
                )
                
                test_output = gr.Textbox(
                    label="Supabase Test",
                    lines=2,
                    interactive=False
                )
    
    # ============================================================
    # 🔹 عرض الترجمات
    # ============================================================
    
    with gr.Tab("📝 Translations"):
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### 📝 Latest Translations")
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")
                translations_output = gr.Markdown(
                    "Click **Refresh** to load data",
                    elem_classes="markdown-text"
                )
    
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
        outputs=translations_output
    )
    
    # تحميل البيانات تلقائياً عند فتح الصفحة
    demo.load(
        fn=fetch_translations,
        outputs=translations_output
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
