"""
机票预订系统 - Skills 实现
/flight_booking/skills/definitions.py
"""
import json
from typing import Dict, Any
from flight_booking.backend.skills.base import BaseSkill, SkillInput
from flight_booking.backend.flight_booking_api import flight_tools


class IntentAnalysisSkill(BaseSkill):
    """意图分析 Skill - 解析用户订票需求"""

    def __init__(self):
        super().__init__()
        self.id = "intent_analysis"
        self.name = "需求分析"
        self.description = "智能解析用户的订票需求，提取关键信息"
        self.icon = "🧠"

    def get_system_prompt(self) -> str:
        return """你是一位专业的机票预订助手，擅长理解用户的订票需求。

请从用户的描述中提取以下关键信息，并进行分析：

## 需要提取的信息：
1. **出发城市** - 用户从哪里出发
2. **到达城市** - 用户要去哪里
3. **出发日期** - 具体日期（如果说"明天"，请推算具体日期）
4. **偏好时间** - 用户偏好的出发时间段
5. **舱位等级** - 经济舱/商务舱/头等舱（默认经济舱）
6. **乘客人数** - 几位乘客（默认1位）
7. **特殊需求** - 如靠窗、餐食偏好等

## 输出格式：
### 📋 需求解析结果

**用户原始需求：** [复述用户需求]

**提取信息：**
| 项目 | 内容 |
|------|------|
| 出发城市 | xxx |
| 到达城市 | xxx |
| 出发日期 | YYYY-MM-DD |
| 偏好时间 | HH:MM |
| 舱位等级 | xxx |
| 乘客人数 | x人 |
| 特殊需求 | xxx |

**需求确认：** [确认理解是否正确]

**下一步：** 将为您查询符合条件的航班信息

---
【JSON数据】
```json
{
  "departure_city": "xxx",
  "arrival_city": "xxx", 
  "date": "YYYY-MM-DD",
  "preferred_time": "HH:MM",
  "cabin_class": "经济舱",
  "passenger_count": 1,
  "special_requests": []
}
```"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        return f"""当前日期：{today}
明天日期：{tomorrow}

用户订票需求：
{input_data.user_request}

请分析并提取用户的订票需求信息。"""


class FlightSearchSkill(BaseSkill):
    """航班查询 Skill - 搜索可用航班"""

    def __init__(self):
        super().__init__()
        self.id = "flight_search"
        self.name = "航班查询"
        self.description = "根据需求查询可用航班，展示航班信息"
        self.icon = "🔍"

    def get_system_prompt(self) -> str:
        return """你是一位专业的机票查询助手。

根据提供的航班查询结果，以清晰易读的方式展示给用户，并给出推荐。

## 输出格式：
### ✈️ 航班查询结果

**查询条件：** [出发地] → [目的地] | [日期] | [舱位]

**共找到 X 个航班：**

---
#### 🌟 推荐航班
[选出最符合用户时间偏好且性价比高的1-2个航班详细展示]

| 项目 | 信息 |
|------|------|
| 航班号 | XXX |
| 航空公司 | XXX |
| 出发时间 | XXX |
| 到达时间 | XXX |
| 飞行时长 | XXX |
| 机型 | XXX |
| 票价 | ¥XXX |
| 准点率 | XX% |
| 剩余座位 | XX |

**推荐理由：** [说明为什么推荐这个航班]

---
#### 📋 其他可选航班

[以简洁表格列出其他航班]

| 航班 | 起飞 | 到达 | 时长 | 票价 | 余票 |
|------|------|------|------|------|------|
| XXX | XX:XX | XX:XX | Xh | ¥XXX | XX |

---
**💡 建议：** [根据情况给出建议，如是否需要尽快预订等]

请确认选择哪个航班，我将为您进行下一步预订。"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context

        # 从上下文获取解析出的信息
        intent_data = context.get("intent_analysis_data", {})

        departure_city = intent_data.get("departure_city", "海口")
        arrival_city = intent_data.get("arrival_city", "北京")
        date = intent_data.get("date", "")
        preferred_time = intent_data.get("preferred_time", "10:00")
        cabin_class = intent_data.get("cabin_class", "经济舱")

        # 调用航班查询工具
        flights = flight_tools.search_flights(
            departure_city=departure_city,
            arrival_city=arrival_city,
            date=date,
            preferred_time=preferred_time,
            cabin_class=cabin_class
        )

        return f"""用户需求分析结果：
{context.get('intent_analysis', '')}

航班查询API返回结果：
```json
{json.dumps(flights, ensure_ascii=False, indent=2)}
```

用户偏好时间：{preferred_time}

请根据查询结果，为用户展示航班信息并给出推荐。特别注意用户偏好的是 {preferred_time} 左右的航班。"""


