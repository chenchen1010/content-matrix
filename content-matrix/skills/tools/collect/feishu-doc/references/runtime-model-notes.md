# Runtime Model Notes

## 为什么普通 DOM 抓取经常不完整

飞书新文档页面里，很多正文不是一次性全部写进最终 HTML 的。

- 页面会按滚动位置懒加载内容。
- 看到的排版节点，很多只是“渲染结果”，不是原始文档结构。
- 有些块在视口外时，DOM 里根本还没真正渲染出来。

这就是为什么只抓 `document.body.innerText`、选中复制，或者只提取可见 DOM，常常会出现“只有标题、摘要、前几段”的情况。

## 为什么运行时块模型更可靠

飞书页面运行时里，通常会保留一份更完整的文档树。这个技能优先读取：

```js
window.PageMain?.blockManager?.rootBlockModel
```

这份数据更接近“文档原始结构”，里面能拿到：

- 标题和段落
- 多级标题
- 引用
- 列表和待办
- 链接
- 图片、附件等块信息

所以它比直接抓 DOM 更容易拿到完整内容。

## 当前脚本的策略

1. 先连接到已经登录飞书的 Chrome。
2. 打开文档后滚动页面，尽量触发飞书自身的懒加载。
3. 优先读取 `rootBlockModel`。
4. 把块结构手动转成 Markdown。
5. 发现图片时，用当前登录态里的 cookies 去下载原图到本地。
6. 如果运行时模型拿不到，再退回到 DOM 提取。

## 关键全局对象

- `window.PageMain`
- `window.PageMain.blockManager`
- `window.PageMain.blockManager.rootBlockModel`
- `window.globalConfig`

其中 `window.globalConfig` 里通常能拿到飞书当前环境下的接口域名，用来拼接图片下载地址。

## 适用范围

这套方法对新版飞书 `docx`、`wiki` 页面最有效。

如果目标是特别老的文档页面，或者页面结构已经被飞书大改，可能要再补新的兼容逻辑。
