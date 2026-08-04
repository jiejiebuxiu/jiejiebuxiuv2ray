from pathlib import Path
import re


INPUT = "speed_result.txt"


OUT = "clean_speed_top100.txt"



BAD_WORDS = [

    "deepseek",
    "workers.dev",
    "pages.dev",
    "speedtest.net",
    "telegram",
    "expire",
    "expired",
    "test"

]



def score(line):

    s = 0

    x=line.lower()


    # 延迟分

    m=re.search(
        r"(\d+)ms",
        x
    )

    if m:

        ms=int(m.group(1))

        if ms < 50:
            s+=50

        elif ms <100:
            s+=35

        elif ms <200:
            s+=20

        else:
            s+=5



    # 协议

    if "vless://" in x:
        s+=30

    elif "trojan://" in x:
        s+=25

    elif "ss://" in x:
        s+=15



    # 高质量传输

    if "security=reality" in x:
        s+=40


    if "security=tls" in x:
        s+=20


    if "grpc" in x:
        s+=15


    if "type=ws" in x:
        s+=5



    # 垃圾扣分

    for b in BAD_WORDS:

        if b in x:
            s-=80



    # 超长路径

    if len(line)>700:

        s-=30



    return s




def main():


    lines=Path(INPUT).read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()



    result=[]


    seen=set()



    for line in lines:


        key=line.split("#")[0]


        if key in seen:
            continue


        seen.add(key)



        result.append(
            (
                score(line),
                line
            )
        )



    result.sort(
        reverse=True,
        key=lambda x:x[0]
    )



    nodes=[]


    for s,n in result:

        # 去掉前面的ms，只输出节点

        node=re.sub(
            r"^\d+ms\s+",
            "",
            n
        )

        nodes.append(node)



    Path(OUT).write_text(
        "\n".join(nodes[:100]),
        encoding="utf-8"
    )



    with open(
        "v10_5_report.txt",
        "w",
        encoding="utf-8"
    ) as f:

        for s,n in result[:50]:

            f.write(
                str(s)
                +" "
                +n[:120]
                +"\n"
            )



    print("原始:",len(lines))

    print("输出TOP100")



if __name__=="__main__":

    main()