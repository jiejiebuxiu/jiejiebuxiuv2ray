import re
from pathlib import Path


INPUT = "best_nodes.txt"


def score(node):

    s = 0

    # 协议优先级
    if node.startswith("vless://"):
        s += 30

    if node.startswith("trojan://"):
        s += 25

    if node.startswith("ss://"):
        s += 15


    # Reality
    if "security=reality" in node:
        s += 40

    # TLS
    if "security=tls" in node:
        s += 20

    # WS
    if "type=ws" in node:
        s += 10


    # 惩罚垃圾

    bad=[
        "chat.deepseek",
        "workers.dev",
        "pages.dev",
        "cloudflare"
    ]

    for b in bad:
        if b in node:
            s-=15


    # 太长一般是垃圾机场转换
    if len(node)>800:
        s-=20


    return s



def clean():

    p=Path(INPUT)

    if not p.exists():
        print("找不到 best_nodes.txt")
        return


    nodes=p.read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()


    result=[]

    seen=set()


    for n in nodes:

        n=n.strip()

        if not n:
            continue


        if not (
            n.startswith(
            (
            "vless://",
            "trojan://",
            "ss://"
            ))
        ):
            continue


        # 去重复
        key=n.split("#")[0]

        if key in seen:
            continue

        seen.add(key)


        result.append(
            (score(n),n)
        )


    result.sort(
        reverse=True,
        key=lambda x:x[0]
    )


    all_nodes=[x[1] for x in result]


    Path(
    "final_best.txt"
    ).write_text(
        "\n".join(all_nodes),
        encoding="utf-8"
    )


    Path(
    "top100.txt"
    ).write_text(
        "\n".join(all_nodes[:100]),
        encoding="utf-8"
    )


    Path(
    "top500.txt"
    ).write_text(
        "\n".join(all_nodes[:500]),
        encoding="utf-8"
    )


    with open(
        "report.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
        f"总节点:{len(nodes)}\n"
        )

        f.write(
        f"有效节点:{len(all_nodes)}\n"
        )

        f.write(
        "\n前20评分:\n"
        )

        for s,n in result[:20]:
            f.write(
            f"{s} {n[:80]}\n"
            )


    print(
    "完成"
    )

    print(
    "最终:",
    len(all_nodes)
    )



if __name__=="__main__":
    clean()