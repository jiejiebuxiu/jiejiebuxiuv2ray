import re


INPUT = "fast_nodes.txt"

OUTPUT = "final_nodes.txt"

REPORT = "node_report.txt"



MAX_OUTPUT = 2000



def clean_node(node):

    node = node.strip()

    if not node:
        return None

    bad_words = [
        "telegram",
        "channel",
        "join"
    ]

    low = node.lower()

    for w in bad_words:
        if w in low:
            return None

    return node


    for w in bad_words:

        if w in low:

            return None



    return node





def get_server(node):

    try:

        # vless/trojan

        m=re.search(

            r'@([^:/?#]+)',

            node

        )


        if m:

            return m.group(1)



        # 部分vmess

        m=re.search(

            r'"add":"([^"]+)"',

            node

        )

        if m:

            return m.group(1)


    except:

        pass


    return None





def main():


    with open(
        INPUT,
        encoding="utf-8"
    ) as f:

        nodes=f.readlines()



    print(
        "读取:",
        len(nodes)
    )


    clean=[]


    servers=set()


    for n in nodes:


        n=clean_node(n)


        if not n:

            continue



        server=get_server(n)


        # 去重复服务器

        if server:

            if server in servers:

                continue

            servers.add(server)



        clean.append(n)



    print(
        "清洗后:",
        len(clean)
    )



    # 保存

    clean=clean[:MAX_OUTPUT]



    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:


        for n in clean:

            f.write(
                n+"\n"
            )



    with open(
        REPORT,
        "w",
        encoding="utf-8"
    ) as f:


        f.write(
            "原始数量:"
            +str(len(nodes))
            +"\n"
        )

        f.write(
            "最终数量:"
            +str(len(clean))
        )



    print(
        "生成:",
        OUTPUT
    )



main()