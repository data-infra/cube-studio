export HF_ENDPOINT=https://hf-mirror.com
apt update && apt install -y aria2 git-lfs wget
wget https://hf-mirror.com/hfd/hfd.sh && chmod a+x hfd.sh
./hfd.sh Qwen/Qwen2.5-7B-Instruct --tool aria2c -x 8
sed -i "s|bfloat16|float16|g"  Qwen2.5-7B-Instruct/config.json