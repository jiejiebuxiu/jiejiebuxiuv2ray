import socket
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import re


INPUT = "fast_nodes.txt"


OUTPUT = "speed_result.txt"


TOP = "speed_top100.txt"


THREADS = 200



def get_host_port(node):

    try:

        m = re.search(
            r'@([^:/?#]+):(\d+)',
            node
        )

        if m:
            return (
                m.group(1),
                int(m.group(2))
            )


    except:
        pass


    return None,None



def test(node):

    host,port=get_host_port(node)


    if not host:
        return None


    start=time.time()


    try:

        s=socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        s.settimeout(3)


        s.connect(
            (host,port)
        )


        delay=int(
            (time.time()-start)*1000
        )


        s.close()


        return (
            delay,
            node
        )


    except:

        return None



def main():


    nodes=Path(INPUT).read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()



    print(
        "节点:",
        len(nodes)
    )


    result=[]


    with ThreadPoolExecutor(
        max_workers=THREADS
    ) as pool:


        tasks=[
            pool.submit(test,n)
            for n in nodes
        ]


        for t in as_completed(tasks):

            r=t.result()

            if r:

                result.append(r)



    result.sort(
        key=lambda x:x[0]
    )


    print(
        "成功:",
        len(result)
    )



    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:


        for delay,node in result:

            f.write(
                f"{delay}ms {node}\n"
            )



    with open(
        TOP,
        "w",
        encoding="utf-8"
    ) as f:


        for delay,node in result[:100]:

            f.write(
                node+"\n"
            )


    print(
        "生成完成"
    )

    print(
        TOP
    )



if __name__=="__main__":

    main()