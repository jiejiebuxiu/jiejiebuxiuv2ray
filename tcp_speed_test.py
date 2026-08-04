import asyncio
import re
import time


INPUT = "good_nodes.txt"

OUTPUT = "fast_nodes.txt"

RANK = "speed_rank.txt"


TIMEOUT = 2

CONCURRENT = 300



def get_host_port(node):

    try:

        # 提取 @ 后面的地址

        m = re.search(
            r'@([^/?#:]+):(\d+)',
            node
        )

        if m:
            return (
                m.group(1),
                int(m.group(2))
            )


        # 兼容部分格式

        m = re.search(
            r'([^:/]+):(\d+)',
            node
        )

        if m:
            return (
                m.group(1),
                int(m.group(2))
            )

    except:

        pass


    return None



async def check(node, sem):

    async with sem:

        hp=get_host_port(node)


        if not hp:

            return None


        host,port=hp


        try:

            start=time.perf_counter()


            reader,writer=await asyncio.wait_for(

                asyncio.open_connection(
                    host,
                    port
                ),

                timeout=TIMEOUT
            )


            delay=int(
                (time.perf_counter()-start)*1000
            )


            writer.close()


            try:
                await writer.wait_closed()
            except:
                pass


            return (
                delay,
                node.strip()
            )


        except:

            return None




async def main():


    with open(
        INPUT,
        encoding="utf-8"
    ) as f:

        nodes=f.readlines()



    print(
        "检测节点:",
        len(nodes)
    )


    sem=asyncio.Semaphore(
        CONCURRENT
    )


    tasks=[

        check(
            n,
            sem
        )

        for n in nodes

    ]


    result=[]


    for r in asyncio.as_completed(tasks):

        data=await r

        if data:

            result.append(data)



    result.sort(
        key=lambda x:x[0]
    )


    print(
        "TCP可连接:",
        len(result)
    )


    # 保存测速排名

    with open(
        RANK,
        "w",
        encoding="utf-8"
    ) as f:


        for ms,node in result:

            f.write(
                f"{ms}ms {node}\n"
            )



    # 导入文件去掉速度前缀

    with open(
        OUTPUT,
        "w",
        encoding="utf-8"
    ) as f:


        for ms,node in result[:5000]:

            f.write(
                node+"\n"
            )


    print(
        "生成:",
        OUTPUT
    )



asyncio.run(main())