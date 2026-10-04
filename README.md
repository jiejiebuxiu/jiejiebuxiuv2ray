# 自动检测的免费节点订阅

在原有节点仓库里增加 `auto_sub/` 和 GitHub Actions。原来的文件和 Windows 脚本保留；新订阅统一放在 `output/`。

## 两个固定订阅地址

只有第一次工作流成功后，这些地址才会有内容。

- v2rayN：`https://raw.githubusercontent.com/jiejiebuxiu/jiejiebuxiuv2ray/main/output/v2ray.txt`
- Clash Verge（Mihomo 内核）：`https://raw.githubusercontent.com/jiejiebuxiu/jiejiebuxiuv2ray/main/output/clash.yaml`
- 检测报告：`https://github.com/jiejiebuxiu/jiejiebuxiuv2ray/blob/main/output/report.json`
- 自动更新运行记录：`https://github.com/jiejiebuxiu/jiejiebuxiuv2ray/actions/workflows/update-subscription.yml`

v2rayN：订阅分组 → 添加订阅 → 粘贴 v2rayN 地址 → 更新订阅 → 测试真连接/速度。

Clash Verge：配置/订阅 → 新建远程配置 → 粘贴 Clash 地址 → 导入并启用 → 代理组选择“自动选择”或具体节点。界面名称会随版本变化。

Clash 配置使用 Mihomo 原生代理集合读取同一份 Base64 节点文件，因此需要能下载两个 raw.githubusercontent.com 地址。配置内容是 JSON（也是合法 YAML），支持 Mihomo。代理集合每 4 小时刷新，本地每 5 分钟再测 HTTPS 延迟。客户端更新订阅不会立即启动服务器测速，而是读取最近一次成功结果。

## 筛选方法

1. 获取 settings.json 中的 5 个公开订阅来源，提取 SS、VMess、VLESS、Trojan、Hysteria2 链接。
2. 忽略名称进行去重，过滤格式错误、私有地址、明确要求跳过 TLS 验证的节点。
3. 每轮检测最多 600 个节点；优先复查仍在来源中的上次成功节点，其余轮换抽样。不是对全部来源进行无限量测试。
4. 使用固定版本 Mihomo 解析节点，通过代理访问 HTTPS，保留延迟 ≤1200ms 的节点。
5. 对其中延迟最小的最多 80 个节点依次进行 1 MiB HTTPS 下载；证书必须通过验证，HTTP 200，完整收到 1 MiB，包含握手时间的速度 ≥128 KiB/s。
6. 按短下载速度降序、延迟升序，发布最多 40 个节点，两个客户端使用同一批结果。

这是短下载样本，不是持续带宽承诺。检测发生在 GitHub runner，报告的 location 是 runner 标识，不是地理定位；不能据此认定中国大陆或你当前网络能连接。仍需客户端本地复测。

## 更新与失败保护

工作流计划每 4 小时运行：北京时间 00:23、04:23、08:23、12:23、16:23、20:23；Actions 可能延迟。也可打开 Actions → Update tested subscriptions → Run workflow 手动运行。修改 auto_sub/ 会触发一次更新。

没有通过实际下载的节点时，任务失败，日志会显示原因，不覆盖上次成功结果。保留结果可能已过期，请检查 report.json 的 tested_at_utc（UTC 时间）和 Actions 最近一次运行状态。没有任何成功结果时不会发布空订阅，也不会把只通端口的节点当成可用节点。

公开仓库长期无活动（60 天）时 GitHub 可能禁用定时任务。需留意运行状态，禁用后重新启用。使用 GitHub 提供的标准公开仓库 runner；费用与可用性以你的 GitHub 账户政策为准，无需付费测速服务。

## 调整来源和标准

编辑 auto_sub/settings.json：sources 为 HTTPS 明文或 Base64 URI 订阅；max_delay_ms、min_speed_kib_s、max_candidates、max_download_tests、max_output 控制筛选与运行量。修改 download_bytes 时也要修改 download_url 的 bytes 参数。

本地测试（Linux amd64，需要 Python 3.11+ 和 curl）：

```sh
python auto_sub/download_core.py
python -m unittest discover -s auto_sub -p 'test_*.py' -v
python auto_sub/update.py
```

Mihomo 固定 v1.19.32，安装时校验官方 release 的 SHA-256。测试控制接口只监听 127.0.0.1，使用随机密钥；测试流量强制走选中节点。没有安装脚本来自节点提供者，也不将节点提交给第三方转换服务。

公开免费节点由第三方控制，可能随时失效；不要把自己的付费订阅或私密节点添加到这个公开仓库。

参考：
- https://wiki.metacubex.one/en/config/proxy-providers/content/
- https://wiki.metacubex.one/en/api/
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
