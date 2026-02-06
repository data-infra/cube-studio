import argparse, time
import torch
import torch.nn as nn
import torch.optim as optim
import horovod.torch as hvd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()

    hvd.init()

    use_cuda = torch.cuda.is_available()
    if use_cuda:
        torch.cuda.set_device(hvd.local_rank())

    if hvd.rank() == 0:
        print(f"[HVD] size={hvd.size()} cuda={use_cuda}")

    model = nn.Sequential(
        nn.Linear(1024, 2048),
        nn.ReLU(),
        nn.Linear(2048, 1000),
    )
    if use_cuda:
        model.cuda()

    optimizer = optim.AdamW(model.parameters(), lr=args.lr * hvd.size())
    optimizer = hvd.DistributedOptimizer(optimizer, named_parameters=model.named_parameters())

    hvd.broadcast_parameters(model.state_dict(), root_rank=0)
    hvd.broadcast_optimizer_state(optimizer, root_rank=0)

    loss_fn = nn.CrossEntropyLoss()

    t0 = time.time()
    loss_avg = 0.0

    for step in range(args.steps):
        x = torch.randn(args.batch_size, 1024)
        y = torch.randint(0, 1000, (args.batch_size,))

        if use_cuda:
            x = x.cuda()
            y = y.cuda()

        optimizer.zero_grad()
        logits = model(x)
        loss = loss_fn(logits, y)
        loss.backward()
        optimizer.step()

        loss_v = hvd.allreduce(loss.detach(), name="loss").item()
        loss_avg = loss_v if step == 0 else (0.9 * loss_avg + 0.1 * loss_v)

        if hvd.rank() == 0 and (step % 10 == 0 or step == args.steps - 1):
            print(f"[训练信息] step={step:03d} loss_avg={loss_avg:.4f}")

    if hvd.rank() == 0:
        print(f"[完成] steps={args.steps}, time={time.time()-t0:.2f}s")

if __name__ == "__main__":
    main()