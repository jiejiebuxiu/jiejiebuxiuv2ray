from pathlib import Path
import re


INPUT = "fast_nodes.txt"


def score(node):

    s = 0
    x = node.lower()


    # 协议
    if x.startswith("vless://"):
        s += 30

    elif x.startswith("trojan://"):
        s += 25

    elif x.startswith("ss://"):
        s += 15



    # 高级传输

    if "security=reality" in x:
        s += 40

    if "security=tls" in x:
        s += 20

    if "type=grpc" in x:
        s += 20

    if "type=ws" in x:
        s += 10


    # 常见优质地区关键词

    regions = [
        "jp",
        "japan",
        "sg",
        "singapore",
        "hk",
        "hongkong",
        "us",
        "america",
        "de",
        "germany"
    ]

    for r in regions:
        if r in x:
            s += 5


    # 垃圾关键词

    bad=[
        "expire",
        "expired",
        "test",
        "free",
        "telegram",
        "null"
    ]

    for b in bad:
        if b in x:
            s -= 20


    # 节点长度
    if len(node)>100:
        s+=5


    return s



def clean(lines):

    result=[]
    seen=set()

    for n in lines:

        n=n.strip()

        if not n:
            continue


        if not (
            n.startswith("vless://")
            or n.startswith("trojan://")
            or n.startswith("ss://")
        ):
            continue


        key=n.split("#")[0]


        if key in seen:
            continue


        seen.add(key)

        result.append(n)


    return result



def save(name,data):

    Path(name).write_text(
        "\n".join(data),
        encoding="utf-8"
    )



def main():

    data=Path(INPUT).read_text(
        encoding="utf-8",
        errors="ignore"
    )


    nodes=clean(data.splitlines())


    print("有效节点:",len(nodes))


    nodes.sort(
        key=score,
        reverse=True
    )


    top100=nodes[:100]

    top50=nodes[:50]


    save(
        "top100.txt",
        top100
    )


    save(
        "top50.txt",
        top50
    )


    save(
        "vless_top.txt",
        [x for x in top100 if x.startswith("vless://")]
    )


    save(
        "trojan_top.txt",
        [x for x in top100 if x.startswith("trojan://")]
    )


    save(
        "ss_top.txt",
        [x for x in top100 if x.startswith("ss://")]
    )


    print("TOP100:",len(top100))
    print("TOP50:",len(top50))

    print("完成")



if __name__=="__main__":
    main()