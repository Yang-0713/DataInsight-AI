# 示例数据

`examples/datasets/retail_sales.csv` 是为 DataInsight AI 演示流程准备的完全合成零售数据，不包含真实个人或企业信息。

## 数据规模

- 40 条记录
- 11 个字段
- 2 个缺失单元格
- 多个数值、分类和日期字段
- 包含少量刻意设置的极端记录，便于观察异常检测结果

## 字段说明

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sample_id` | 文本 | 合成样本编号 |
| `date` | 日期 | 汇总日期 |
| `region` | 分类 | East、North、South、West |
| `category` | 分类 | 商品类别 |
| `channel` | 分类 | Online 或 Store |
| `orders` | 数值 | 订单数量 |
| `units` | 数值 | 商品件数 |
| `revenue` | 数值 | 合成销售收入 |
| `cost` | 数值 | 合成销售成本 |
| `discount_rate` | 数值 | 折扣比例 |
| `satisfaction_score` | 数值 | 1–5 的合成满意度 |

金额字段没有指定真实货币单位，仅用于展示统计分析。

## 推荐体验流程

1. 注册并登录 DataInsight AI。
2. 在“数据集”页面上传 `retail_sales.csv`。
3. 运行自动 EDA，检查字段类型、缺失值、分布和时间趋势。
4. 在机器学习页面选择 `orders`、`units`、`revenue`、`cost`、`discount_rate` 和 `satisfaction_score`。
5. 使用默认异常比例运行 PCA、Isolation Forest 和 LOF。
6. 配置 AI 服务后，询问“哪些异常样本值得优先调查？”。
7. 生成并下载 HTML 综合报告。

示例数据以 MIT License 随项目一起发布，可以自由用于测试、演示和文档。