class PassengerInfoSkill(BaseSkill):
    """乘客信息 Skill - 收集乘客信息"""

    def __init__(self):
        super().__init__()
        self.id = "passenger_info"
        self.name = "乘客信息"
        self.description = "收集并确认乘客信息，准备预订"
        self.icon = "👤"

    def get_system_prompt(self) -> str:
        return """你是一位专业的机票预订助手，负责收集和确认乘客信息。

## 任务：
1. 为用户生成/确认乘客信息
2. 由于这是演示系统，使用模拟的乘客信息
3. 确认选定的航班信息

## 输出格式：
### 👤 乘客信息确认

**已选航班：**
- 航班号：XXX
- 航线：XXX → XXX
- 时间：XXX
- 票价：¥XXX/人

---
**乘客信息：**

| 序号 | 姓名 | 证件类型 | 证件号码 | 手机号 | 乘客类型 |
|------|------|----------|----------|--------|----------|
| 1 | XXX | 身份证 | XXX | XXX | 成人 |

---
**费用明细：**
- 机票费用：¥XXX × 1人 = ¥XXX
- 机建燃油：¥50 × 1人 = ¥50
- **应付总额：¥XXX**

---
**⚠️ 重要提示：**
1. 请仔细核对乘客信息，证件信息错误将无法登机
2. 请确保手机号正确，用于接收行程信息

**请确认以上信息无误，即将进入支付环节。**

---
【JSON数据】
```json
{
  "selected_flight": {...},
  "passengers": [...],
  "total_price": XXX
}
```"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context
        intent_data = context.get("intent_analysis_data", {})
        passenger_count = intent_data.get("passenger_count", 1)

        # 模拟乘客信息
        mock_passengers = [
            {
                "name": "张三",
                "id_type": "身份证",
                "id_number": "110101199001011234",
                "phone": "13800138001",
                "passenger_type": "成人"
            }
        ]

        # 设置乘客信息到工具
        flight_tools.set_passenger_info(mock_passengers)

        return f"""航班查询结果：
{context.get('flight_search', '')}

乘客数量：{passenger_count}人

模拟乘客信息（演示用）：
```json
{json.dumps(mock_passengers, ensure_ascii=False, indent=2)}
```

请确认乘客信息并展示费用明细。假设用户选择了推荐的第一个航班。"""


class PaymentSkill(BaseSkill):
    """支付处理 Skill - 处理支付流程"""

    def __init__(self):
        super().__init__()
        self.id = "payment"
        self.name = "支付处理"
        self.description = "处理订单支付，完成购票交易"
        self.icon = "💳"

    def get_system_prompt(self) -> str:
        return """你是一位专业的支付处理助手。

## 任务：
1. 展示支付方式选择
2. 模拟支付过程
3. 返回支付结果

## 输出格式：
### 💳 订单支付

**订单信息：**
- 订单金额：¥XXX
- 乘客：XXX
- 航班：XXX

---
**选择支付方式：**
- [x] 支付宝（推荐）
- [ ] 微信支付
- [ ] 银联卡

---
### ⏳ 支付处理中...

正在连接支付宝...
正在验证订单信息...
正在处理支付请求...

---
### ✅ 支付成功！

| 项目 | 信息 |
|------|------|
| 订单号 | TBXXXXXXXXXXXX |
| 支付金额 | ¥XXX |
| 支付方式 | 支付宝 |
| 支付时间 | XXXX-XX-XX XX:XX:XX |
| 支付状态 | ✅ 成功 |

**温馨提示：** 电子客票信息将在1分钟内发送至您的手机。

