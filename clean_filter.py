import re


INPUT = "best_nodes.txt"


FILES = {
    "reality_nodes.txt": [],
    "trojan_nodes.txt": [],
    "vless_ws_nodes.txt": [],
    "ss_nodes.txt": []
}


# 垃圾关键词
BAD_WORDS = [
    "deepseek",
    "example",
    "test",
    "localhost",
    "127.0.0.1",
    "googleusercontent",
]


servers=set()



def get_host(node):

    try:

        m=re.search(
            r'@([^:/?#]+)',
            node
        )

        if m:
            return m.group(1)


    except:
        pass


    return None



def bad_node(node):

    low=node.lower()

    for w in BAD_WORDS:

        if w in low:
            return True

    return False



def main():


    with open(
        INPUT,
        encoding="utf-8"
    ) as f:

        nodes=f.readlines()



    total=0
    clean=0


    for node in nodes:


        node=node.strip()


        if not node:
            continue


        total+=1



        if bad_node(node):

            continue



        host=get_host(node)


        if host:


            if host in servers:

                continue


            servers.add(host)



        clean+=1



        # Reality

        if (
            node.startswith("vless://")
            and "security=reality" in node
        ):

            FILES["reality_nodes.txt"].append(node)



        # Trojan

        elif node.startswith("trojan://"):

            FILES["trojan_nodes.txt"].append(node)



        # VLESS WS

        elif (
            node.startswith("vless://")
            and "type=ws" in node
        ):

            FILES["vless_ws_nodes.txt"].append(node)



        # SS

        elif node.startswith("ss://"):

            FILES["ss_nodes.txt"].append(node)



    for filename,data in FILES.items():


        with open(
            filename,
            "w",
            encoding="utf-8"
        ) as f:

            for n in data:

                f.write(
                    n+"\n"
                )



    with open(
        "clean_report.txt",
        "w",
        encoding="utf-8"
    ) as f:


        f.write(
            "原始节点:"
            +str(total)
            +"\n"
        )


        f.write(
            "清洗后:"
            +str(clean)
            +"\n\n"
        )


        for k,v in FILES.items():

            f.write(
                k
                +" : "
                +str(len(v))
                +"\n"
            )



    print("完成")
    print("原始:",total)
    print("清洗:",clean)


    for k,v in FILES.items():

        print(
            k,
            len(v)
        )



main()