import re


INPUT = "subscribe.txt"

OUTPUT = "good_nodes.txt"


BAD_WORDS = [
    "官网",
    "流量",
    "剩余",
    "套餐",
    "到期",
    "机场",
    "群",
    "邀请",
    "优惠"
]


def clean():

    with open(
        INPUT,
        "r",
        encoding="utf-8"
    ) as f:

        nodes=f.readlines()


    result=[]


    for node in nodes:

        node=node.strip()


        if len(node)<30:
            continue


        bad=False


        for w in BAD_WORDS:

            if w in node:

                bad=True
                break


        if bad:
            continue


        result.append(node)



    # 去重

    result=list(set(result))


    print(
        "过滤后:",
        len(result)
    )


    # 优先排序

    result.sort(
        key=lambda x:
        (
            "vless" not in x,
            "trojan" not in x
        )
    )


    # 保留前50000

    result=result[:50000]


    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:


        for n in result:

            f.write(
                n+"\n"
            )


    print(
        "生成:",
        OUTPUT
    )



if __name__=="__main__":

    clean()