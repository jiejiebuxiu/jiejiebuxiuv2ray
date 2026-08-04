import re
from pathlib import Path


INPUT = "best_nodes.txt"


def score(node):

    s = 0
    low = node.lower()

    # 协议评分
    if low.startswith("vless://"):
        s += 30

    elif low.startswith("trojan://"):
        s += 25

    elif low.startswith("ss://"):
        s += 15


    # 安全类型
    if "security=tls" in low:
        s += 20

    if "security=reality" in low:
        s += 30

    if "type=ws" in low:
        s += 10

    if "grpc" in low:
        s += 10


    # 删除明显垃圾
    bad = [
        "telegram",
        "test",
        "expire",
        "expired",
        "null",
        "undefined"
    ]

    for b in bad:
        if b in low:
            s -= 50


    # 节点长度合理
    if len(node) > 80:
        s += 5


    return s



def clean(lines):

    result=[]

    seen=set()

    for x in lines:

        x=x.strip()

        if not x:
            continue

        if not (
            x.startswith("vless://")
            or x.startswith("trojan://")
            or x.startswith("ss://")
        ):
            continue


        key=x.split("#")[0]

        if key in seen:
            continue

        seen.add(key)

        result.append(x)


    return result



def save(name,data):

    Path(name).write_text(
        "\n".join(data),
        encoding="utf-8"
    )



def main():

    text=Path(INPUT).read_text(
        encoding="utf-8",
        errors="ignore"
    )


    nodes=clean(text.splitlines())


    nodes.sort(
        key=score,
        reverse=True
    )


    print("清洗后:",len(nodes))


    save(
        "v8_best_nodes.txt",
        nodes
    )


    vless=[
        x for x in nodes
        if x.startswith("vless://")
    ]

    trojan=[
        x for x in nodes
        if x.startswith("trojan://")
    ]

    ss=[
        x for x in nodes
        if x.startswith("ss://")
    ]


    save("v8_vless.txt",vless)
    save("v8_trojan.txt",trojan)
    save("v8_ss.txt",ss)


    print("VLESS:",len(vless))
    print("Trojan:",len(trojan))
    print("SS:",len(ss))

    print("完成")



if __name__=="__main__":
    main()