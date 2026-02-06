import os, time, argparse
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import Dataset, DataLoader, DistributedSampler
import colossalai

class RandomClsDataset(Dataset):
    def __init__(self, n, in_dim, num_classes, seed):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(n, in_dim, generator=g)
        self.y = torch.randint(0, num_classes, (n,), generator=g)
    def __len__(self): return self.x.size(0)
    def __getitem__(self, idx): return self.x[idx], self.y[idx]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=int(os.getenv("STEPS", "50")))
    ap.add_argument("--batch_size", type=int, default=int(os.getenv("BATCH_SIZE", "8")))
    ap.add_argument("--lr", type=float, default=float(os.getenv("LR", "1e-3")))
    ap.add_argument("--in_dim", type=int, default=1024)
    ap.add_argument("--hidden", type=int, default=2048)
    ap.add_argument("--num_classes", type=int, default=10)
    ap.add_argument("--dataset_size", type=int, default=4096)
    args = ap.parse_args()

    backend = "nccl" if torch.cuda.is_available() else "gloo"
    colossalai.launch_from_torch(backend=backend)

    rank = dist.get_rank()
    world = dist.get_world_size()
    local_rank = int(os.environ.get("LOCAL_RANK", "0"))

    if torch.cuda.is_available():
        torch.cuda.set_device(local_rank)
        device = torch.device("cuda", local_rank)
    else:
        device = torch.device("cpu")

    if rank == 0:
        print(f"[初始化] backend={backend} world_size={world}")
        print(f"[环境] MASTER_ADDR={os.environ.get('MASTER_ADDR')} MASTER_PORT={os.environ.get('MASTER_PORT')}")

    model = nn.Sequential(
        nn.Linear(args.in_dim, args.hidden),
        nn.GELU(),
        nn.Linear(args.hidden, args.num_classes),
    ).to(device)

    ddp = DDP(
        model,
        device_ids=[local_rank] if device.type == "cuda" else None,
        output_device=local_rank if device.type == "cuda" else None,
    )
    opt = torch.optim.AdamW(ddp.parameters(), lr=args.lr)
    loss_fn = nn.CrossEntropyLoss()

    ds = RandomClsDataset(args.dataset_size, args.in_dim, args.num_classes, seed=2026)
    sampler = DistributedSampler(ds, num_replicas=world, rank=rank, shuffle=True, seed=2026)
    dl = DataLoader(ds, batch_size=args.batch_size, sampler=sampler, num_workers=0, pin_memory=(device.type=="cuda"))

    it = iter(dl)
    t0 = time.time()
    for step in range(args.steps):
        try:
            x, y = next(it)
        except StopIteration:
            sampler.set_epoch(step)
            it = iter(dl)
            x, y = next(it)

        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        opt.zero_grad(set_to_none=True)
        logits = ddp(x)
        loss = loss_fn(logits, y)
        loss.backward()
        opt.step()

        # 聚合loss，验证跨rank通信
        loss_det = loss.detach()
        dist.all_reduce(loss_det, op=dist.ReduceOp.SUM)
        loss_avg = (loss_det / world).item()

        if rank == 0 and (step % 10 == 0 or step == args.steps - 1):
            print(f"[训练] step={step:03d} loss_avg={loss_avg:.4f}")

    dist.barrier()
    if rank == 0:
        print(f"[完成] steps={args.steps}, time={time.time()-t0:.2f}s")
    dist.destroy_process_group()

if __name__ == "__main__":
    main()