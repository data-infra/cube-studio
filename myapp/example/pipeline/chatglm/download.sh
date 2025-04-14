#pip3 install -U huggingface_hub==0.22.2 hf_transfer
#export HF_HUB_ENABLE_HF_TRANSFER=1
#export HF_ENDPOINT="https://hf-mirror.com"

# 下载chatglm2
# mkdir -p chatglm2-6b
# huggingface-cli download --resume-download THUDM/chatglm2-6b --local-dir chatglm2-6b --local-dir-use-symlinks False

# 下载chatglm3
#mkdir -p chatglm3-6b
#huggingface-cli download --resume-download THUDM/chatglm3-6b --local-dir chatglm3-6b --local-dir-use-symlinks False

# 下载chatglm4
#mkdir -p glm-4-9b-chat
#huggingface-cli download --resume-download THUDM/glm-4-9b-chat --local-dir glm-4-9b-chat --local-dir-use-symlinks False


# 使用hfd.sh脚本下载
export HF_ENDPOINT=https://hf-mirror.com
apt update && apt install -y aria2 git-lfs wget
wget https://hf-mirror.com/hfd/hfd.sh && chmod a+x hfd.sh
./hfd.sh THUDM/chatglm3-6b --tool aria2c -x 8
./hfd.sh THUDM/glm-4-9b-chat --tool aria2c -x 8

### 从阿里云下载chatglm2
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-aa
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ab
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ac
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ad
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ae
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-af
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ag
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ah
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-ai
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm2/chatglm2-6b-part-aj
#cat chatglm2-6b-part-* >  chatglm2-6b.zip
#unzip -d ./ chatglm2-6b.zip
#rm -rf chatglm2-6b.zip chatglm2-6b-part-*
#
## 从阿里云下载chatglm3
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-aa
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ab
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ac
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ad
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ae
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-af
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ag
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ah
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-ai
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/chatglm3/chatglm3-part-aj
#
#cat chatglm3-part-* >  chatglm3-6b.zip
#unzip -d ./ chatglm3-6b.zip
#rm -rf chatglm3-6b.zip chatglm3-part-*