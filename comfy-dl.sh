#!/bin/bash
# ========== 配置区域 ==========
WORKSPACE="/workspace"
CIVITAI_API_KEY=""
HF_ENDPOINT="https://huggingface.co"
# ==============================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== ComfyUI 模型下载工具 ==="
echo ""

# 检查 WORKSPACE 是否存在
if [ ! -d "$WORKSPACE" ]; then
    echo "[错误] 工作目录 $WORKSPACE 不存在，请检查配置区域中的 WORKSPACE"
    exit 1
fi

# 检查 ComfyUI 目录
COMFYUI_DIR="$WORKSPACE/ComfyUI"
if [ ! -d "$COMFYUI_DIR" ]; then
    echo "[错误] 未找到 $COMFYUI_DIR，请确认 ComfyUI 已安装"
    exit 1
fi

# 选择下载类型
while true; do
    echo "请选择下载类型："
    echo "1) 模型 (checkpoint)"
    echo "2) LoRA"
    read -p "> " type_choice
    case $type_choice in
        1) dest="checkpoints"; break ;;
        2) dest="loras"; break ;;
        *) echo "[提示] 无效选项，请输入 1 或 2"; echo "" ;;
    esac
done

echo ""

# 选择下载源
while true; do
    echo "请选择下载源："
    echo "1) HuggingFace"
    echo "2) CivitAI"
    read -p "> " source_choice
    case $source_choice in
        1) source="hf"; break ;;
        2) source="civitai"; break ;;
        *) echo "[提示] 无效选项，请输入 1 或 2"; echo "" ;;
    esac
done

echo ""

# 输入模型 ID
read -p "请输入模型 ID: " model_id
if [ -z "$model_id" ]; then
    echo "[错误] 模型 ID 不能为空"
    exit 1
fi

echo ""

# 导出环境变量并调用 Python
export WORKSPACE HF_ENDPOINT CIVITAI_API_KEY
python "$SCRIPT_DIR/downloader.py" \
    --source "$source" \
    --model "$model_id" \
    --dest "$COMFYUI_DIR/models/$dest"
