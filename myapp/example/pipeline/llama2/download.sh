#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-aa &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ab &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ac &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ad &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ae &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-af &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ag &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ah &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ai &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-aj &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-ak &
#wget https://cube-studio.oss-cn-hangzhou.aliyuncs.com/aihub/gpt/llama2/Llama2-Chinese-7b-Chat-part-al &
#
#wait
#
#cat Llama2-Chinese-7b-Chat-part-* > Llama2-Chinese-7b-Chat.zip
#
#unzip -d ./ Llama2-Chinese-7b-Chat.zip
#
#rm -rf Llama2-Chinese-7b-Chat.zip
#rm -rf Llama2-Chinese-7b-Chat-part-a*


pip install -U huggingface_hub hf_transfer
export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_ENDPOINT="https://hf-mirror.com"
mkdir -p FlagAlpha/Llama2-Chinese-7b-Chat
huggingface-cli download --resume-download FlagAlpha/Llama2-Chinese-7b-Chat --local-dir FlagAlpha/Llama2-Chinese-7b-Chat --local-dir-use-symlinks False

