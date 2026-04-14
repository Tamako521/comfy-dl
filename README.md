# comfy-dl

ComfyUI 模型与 LoRA 下载工具，支持 HuggingFace 和 CivitAI。适用于云平台（AI Studio、AutoDL 等）环境，免去手动拼接长命令的麻烦。

## 目录结构

将 `comfy-dl` 文件夹放到云平台工作目录，与 `ComfyUI` 并列：

```
<工作目录>/
├── ComfyUI/
└── comfy-dl/
    ├── comfy-dl.sh
    ├── downloader.py
    └── README.md
```

## 安装依赖

```bash
pip install huggingface_hub requests tqdm
```

## 配置

打开 `comfy-dl.sh`，修改顶部配置区域：

```bash
WORKSPACE="/workspace"                   # 云平台工作目录（如 /workspace 或 /aistudio）
CIVITAI_API_KEY=""                       # CivitAI API Key（需要认证时填写）
HF_ENDPOINT="https://huggingface.co"     # HuggingFace 地址，国内可改为 https://hf-mirror.com
```

如需下载 HuggingFace 私有模型，额外导出环境变量：

```bash
export HF_TOKEN="hf_xxxxxxxxxxxx"
```

## 使用

```bash
bash comfy-dl.sh
```

按提示依次选择：

1. 下载类型：`1) 模型` 或 `2) LoRA`
2. 下载源：`1) HuggingFace` 或 `2) CivitAI`
3. 输入模型 ID：
   - HuggingFace：格式 `用户名/仓库名`，例如 `stabilityai/stable-diffusion-xl-base-1.0`
   - CivitAI：模型数字 ID，例如 `12345`（从模型页面 URL 中获取）

下载文件将自动存放到：

- 模型 → `$WORKSPACE/ComfyUI/models/checkpoints/`
- LoRA → `$WORKSPACE/ComfyUI/models/loras/`

## 修改存放路径

如需更改默认的存放目录，编辑 [comfy-dl.sh](comfy-dl.sh) 中 `case $type_choice` 分支（约第 32-36 行）：

```bash
case $type_choice in
    1) dest="checkpoints"; break ;;   # 模型存放目录
    2) dest="loras"; break ;;         # LoRA 存放目录
    *) echo "[提示] 无效选项，请输入 1 或 2"; echo "" ;;
esac
```

- **模型存放路径**：可将 `checkpoints` 改为 `diffusion_models`（ComfyUI 也会从该目录加载扩散模型）。
- **LoRA 存放路径**：请勿修改，必须保持为 `loras`，否则 ComfyUI 的 LoRA 加载节点无法识别。

## 特性

- 进度条显示
- 断点续传：网络中断后重新运行即可继续
- 清晰的错误提示

## 常见问题

**Q: 下载中断了怎么办？**
重新运行 `bash comfy-dl.sh`，用相同参数继续下载，会自动从中断处续传。

**Q: 国内无法访问 HuggingFace？**
将 `HF_ENDPOINT` 改为 `https://hf-mirror.com`。

**Q: CivitAI 提示认证失败？**
在 CivitAI 账户设置中生成 API Key，填入 `comfy-dl.sh` 的 `CIVITAI_API_KEY`。

