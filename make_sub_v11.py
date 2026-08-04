from pathlib import Path
import base64


INPUT = "clean_speed_top100.txt"


OUT = "my_subscription.txt"


BASE64_OUT = "my_subscription_base64.txt"



def main():

    nodes = Path(INPUT).read_text(
        encoding="utf-8",
        errors="ignore"
    ).splitlines()


    result=[]

    seen=set()


    for n in nodes:

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



    Path(OUT).write_text(
        "\n".join(result),
        encoding="utf-8"
    )


    b64=base64.b64encode(
        "\n".join(result).encode()
    ).decode()


    Path(BASE64_OUT).write_text(
        b64,
        encoding="utf-8"
    )


    print("节点数量:",len(result))

    print("生成:")
    print(OUT)
    print(BASE64_OUT)



if __name__=="__main__":
    main()