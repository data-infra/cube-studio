export HF_ENDPOINT=https://hf-mirror.com
apt update && apt install -y aria2 git-lfs wget
wget https://hf-mirror.com/hfd/hfd.sh && chmod a+x hfd.sh
./hfd.sh meta-llama/Meta-Llama-3-8B-Instruct --tool aria2c -x 8