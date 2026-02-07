"""
机票预订系统 - 模拟航班API工具
/flight_booking/tools/flight_api.py
"""
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
import json


@dataclass
class Flight:
    """航班信息"""
    flight_no: str
    airline: str
    departure_city: str
    arrival_city: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    duration: str
    price: int
    cabin_class: str
    seats_available: int
    aircraft: str
    on_time_rate: str


@dataclass
class Passenger:
    """乘客信息"""
    name: str
    id_type: str  # 身份证/护照
    id_number: str
    phone: str
    passenger_type: str = "成人"  # 成人/儿童/婴儿


@dataclass
class BookingOrder:
    """订单信息"""
    order_id: str
    flight: Flight
    passengers: List[Passenger]
    total_price: int
    status: str
    created_at: str
    payment_status: str = "待支付"
    payment_method: str = ""
    ticket_numbers: List[str] = field(default_factory=list)


class FlightAPITools:
    """
    模拟航班API工具集
    实际项目中这些会调用真实的航空公司API
    """

    # 模拟数据
    AIRLINES = [
        ("CA", "中国国航", "Boeing 737-800"),
        ("MU", "东方航空", "Airbus A320"),
        ("CZ", "南方航空", "Boeing 787"),
        ("HU", "海南航空", "Airbus A330"),
        ("3U", "四川航空", "Airbus A321"),
        ("ZH", "深圳航空", "Boeing 737 MAX"),
    ]

    AIRPORTS = {
        "海口": ("HAK", "海口美兰国际机场"),
        "北京": ("PEK", "北京首都国际机场"),
        "上海": ("SHA", "上海虹桥国际机场"),
        "广州": ("CAN", "广州白云国际机场"),
        "深圳": ("SZX", "深圳宝安国际机场"),
        "成都": ("CTU", "成都双流国际机场"),
        "杭州": ("HGH", "杭州萧山国际机场"),
        "西安": ("XIY", "西安咸阳国际机场"),
        "三亚": ("SYX", "三亚凤凰国际机场"),
    }

    def __init__(self):
        self.orders: Dict[str, BookingOrder] = {}
        self.current_passengers: List[Passenger] = []

    def search_flights(
            self,
            departure_city: str,
            arrival_city: str,
            date: str,
            preferred_time: Optional[str] = None,
            cabin_class: str = "经济舱"
    ) -> List[Dict]:
        """
        搜索航班

        Args:
            departure_city: 出发城市
            arrival_city: 到达城市
            date: 日期 (YYYY-MM-DD)
            preferred_time: 偏好时间 (如 "10:00")
            cabin_class: 舱位等级

        Returns:
            航班列表
        """
        dep_airport = self.AIRPORTS.get(departure_city, ("UNK", f"{departure_city}机场"))
        arr_airport = self.AIRPORTS.get(arrival_city, ("UNK", f"{arrival_city}机场"))

        flights = []

        # 生成6-10个模拟航班
        num_flights = random.randint(6, 10)
        base_times = ["06:30", "08:00", "09:30", "10:00", "11:30", "13:00", "14:30", "16:00", "18:00", "20:30"]

        for i in range(num_flights):
            airline_code, airline_name, aircraft = random.choice(self.AIRLINES)
            flight_num = f"{airline_code}{random.randint(1000, 9999)}"

            # 出发时间
            dep_time = base_times[i % len(base_times)]

            # 飞行时长 (海口到北京约3-3.5小时)
            duration_hours = random.randint(2, 4)
            duration_mins = random.choice([0, 15, 30, 45])
            duration = f"{duration_hours}小时{duration_mins}分钟" if duration_mins else f"{duration_hours}小时"

            # 计算到达时间
            dep_dt = datetime.strptime(dep_time, "%H:%M")
            arr_dt = dep_dt + timedelta(hours=duration_hours, minutes=duration_mins)
            arr_time = arr_dt.strftime("%H:%M")

            # 价格 (根据时间和舱位)
            base_price = random.randint(800, 2000)
            if cabin_class == "商务舱":
                base_price *= 3
            elif cabin_class == "头等舱":
                base_price *= 5

            # 如果是偏好时间附近，价格略高
            if preferred_time:
                pref_hour = int(preferred_time.split(":")[0])
                dep_hour = int(dep_time.split(":")[0])
                if abs(pref_hour - dep_hour) <= 1:
                    base_price = int(base_price * 1.1)

            flight = Flight(
                flight_no=flight_num,
                airline=airline_name,
                departure_city=departure_city,
                arrival_city=arrival_city,
                departure_airport=f"{dep_airport[1]} ({dep_airport[0]})",
                arrival_airport=f"{arr_airport[1]} ({arr_airport[0]})",
                departure_time=f"{date} {dep_time}",
                arrival_time=f"{date} {arr_time}" if arr_dt.hour >= dep_dt.hour else f"{date} {arr_time}(+1)",
                duration=duration,
                price=base_price,
                cabin_class=cabin_class,
                seats_available=random.randint(1, 50),
                aircraft=aircraft,
                on_time_rate=f"{random.randint(85, 99)}%"
            )
            flights.append(asdict(flight))

        # 按出发时间排序
        flights.sort(key=lambda x: x["departure_time"])

        # 如果有偏好时间，把最接近的排在前面
        if preferred_time:
            pref_hour = int(preferred_time.split(":")[0])
            flights.sort(key=lambda x: abs(int(x["departure_time"].split(" ")[1].split(":")[0]) - pref_hour))

        return flights

    def set_passenger_info(self, passengers: List[Dict]) -> Dict:
        """
        设置乘客信息

        Args:
            passengers: 乘客信息列表

        Returns:
            确认信息
        """
        self.current_passengers = []
        for p in passengers:
            passenger = Passenger(
                name=p.get("name", ""),
                id_type=p.get("id_type", "身份证"),
                id_number=p.get("id_number", ""),
                phone=p.get("phone", ""),
                passenger_type=p.get("passenger_type", "成人")
            )
            self.current_passengers.append(passenger)

        return {
            "success": True,
            "message": f"已添加 {len(self.current_passengers)} 位乘客信息",
            "passengers": [asdict(p) for p in self.current_passengers]
        }

    def process_payment(
            self,
            flight_info: Dict,
            payment_method: str = "支付宝"
    ) -> Dict:
        """
        处理支付

        Args:
            flight_info: 航班信息
            payment_method: 支付方式

        Returns:
            支付结果
        """
        if not self.current_passengers:
            return {
                "success": False,
                "message": "请先添加乘客信息"
            }

        # 计算总价
        total_price = flight_info.get("price", 0) * len(self.current_passengers)

        # 模拟支付过程 (实际会调用支付宝/微信支付API)
        order_id = f"TB{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

        # 生成票号
        ticket_numbers = []
        for i, p in enumerate(self.current_passengers):
            ticket_no = f"784-{random.randint(1000000000, 9999999999)}"
            ticket_numbers.append(ticket_no)

        # 创建订单
        flight = Flight(**flight_info) if isinstance(flight_info, dict) else flight_info

        order = BookingOrder(
            order_id=order_id,
            flight=flight,
            passengers=self.current_passengers,
            total_price=total_price,
            status="已出票",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            payment_status="支付成功",
            payment_method=payment_method,
            ticket_numbers=ticket_numbers
        )

        self.orders[order_id] = order

        return {
            "success": True,
            "order_id": order_id,
            "total_price": total_price,
            "payment_method": payment_method,
            "payment_status": "支付成功",
            "message": f"支付成功！订单号: {order_id}"
        }

    def get_booking_result(self, order_id: str) -> Dict:
        """
        获取订票结果

        Args:
            order_id: 订单ID

        Returns:
            订票详情
        """
        order = self.orders.get(order_id)
        if not order:
            return {
                "success": False,
                "message": f"订单 {order_id} 不存在"
            }

        return {
            "success": True,
            "order": {
                "order_id": order.order_id,
                "status": order.status,
                "flight": asdict(order.flight) if isinstance(order.flight, Flight) else order.flight,
                "passengers": [
                    {
                        **asdict(p),
                        "ticket_number": order.ticket_numbers[i] if i < len(order.ticket_numbers) else ""
                    }
                    for i, p in enumerate(order.passengers)
                ],
                "total_price": order.total_price,
                "payment_status": order.payment_status,
                "payment_method": order.payment_method,
                "created_at": order.created_at
            }
        }


# 全局工具实例
flight_tools = FlightAPITools()
