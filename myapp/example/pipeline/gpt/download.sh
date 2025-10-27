
pip3 install -U huggingface_hub hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_ENDPOINT="https://hf-mirror.com"

# 下载chatglm4
mkdir -p THUDM/glm-4-9b-chat
huggingface-cli download --resume-download THUDM/glm-4-9b-chat --local-dir THUDM/glm-4-9b-chat --local-dir-use-symlinks False

# 下载qwen3
mkdir -p Qwen/Qwen3-8B
huggingface-cli download --resume-download Qwen/Qwen3-8B-Instruct --local-dir Qwen/Qwen3-8B --local-dir-use-symlinks False

# 下载bigscience/bloomz
mkdir -p bigscience/bloomz
huggingface-cli download --resume-download bigscience/bloomz --local-dir bigscience/bloomz --local-dir-use-symlinks False

# 下载llama3
mkdir -p meta-llama/Meta-Llama-3-8B
huggingface-cli download --resume-download meta-llama/Meta-Llama-3-8B --local-dir meta-llama/Meta-Llama-3-8B --local-dir-use-symlinks False

