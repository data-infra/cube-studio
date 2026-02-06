from llamafactory.chat import ChatModel
from llamafactory.extras.misc import torch_gc

args = dict(
    model_name_or_path="/app/qwen-vl-7b",
    adapter_name_or_path="qwen2_vl_lora",
    template="qwen2_vl",
    finetuning_type="lora",
    trust_remote_code=True,
)

chat_model = ChatModel(args)

messages = []
images_ctx = []

print("使用：img <图片路径> <空格> <你的问题>。输入 clear 清空历史，exit 退出。")
while True:
    query = input("\nUser: ").strip()
    if query == "exit":
        break
    if query == "clear":
        messages.clear()
        images_ctx.clear()
        torch_gc()
        print("历史已清空。")
        continue

    if query.startswith("img "):
        rest = query[4:].strip()
        if " " in rest:
            img_path, user_text = rest.split(" ", 1)
            user_text = user_text.strip()
        else:
            img_path, user_text = rest, "请描述这张图"

        messages.append({"role": "user", "content": f"<image>\n{user_text}"})
        images_ctx.append(img_path)
    else:
        messages.append({"role": "user", "content": query})

    kwargs = {"images": images_ctx} if images_ctx else {}

    print("Assistant: ", end="", flush=True)
    response = ""
    for tok in chat_model.stream_chat(messages, **kwargs):
        print(tok, end="", flush=True)
        response += tok
    print()
    messages.append({"role": "assistant", "content": response})

torch_gc()
