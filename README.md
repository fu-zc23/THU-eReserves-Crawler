# THU-eReserves-Crawler

从清华大学电子教学参考书服务平台下载电子教参，将指定列表中的书籍以 pdf 格式保存到本地。

**该项目仅供个人学习参考，仅限在教学科研范围内合理使用。所下载内容严禁传播、营利，使用完毕请及时删除。请自觉遵守相关法律法规，一切法律责任由用户自行承担。**

## 使用说明

### 1. 配置 `config.json` 文件

登录[清华大学电子教学参考书服务平台](https://ereserves.lib.tsinghua.edu.cn/)，进入需要下载的书籍主页。

按 `F12` 打开开发者工具，切换到 “网络” 标签页并刷新页面。

找到 `access` 请求，将请求标头中的 `Jcclient` 字段复制到 `config.json` 文件的对应位置。

再将 `Referer` 字段中 `bookDetail/` 之后的编号复制到 `config.json` 中的 `bookList` 中。该字段支持多本书籍下载，用逗号分隔即可。

![bookDetail](/img/bookDetail.jpg)

### 2. 运行程序

确保安装所有依赖后运行该程序，注意 `fpdf` 需要安装 `fpdf2`。

```
python THU-eReserves-Crawler.py
```

如果某页下载失败，会在 pdf 文件中用空白页代替。最后文件 `{title}.pdf` 会保存到当前目录，原书名中的非法字符会被替换为 `.`。

### 3. 注意事项

部分书籍的资源位于 “文泉学堂” 、 “可知” 等平台，该程序会给出提示并终止，无法下载。

一段时间后可能因 `jcclient` 更新而无法运行，请及时更新 `config.json`。

## LISENCE

本仓库的内容采用 [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/) 许可协议。您可以自由使用、修改、分发和创作衍生作品，但只能用于非商业目的，并署名原作者，以相同的授权协议共享衍生作品。

如果您认为文档的部分内容侵犯了您的合法权益，请联系项目维护者，我们会尽快删除相关内容。
