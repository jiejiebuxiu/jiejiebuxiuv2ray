import requests
import base64
import re


SOURCES = [

    # GitHub FreeNodes
    "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/nodefree.txt",

    "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/v2rayshare.txt",

    "https://raw.githubusercontent.com/Barabama/FreeNodes/main/nodes/yudou66.txt",


    # ebrasha
    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/V2Ray-Config-By-EbraSha-All-Type.txt",

    "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/all_extracted_configs.txt",

]


def get_url(url):

    try:

        r=requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent":"Mozilla/5.0"
            }
        )

        return r.text

    except Exception as e:

        print("失败:",url)

        return ""



def decode_base64(text):

    result=[]


    try:

        raw=base64.b64decode(
            text+"==="
        ).decode(
            errors="ignore"
        )

        result.append(raw)

    except:

        pass


    return "\n".join(result)



def extract(text):

    nodes=[]


    # 先解base64

    text += "\n" + decode_base64(text)



    pattern=r"""

    (

    vmess://[^\s]+

    |

    vless://[^\s]+

    |

    trojan://[^\s]+

    |

    ss://[^\s]+

    )

    """


    result=re.findall(
        pattern,
        text,
        re.X
    )


    nodes.extend(result)


    return nodes



def main():


    all_nodes=[]


    print("[+] 开始抓取...")


    for url in SOURCES:


        print(url)


        txt=get_url(url)


        nodes=extract(txt)


        print(
            "发现:",
            len(nodes)
        )


        all_nodes += nodes



    print(
        "[+] 总节点:",
        len(all_nodes)
    )


    # 去重

    all_nodes=list(
        set(all_nodes)
    )


    print(
        "[+] 去重后:",
        len(all_nodes)
    )



    with open(
        "subscribe.txt",
        "w",
        encoding="utf-8"
    ) as f:


        for n in all_nodes:

            f.write(
                n+"\n"
            )


    print(
        "[+] 完成 subscribe.txt"
    )



if __name__=="__main__":

    main()