---
【JSON数据】
```json
{
  "order_id": "TBXXXX",
  "payment_status": "成功",
  "total_price": XXX
}
```"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context

        # 从上下文提取航班信息（简化处理，使用模拟数据）
        intent_data = context.get("intent_analysis_data", {})

        # 模拟支付
        mock_flight = {
            "flight_no": "HU7001",
            "airline": "海南航空",
            "departure_city": intent_data.get("departure_city", "海口"),
            "arrival_city": intent_data.get("arrival_city", "北京"),
            "departure_time": f"{intent_data.get('date', '')} {intent_data.get('preferred_time', '10:00')}",
            "arrival_time": f"{intent_data.get('date', '')} 13:30",
            "price": 1280,
            "cabin_class": "经济舱"
        }

        payment_result = flight_tools.process_payment(
            flight_info=mock_flight,
            payment_method="支付宝"
        )

        return f"""乘客信息确认：
{context.get('passenger_info', '')}

支付API返回结果：
```json
{json.dumps(payment_result, ensure_ascii=False, indent=2)}
```

请展示支付过程和结果。"""


class BookingResultSkill(BaseSkill):
    """订票结果 Skill - 展示最终订票结果"""

    def __init__(self):
        super().__init__()
        self.id = "booking_result"
        self.name = "订票结果"
        self.description = "生成电子客票，展示完整订票信息"
        self.icon = "🎫"

    def get_system_prompt(self) -> str:
        return """你是一位专业的机票预订助手，负责生成最终的订票确认信息。

## 任务：
生成完整的电子客票信息和行程单

## 输出格式：
### 🎫 电子客票 - 预订成功！

```
╔══════════════════════════════════════════════════════════════╗
║                      ✈️ 电子客票行程单                        ║
╠══════════════════════════════════════════════════════════════╣
║  订单号：TBXXXXXXXXXXXX                                       ║
║  票号：784-XXXXXXXXXX                                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  👤 乘客：XXX          证件：XXXXXXXXXXXXXXXXXX               ║
║                                                              ║
║  ┌─────────────────────────────────────────────────────────┐║
║  │  XXXX    ✈️ XXX航空 XXXXX    经济舱                     │║
║  │                                                         │║
║  │  [出发城市]              ───────────►        [到达城市]  │║
║  │  XX:XX                                          XX:XX   │║
║  │  XXX机场                                     XXX机场    │║
║  │                                                         │║
║  │  📅 XXXX年XX月XX日                                      │║
║  └─────────────────────────────────────────────────────────┘║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  💰 票价：¥XXXX（含机建燃油）                                  ║
║  ✅ 支付状态：已支付                                          ║
╚══════════════════════════════════════════════════════════════╝
```

---
### 📱 温馨提示

1. **值机提醒：** 起飞前24小时可通过航空公司APP或官网办理网上值机
2. **登机时间：** 请于起飞前90分钟到达机场办理乘机手续
3. **行李规定：** 经济舱免费托运20KG行李，手提行李不超过5KG
4. **证件要求：** 请携带有效身份证件原件

### 📞 客服热线
如需改签、退票或其他帮助，请拨打：400-XXX-XXXX

---
**感谢您使用智能机票预订系统！祝您旅途愉快！** ✈️🌟"""

    def get_user_prompt(self, input_data: SkillInput) -> str:
        context = input_data.context

        # 获取最新订单
        if flight_tools.orders:
            order_id = list(flight_tools.orders.keys())[-1]
            booking_result = flight_tools.get_booking_result(order_id)
        else:
            booking_result = {"success": False, "message": "未找到订单"}

        return f"""支付结果：
{context.get('payment', '')}

订单详情API返回：
```json
{json.dumps(booking_result, ensure_ascii=False, indent=2)}
```

请生成完整的电子客票行程单。"""


# ============ Skill 注册中心 ============

class SkillRegistry:
    """Skill 注册中心"""

    def __init__(self):
        self._skills = {}
        self._workflow_order = []
        self._register_default_skills()

    def _register_default_skills(self):
        """注册默认Skills"""
        skills = [
            IntentAnalysisSkill(),
            FlightSearchSkill(),
            PassengerInfoSkill(),
            PaymentSkill(),
            BookingResultSkill()
        ]
        for skill in skills:
            self.register(skill)

        self._workflow_order = [s.id for s in skills]

    def register(self, skill: BaseSkill):
        self._skills[skill.id] = skill

    def get(self, skill_id: str) -> BaseSkill:
        return self._skills.get(skill_id)

    def get_all(self) -> list:
        return list(self._skills.values())

    def get_workflow_order(self) -> list:
        return self._workflow_order


skill_registry = SkillRegistry()
