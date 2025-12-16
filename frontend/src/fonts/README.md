# 字体文件目录

请将您的字体文件放在此目录下。

## 支持的字体格式

- `.woff2` (推荐，体积最小，兼容性最好)
- `.woff` (备选)
- `.ttf` (备选)
- `.otf` (备选)

## 字体文件命名规范

请按照以下命名规范放置字体文件：

- `CustomFont-Regular.woff2` - 常规字重 (400)
- `CustomFont-Medium.woff2` - 中等字重 (500)
- `CustomFont-SemiBold.woff2` - 半粗字重 (600)
- `CustomFont-Bold.woff2` - 粗体字重 (700)

## 使用说明

1. 将字体文件复制到此目录
2. 如果您的字体文件名不同，请修改 `src/styles/global.css` 中的 `@font-face` 声明
3. 如果您的字体名称不是 "CustomFont"，请修改 `global.css` 中的 `font-family` 名称

## 示例

如果您使用的是 "PingFang SC" 字体，文件名为 `PingFangSC-Regular.woff2`：

1. 将文件放在此目录：`PingFangSC-Regular.woff2`
2. 修改 `src/styles/global.css`：
   - 将 `font-family: "CustomFont"` 改为 `font-family: "PingFang SC"`
   - 将 `url("../fonts/CustomFont-Regular.woff2")` 改为 `url("../fonts/PingFangSC-Regular.woff2")`

