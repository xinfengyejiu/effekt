## 9月17日（周四）

**1. 页面来回切换后数据错乱、首次进入数据刷不出来**
你反馈"第一次进来和这里来回切换，对应的就会变；第一次进来数据多了都刷不出来，要不要翻页"。付静回复"不翻页吧，翻页的话选中的内容看不全，倒是可以优化下速度看看"。

![页面切换数据错乱截图1](https://aka.doubaocdn.com/s/BnAvzXbM7p)
![页面切换数据错乱截图2](https://aka.doubaocdn.com/s/hKCbG0Wgsg)
![页面切换数据错乱截图3](https://aka.doubaocdn.com/s/70DELzFU2b)

**2. 多个面单刷不出来**
你反馈"多个面单的时候，这个也刷不出来嘛"。付静回复"这里我改了"，你请她提代码，并补充"这里的好多功能感觉都不对嘛"。

![多个面单刷不出来截图](https://aka.doubaocdn.com/s/3jWXgn2mmp)

**3. Table 切换后数据被置空、面单加载不出来**
你反馈"这个 table 切换后，数据就被置空了，而且面单也加载不出来，只能手动刷新"。付静回复"已经改了，新的版本还没提交"。

**4. 发布/部署明显变慢**
你反馈"还没有发好""都是在装新东西，上线估计也相应会慢很多"，并截图显示发布耗时半小时。

![发布慢截图1](https://aka.doubaocdn.com/s/gFXnEHK6lD)
![发布慢截图2](https://aka.doubaocdn.com/s/Vmy3OUgGjS)
![发布耗时半小时截图](https://aka.doubaocdn.com/s/BYWXJJUTaH)

---

## 9月16日（周三）

**5. 运费报价失败（calculate-freight 批量 400）**
客户端待付款订单页 `calculate-freight` 接口批量 400，亚马逊订单 SKU 映射关系不存在（`HEDH-ZZZ-0730-2` 待映射）；运费报价发给捷帆 API 试算被拒，定位到仓库 19（纽约仓 NY02）捷帆账号 ZKS，捷帆报价走 SKU 计价模式（`useSkuPricing=true` 硬编码），重量/体积参数不传。你补充了关键截图并给出排查编号 `Q20260916094823412JLY`。

---

## 9月15日（周二）

**6. 历史订单显示"待计算"、运费为 0 可提交**
你反馈"之前的历史订单，这里显示的都成待计算了""现在运费都是 0，然后可以直接提交订单了么"。

![历史订单待计算截图](https://aka.doubaocdn.com/s/B8OouWegav)
![运费为0订单截图](https://aka.doubaocdn.com/s/07rdOzYNKv)

**7. FAQ 插件问题：序号不显示、保存后需手动刷新**
你反馈"这个插件应该有问题，默认序号展示不出来，保存后关闭弹框到列表页面只能手动刷新"。

![FAQ新建页面问题截图](https://aka.doubaocdn.com/s/JBUKtjFyjv)

**8. 图片预览关闭后悬浮框残留**
你反馈"图片预览，点击×后，左边还有悬浮预览框，还得点击才消失"。

![图片预览悬浮框问题截图](https://aka.doubaocdn.com/s/bmUDO6H1AC)

**9. 公司简介页"首页"导航太靠左**
你反馈"这个是不是太靠近左边了"。

![首页导航位置截图](https://aka.doubaocdn.com/s/VJsnpPW2il)

**10. 联系邮箱超链点不动**
你反馈"邮箱这个超链确实点不动"。

![邮箱超链截图](https://aka.doubaocdn.com/s/2oipUljWLm)

**11. SKU 映射消失的提醒按钮点不动**
你反馈"如果 sku 映射消失，给的提醒在页面上开不到，就是点不动按钮"，付静回复表情确认（代码已提交）。

![SKU映射提醒按钮问题截图](https://aka.doubaocdn.com/s/1M5Ab6pMcw)
