# Auto-Subtitle Generator for macOS (Apple Silicon)

一个基于 `whisper.cpp` 和 Python 的自动视频字幕生成工具，专为 macOS M 系列芯片 (M1/M2/M3) 优化。支持硬件加速转录和多语言翻译。

## ✨ 特性

- 🚀 **Mac 硬件加速**: 利用 Metal/CoreML 跑 Whisper 模型，速度极快。
- 🎙️ **高精度转录**: 使用 OpenAI 的 Whisper 模型。
- 🌍 **多语言支持**: 集成 Google Translate 等服务，支持将字幕翻译成目标语言。
- 🎞️ **自动生成 SRT**: 直接生成标准 SRT 字幕文件。

## 🛠️ 安装指南 (重要)

由于需要启用 Mac 的硬件加速，安装 `pywhispercpp` 需要一些特定步骤，不能只简单运行 `pip install`。

### 1. 前置依赖

确保你安装了 ffmpeg：

```bash
brew install ffmpeg
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. (关键) 安装支持 CoreML 的 pywhispercpp

为了在 M 系列芯片上获得更快的速度，你需要重新编译安装 `pywhispercpp` 并开启 CoreML 支持。

> **注意**: 请确保已安装 Xcode Command Line Tools (`xcode-select --install`).

```bash
# 卸载可能存在的旧版本
pip uninstall pywhispercpp

# 下载 whisper.cppCoreML 权重转换脚本需要的依赖 (可选，如果模型自动下载失败)
pip install ane_transformers openai-whisper coremltools

# 源码编译安装 (开启 CoreML)
# 方法 A: 使用环境变量 (推荐)
WHISPER_COREML=1 pip install git+https://github.com/abdeladim-s/pywhispercpp

# 如果方法 A 失败，或你想手动编译：
# git clone https://github.com/abdeladim-s/pywhispercpp
# cd pywhispercpp
# WHISPER_COREML=1 pip install .
```

**第一次运行模型时**:
程序会自动下载 Whisper 模型。启用 CoreML 后，它还会自动将 PyTorch 模型转换为 CoreML 模型（这需要几分钟时间，请耐心等待）。转换后的模型会缓存，下次运行无需转换。

## 🚀 使用方法

### 基本用法 (转录 + 翻译成英文)

```bash
python3 -m autosub_mac.main your_video.mp4
```

### 🖥️ 可视化操作界面 (Web GUI)

我们提供了一个基于 Web 的可视化操作界面，方便进行拖拽上传和参数配置。

```bash
streamlit run app.py
```

运行后浏览器会自动打开操作页面。

### 指定模型大小

支持 `tiny`, `base`, `small`, `medium`, `large`。模型越大，精度越高，速度越慢。

```bash
python3 -m autosub_mac.main your_video.mp4 --model medium
```

### 翻译成中文 (默认 Google Translate)

```bash
python3 -m autosub_mac.main your_video.mp4 --lang zh-CN
```

### 使用 DeepL 翻译 (需要 API Key)

```bash
python3 -m autosub_mac.main your_video.mp4 --lang zh-CN --provider deepl --api-key YOUR_DEEPL_KEY
```

### 仅转录 (不翻译)

使用 `--no-translate` 参数。

```bash
python3 -m autosub_mac.main your_video.mp4 --no-translate
```

### ⚡️ 高级功能：分段多线程转录 (提高效率)

对于长视频，你可以将音频切分成小段并行处理。

- `--segment-duration`: 切分每段的时长（秒），建议设置为 300 或 600 (5-10 分钟)。
- `--threads`: 并行线程数，根据你的 Mac 核心数设置 (e.g., 4 or 8)。

```bash
# 将音频切分为 5 分钟一段，开启 4 个线程并行转录
python3 -m autosub_mac.main your_video.mp4 --segment-duration 300 --threads 4
```

> **注意**: 强制切分音频可能会导致切分点处的语句微小的不连贯（虽然 Whisper 通常能自动纠正上下文），建议切分粒度不要太小。

## 📂 项目结构

- `autosub_mac/`: 源码目录
- `requirements.txt`: 依赖列表

## ⚠️ 常见问题

1. **ImportError: No module named 'pywhispercpp'**

   - 请确保在虚拟环境中运行，并且安装步骤无误。

2. **CoreML 模型转换失败**
   - 请检查磁盘空间。
   - 确保安装了 `coremltools`。
   - 第一次转换非常消耗资源，请不要在转换过程中强制退出。
