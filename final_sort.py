import re


INPUT = "speed_rank.txt"

OUTPUT = "best_nodes.txt"

REPORT = "best_report.txt"


MAX_OUTPUT = 1500



def get_server(node):

    try:

        # vless/trojan

        m = re.search(
            r'@([^:/?#]+)',
            node
        )

        if m:
            return m.group(1)



        # vmess json

        m = re.search(
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

        lines=f.readlines()



    print(
        "读取:",
        len(lines)
    )


    servers=set()

    result=[]


    for line in lines:


        line=line.strip()


        if not line:
            continue



        # 去掉前面的延迟

        m=re.search(
            r'\d+ms\s+(.*)',
            line
        )


        if not m:

            continue


        node=m.group(1)



        server=get_server(node)



        if server:


            if server in servers:

                continue


            servers.add(server)



        result.append(node)



    print(
        "去重后:",
        len(result)
    )



    result=result[:MAX_OUTPUT]



    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:


        for n in result:

            f.write(
                n+"\n"
            )



    with open(
        REPORT,
        "w",
        encoding="utf-8"
    ) as f:


        f.write(
            "原始:"
            +str(len(lines))
            +"\n"
        )

        f.write(
            "去重:"
            +str(len(result))
            +"\n"
        )



    print(
        "生成:",
        OUTPUT
    )



main()