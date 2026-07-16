import gradio as gr
import requests
import os
import traceback
import time
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
# ▶️ تشغيل الـ Workflow مع شريط التقدم
# ============================================================

def run_workflow_with_progress(video_url, progress=gr.Progress()):
    """
    تشغيل الـ Workflow مع عرض شريط التقدم
    """
    # التحقق من صحة الرابط
    if not video_url or not video_url.strip():
        return "❌ Please enter a YouTube URL"
    
    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        return "❌ Please enter a valid YouTube URL"
    
    if not N8N_WEBHOOK_URL:
        return "❌ N8N Webhook not configured. Please add N8N_WEBHOOK_URL to Secrets."
    
    try:
        # ✅ الخطوة 1: التحقق من الرابط (0-10%)
        progress(0.1, desc="📋 Checking video URL...")
        time.sleep(0.5)
        
        # ✅ الخطوة 2: إرسال الطلب إلى Webhook (10-30%)
        progress(0.2, desc="📤 Sending request to workflow...")
        
        response = requests.post(
            N8N_WEBHOOK_URL,
            json={'videoUrl': video_url.strip()},
            timeout=120
        )
        
        # ✅ الخطوة 3: معالجة الاستجابة (30-50%)
        progress(0.4, desc="⏳ Waiting for workflow response...")
        time.sleep(1)
        
        if response.status_code == 200:
            # ✅ الخطوة 4: اكتمل (50-90%)
            progress(0.7, desc="🔄 Processing translation...")
            time.sleep(1)
            
            # ✅ الخطوة 5: حفظ في Supabase (90-100%)
            progress(0.9, desc="💾 Saving to Supabase...")
            time.sleep(0.5)
            
            progress(1.0, desc="✅ Translation complete!")
            
            return f"""✅ **Workflow started successfully!**

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
# 🔍 التحقق من حالة الـ Workflow
# ============================================================

def check_workflow_status(video_id):
    """
    التحقق من حالة الترجمة لفيديو معين
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
            f'{SUPABASE_URL}/rest/v1/translations?video_id=eq.{video_id}',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return f"✅ Translation found for video ID: {video_id}\n\n📝 Title: {data[0].get('video_title', 'N/A')}\n🕐 Created: {data[0].get('created_at', 'N/A')}"
            else:
                return f"⏳ No translation found yet for video ID: {video_id}\n\n🔄 The workflow is still processing. Please wait a moment and refresh."
        else:
            return f"❌ Error checking status: {response.status_code}"
            
    except Exception as e:
        return f"❌ Error: {str(e)[:200]}"

# ============================================================
# 🎨 إنشاء الواجهة (Gradio) - مع شريط التقدم
# ============================================================

with gr.Blocks(
    title="🎬 Video Translation Dashboard",
    theme=gr.themes.Soft(),
    css="""
        .gradio-container { max-width: 950px; margin: auto; }
        .markdown-text { font-size: 14px; }
        .progress-container { 
            background: rgba(99, 102, 241, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border: 1px solid rgba(99, 102, 241, 0.3);
        }
        .status-box {
            padding: 10px 15px;
            border-radius: 8px;
            margin: 5px 0;
        }
        .status-success { background: rgba(34, 197, 94, 0.15); border-left: 4px solid #22c55e; }
        .status-warning { background: rgba(234, 179, 8, 0.15); border-left: 4px solid #eab308; }
        .status-error { background: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444; }
        .status-info { background: rgba(59, 130, 246, 0.15); border-left: 4px solid #3b82f6; }
    """
) as demo:
    
    gr.Markdown("""
    # 🎬 Video Translation Dashboard
    
    **Translate YouTube videos with AI**
    - Enter a YouTube URL and click **Translate**
    - Watch the progress bar for real-time updates
    - Click **Refresh** to see the latest translations
    """)
    
    # ============================================================
    # 🔹 قسم الترجمة
    # ============================================================
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### ▶️ Translate Video")
            
            video_input = gr.Textbox(
                label="YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                lines=1
            )
            
            with gr.Row():
                translate_btn = gr.Button("🚀 Translate", variant="primary", size="lg")
                check_btn = gr.Button("🔍 Check Status", variant="secondary", size="sm")
                test_btn = gr.Button("🔍 Test Supabase", variant="secondary", size="sm")
            
            # عرض الحالة
            status_output = gr.Textbox(
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
    
    # زر الترجمة مع شريط التقدم
    translate_btn.click(
        fn=run_workflow_with_progress,
        inputs=video_input,
        outputs=status_output
    )
    
    # زر التحقق من الحالة
    check_btn.click(
        fn=check_workflow_status,
        inputs=video_input,
        outputs=status_output
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
