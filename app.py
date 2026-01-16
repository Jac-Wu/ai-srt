import streamlit as st
import os
import shutil
import tempfile
import time
from autosub_mac.transcriber import WhisperTranscriber
from autosub_mac.audio import extract_audio, split_audio
from autosub_mac.translator import SubtitleTranslator
from autosub_mac.utils import write_srt
import traceback

st.set_page_config(
    page_title="Auto-Subtitle Generator (Mac/Whisper)",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 自动字幕生成器 (Auto-Subtitle Mac)")
st.markdown("专为 macOS M-Series 芯片优化的本地化视频字幕工具。")

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ 参数配置")
    
    model_size = st.selectbox(
        "Whisper 模型大小",
        options=["tiny", "base", "small", "medium", "large"],
        index=1,
        help="越大越准，但速度越慢。"
    )
    
    target_lang = st.text_input(
        "目标语言 (Target Language)",
        value="zh-CN",
        help="例如: zh-CN (简体中文), en (英语), es (西班牙语)。留空则不翻译。"
    )
    
    trans_provider = st.selectbox(
        "翻译服务商 (Translation Provider)",
        options=["google", "deepl"],
        index=0
    )
    
    api_key = ""
    if trans_provider == "deepl":
        api_key = st.text_input("DeepL API Key", type="password", help="请输入你的 DeepL API Key")
    
    st.divider()
    
    st.subheader("⚡️ 性能优化")
    segment_duration = st.slider(
        "分段时长 (秒)",
        min_value=0,
        max_value=1200,
        value=300,
        step=60,
        help="0 表示不分段。分段处理可以减少长视频的内存压力。"
    )
    
    # CoreML/Metal has crash issues with multi-threading.
    # We disable this option for now to ensure stability.
    st.info("ℹ️ 多线程已禁用 (CoreML 稳定性优化)")
    threads = st.number_input(
        "并行线程数",
        min_value=1,
        max_value=1,
        value=1,
        disabled=True,
        help="因 CoreML 后端稳定性原因，暂时禁用多线程并行。但不用担心，Mac 本身的 GPU 加速已经非常快了！"
    )
    
    st.divider()
    if st.button("🗑️ 清除模型缓存 (修复启动失败)"):
        cache_dir = os.path.expanduser("~/Library/Application Support/pywhispercpp/models")
        if os.path.exists(cache_dir):
            try:
                shutil.rmtree(cache_dir)
                st.success(f"已清理缓存: {cache_dir}。请重新运行任务，程序将自动重新下载/编译模型。")
            except Exception as e:
                st.error(f"清理失败: {e}")
        else:
            st.warning("缓存目录不存在，无需清理。")

# --- Main Interface ---
st.info("💡 请上传视频文件，或输入本地文件绝对路径。")

tab1, tab2 = st.tabs(["📂 文件上传", "📍 本地路径"])

filepath = None
upload_mode = False

with tab1:
    uploaded_file = st.file_uploader("拖拽视频文件到此处", type=["mp4", "mov", "mkv", "avi"])
    if uploaded_file:
        upload_mode = True

with tab2:
    local_path = st.text_input("输入本地视频绝对路径", placeholder="/Users/yourname/Movies/video.mp4")
    if local_path and os.path.exists(local_path):
        filepath = local_path
    elif local_path:
        st.error("❌ 文件不存在")

# --- Processing Logic ---
# --- Processing Logic ---
if st.button("🚀 开始生成字幕 (Start Processing)", type="primary"):
    if not upload_mode and not filepath:
        st.warning("⚠️ 请先提供视频文件。")
        st.stop()
        
    status_container = st.status("正在处理...", expanded=True)
    log_area = status_container.empty()
    
    def log(msg):
        log_area.code(msg, language="text")
        # print(msg) 

    import subprocess
    import sys

    try:
        # Prepare working file
        work_dir = tempfile.mkdtemp()
        
        if upload_mode:
            video_name = uploaded_file.name
            video_path = os.path.join(work_dir, video_name)
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            log(f"📥 已保存上传文件: {video_path}")
        else:
            video_name = os.path.basename(filepath)
            video_path = filepath
            
        base_name = os.path.splitext(video_name)[0]
        
        # Build Command
        # python3 -m autosub_mac.main video_path --model X --lang Y --segment-duration Z
        cmd = [
            sys.executable, "-m", "autosub_mac.main",
            video_path,
            "--model", model_size,
            "--segment-duration", str(segment_duration),
            # Threads are hardcoded to 1 to avoid internal crashes, but we pass the arg anyway if we re-enable it later
            "--threads", str(threads),
            "--output", os.path.join(work_dir, f"{base_name}.srt")
        ]
        
        if target_lang:
            cmd.extend(["--lang", target_lang])
            cmd.extend(["--provider", trans_provider])
            if api_key:
                cmd.extend(["--api-key", api_key])
        else:
            cmd.append("--no-translate")
            
        log(f"Running command: {' '.join(cmd)}")
        
        # Run Subprocess
        status_container.write("⚙️ 执行后台任务...")
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=os.getcwd()
        )
        
        # Read output real-time
        logs = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                logs.append(line)
                # Keep only last 10 lines for cleanliness, or accumulate all? 
                # Let's show last few lines to avoid UI lag
                log_text = "\n".join(logs[-15:])
                log(log_text)
                
        return_code = process.poll()
        
        if return_code == 0:
            status_container.update(label="✅ 处理已完成!", state="complete", expanded=False)
            st.success(f"🎉 字幕生成成功!")
            
            # Find generated file
            # We forced output path in cmd
            output_srt_path = os.path.join(work_dir, f"{base_name}.srt")
            
            if os.path.exists(output_srt_path):
                with open(output_srt_path, "r", encoding='utf-8') as f:
                    srt_content = f.read()
                
                st.download_button(
                    label="📥 下载 SRT 字幕文件",
                    data=srt_content,
                    file_name=f"{base_name}.srt",
                    mime="text/plain"
                )
                
                st.subheader("📝 字幕预览 (Preview)")
                st.text_area("Content", value=srt_content, height=300)
            else:
                st.error("❌ 未找到生成的字幕文件。")
        else:
            status_container.update(label="❌ 处理失败", state="error")
            st.error("任务执行失败，请检查上方日志。")
        
        # Cleanup temp dir? 
        # shutil.rmtree(work_dir)
        
    except Exception as e:
        status_container.update(label="❌ 系统错误", state="error")
        st.error(f"发生错误: {str(e)}")
        st.code(traceback.format_exc())
