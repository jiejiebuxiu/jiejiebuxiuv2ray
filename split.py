SS="ss_nodes.txt"
VLESS="vless_nodes.txt"
TROJAN="trojan_nodes.txt"


with open("best_nodes.txt","r",encoding="utf-8") as f:
    nodes=f.readlines()


ss=[]
vless=[]
trojan=[]


for n in nodes:

    n=n.strip()

    if n.startswith("ss://"):
        ss.append(n)

    elif n.startswith("vless://"):
        vless.append(n)

    elif n.startswith("trojan://"):
        trojan.append(n)



with open(SS,"w",encoding="utf-8") as f:
    f.write("\n".join(ss))


with open(VLESS,"w",encoding="utf-8") as f:
    f.write("\n".join(vless))


with open(TROJAN,"w",encoding="utf-8") as f:
    f.write("\n".join(trojan))


print("SS:",len(ss))
print("VLESS:",len(vless))
print("Trojan:",len(trojan))