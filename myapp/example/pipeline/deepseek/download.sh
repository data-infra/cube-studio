
# 使用hfd.sh脚本下载
export HF_ENDPOINT=https://hf-mirror.com
apt update && apt install -y aria2 git-lfs wget
wget https://hf-mirror.com/hfd/hfd.sh && chmod a+x hfd.sh

./hfd.sh deepseek-ai/DeepSeek-R1-Distill-Qwen-7B --tool aria2c -x 8

sed -i "s|bfloat16|float16|g"  DeepSeek-R1-Distill-Qwen-7B/config.json

#./hfd.sh deepseek-ai/DeepSeek-R1-Distill-Qwen-14B --tool aria2c -x 8

