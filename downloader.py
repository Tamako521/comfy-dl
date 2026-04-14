import argparse
import os
import sys
import requests
from pathlib import Path


def download_hf(model_id, dest):
    """从 HuggingFace 下载模型"""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        print("[错误] 未安装 huggingface_hub，请运行: pip install huggingface_hub")
        sys.exit(1)

    endpoint = os.environ.get("HF_ENDPOINT") or None
    token = os.environ.get("HF_TOKEN") or None

    print(f"[信息] 从 HuggingFace 下载: {model_id}")
    print(f"[信息] 目标目录: {dest}")
    if endpoint:
        print(f"[信息] 使用镜像站: {endpoint}")

    try:
        snapshot_download(
            repo_id=model_id,
            local_dir=dest,
            endpoint=endpoint,
            token=token,
        )
        print("[完成] 下载成功!")
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "not found" in error_msg.lower():
            print(f"[错误] 模型未找到，请检查 ID: {model_id}")
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print("[错误] 认证失败，请检查 HF_TOKEN 环境变量")
        else:
            print(f"[错误] 下载失败: {error_msg}")
            print("[提示] 请重新运行以继续下载（支持断点续传）")
        sys.exit(1)


def download_civitai(model_id, dest):
    """从 CivitAI 下载模型"""
    api_key = os.environ.get("CIVITAI_API_KEY", "")
    api_url = f"https://civitai.com/api/v1/models/{model_id}"

    print(f"[信息] 从 CivitAI 下载: {model_id}")
    print(f"[信息] 目标目录: {dest}")

    # 1. 查询模型信息
    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = requests.get(api_url, headers=headers, timeout=30)
        resp.raise_for_status()
        model_data = resp.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"[错误] 模型未找到，请检查 ID: {model_id}")
        elif e.response.status_code == 401:
            print("[错误] 认证失败，请在 comfy-dl.sh 配置区域填写 CIVITAI_API_KEY")
        else:
            print(f"[错误] 获取模型信息失败: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("[错误] 无法连接到 CivitAI，请检查网络")
        sys.exit(1)

    # 2. 获取最新版本的下载链接
    versions = model_data.get("modelVersions", [])
    if not versions:
        print("[错误] 该模型没有可用版本")
        sys.exit(1)

    latest_version = versions[0]
    files = latest_version.get("files", [])
    if not files:
        print("[错误] 该模型版本没有可下载文件")
        sys.exit(1)

    # 取主文件（通常是第一个）
    file_info = files[0]
    download_url = file_info.get("downloadUrl", "")
    file_name = file_info.get("name", f"model_{model_id}.safetensors")
    file_size = file_info.get("sizeKB", 0) * 1024  # 转为字节

    if not download_url:
        print("[错误] 无法获取下载链接")
        sys.exit(1)

    # 带上 API Key
    if api_key:
        separator = "&" if "?" in download_url else "?"
        download_url = f"{download_url}{separator}token={api_key}"

    # 3. 下载文件（支持断点续传）
    file_path = Path(dest) / file_name
    _download_file(download_url, file_path, file_size)
    print("[完成] 下载成功!")


def _download_file(url, file_path, total_size=0):
    """带断点续传和进度条的文件下载"""
    try:
        from tqdm import tqdm
    except ImportError:
        print("[错误] 未安装 tqdm，请运行: pip install tqdm")
        sys.exit(1)

    # 断点续传：检查已下载的部分
    downloaded = 0
    if file_path.exists():
        downloaded = file_path.stat().st_size
        if total_size and downloaded >= total_size:
            print(f"[信息] 文件已存在且完整: {file_path.name}")
            return

    headers = {}
    if downloaded > 0:
        headers["Range"] = f"bytes={downloaded}-"
        print(f"[信息] 检测到已下载 {_format_size(downloaded)}，继续下载...")

    try:
        resp = requests.get(url, headers=headers, stream=True, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401 or e.response.status_code == 403:
            print("[错误] 下载被拒绝，请检查 CIVITAI_API_KEY 是否正确")
        else:
            print(f"[错误] 下载请求失败: {e}")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("[错误] 网络连接失败")
        print("[提示] 请重新运行以继续下载（支持断点续传）")
        sys.exit(1)

    # 如果服务器返回 Content-Range，说明支持续传
    if resp.status_code == 206:
        mode = "ab"
    else:
        mode = "wb"
        downloaded = 0

    # 获取总大小
    content_length = resp.headers.get("Content-Length")
    if content_length:
        remaining = int(content_length)
        total = downloaded + remaining
    elif total_size:
        total = total_size
    else:
        total = 0

    print(f"[信息] 正在下载: {file_path.name}")

    try:
        with open(file_path, mode) as f:
            with tqdm(
                total=total,
                initial=downloaded,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=file_path.name,
                ncols=80,
            ) as pbar:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
    except (requests.exceptions.ConnectionError, IOError) as e:
        print(f"\n[错误] 下载中断: {e}")
        print("[提示] 请重新运行以继续下载（支持断点续传）")
        sys.exit(1)
    except OSError as e:
        if "No space" in str(e) or "空间不足" in str(e):
            print(f"\n[错误] 磁盘空间不足")
        else:
            print(f"\n[错误] 写入文件失败: {e}")
        sys.exit(1)


def _format_size(size_bytes):
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 模型下载工具")
    parser.add_argument("--source", required=True, choices=["hf", "civitai"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()

    os.makedirs(args.dest, exist_ok=True)

    if args.source == "hf":
        download_hf(args.model, args.dest)
    elif args.source == "civitai":
        download_civitai(args.model, args.dest)


if __name__ == "__main__":
    main()
