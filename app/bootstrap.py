from __future__ import annotations

import json
import random
from datetime import date, datetime, timedelta
from pathlib import Path

from sqlalchemy import (
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    create_engine,
    inspect,
)

from app.config import PROJECT_ROOT, get_settings


DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


def _dt(day: date, hour: int = 12) -> datetime:
    return datetime(day.year, day.month, day.day, hour, 0, 0)


def build_sample_database() -> Path | str:
    settings = get_settings()
    write_metadata_files(DATA_DIR)
    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        if db_path.exists():
            return db_path
    else:
        db_path = settings.database_url.split("@")[-1]

    engine = create_engine(settings.database_url, future=True)
    metadata = MetaData()

    channels = Table(
        "channels",
        metadata,
        Column("channel_id", Integer, primary_key=True),
        Column("channel_name", String, nullable=False),
        Column("channel_type", String, nullable=False),
    )
    users = Table(
        "users",
        metadata,
        Column("user_id", Integer, primary_key=True),
        Column("register_date", DateTime, nullable=False),
        Column("region", String, nullable=False),
        Column("channel_id", Integer, ForeignKey("channels.channel_id")),
    )
    products = Table(
        "products",
        metadata,
        Column("product_id", Integer, primary_key=True),
        Column("product_name", String, nullable=False),
        Column("category", String, nullable=False),
        Column("unit_price", Float, nullable=False),
    )
    orders = Table(
        "orders",
        metadata,
        Column("order_id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.user_id")),
        Column("product_id", Integer, ForeignKey("products.product_id")),
        Column("channel_id", Integer, ForeignKey("channels.channel_id")),
        Column("order_date", DateTime, nullable=False),
        Column("paid_at", DateTime, nullable=False),
        Column("status", String, nullable=False),
        Column("quantity", Integer, nullable=False),
        Column("pay_amount", Float, nullable=False),
    )
    order_items = Table(
        "order_items",
        metadata,
        Column("item_id", Integer, primary_key=True),
        Column("order_id", Integer, ForeignKey("orders.order_id")),
        Column("product_id", Integer, ForeignKey("products.product_id")),
        Column("quantity", Integer, nullable=False),
        Column("item_amount", Float, nullable=False),
    )
    user_events = Table(
        "user_events",
        metadata,
        Column("event_id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.user_id")),
        Column("event_name", String, nullable=False),
        Column("event_time", DateTime, nullable=False),
        Column("page", String, nullable=False),
    )

    inspector = inspect(engine)
    if "orders" in inspector.get_table_names():
        return db_path

    metadata.create_all(engine)

    rng = random.Random(42)
    channel_rows = [
        {"channel_id": 1, "channel_name": "Organic Search", "channel_type": "search"},
        {"channel_id": 2, "channel_name": "Paid Ads", "channel_type": "paid"},
        {"channel_id": 3, "channel_name": "Direct", "channel_type": "direct"},
        {"channel_id": 4, "channel_name": "Referral", "channel_type": "referral"},
    ]
    category_rows = ["Home", "Fashion", "Electronics", "Beauty", "Food"]
    product_rows = []
    for idx in range(1, 31):
        category = rng.choice(category_rows)
        product_rows.append(
            {
                "product_id": idx,
                "product_name": f"{category} Item {idx:02d}",
                "category": category,
                "unit_price": round(rng.uniform(19, 999), 2),
            }
        )

    start = date(2026, 4, 1)
    end = date(2026, 7, 31)
    days = (end - start).days + 1
    user_rows = []
    for uid in range(1, 801):
        reg_day = start + timedelta(days=rng.randrange(days))
        user_rows.append(
            {
                "user_id": uid,
                "register_date": _dt(reg_day, rng.randint(8, 20)),
                "region": rng.choice(["East China", "South China", "North China", "West China"]),
                "channel_id": rng.choice([1, 2, 3, 4]),
            }
        )

    order_rows = []
    item_rows = []
    event_rows = []
    order_id = 1
    item_id = 1
    event_id = 1
    for _ in range(2400):
        user = rng.choice(user_rows)
        product = rng.choice(product_rows)
        order_day = start + timedelta(days=rng.randrange(days))
        qty = rng.randint(1, 5)
        pay_amount = round(product["unit_price"] * qty * rng.uniform(0.85, 1.0), 2)
        status = rng.choices(["paid", "paid", "paid", "refunded", "cancelled"], weights=[65, 20, 5, 6, 4])[0]
        paid_at = _dt(order_day, rng.randint(9, 21))
        order_rows.append(
            {
                "order_id": order_id,
                "user_id": user["user_id"],
                "product_id": product["product_id"],
                "channel_id": user["channel_id"],
                "order_date": _dt(order_day, rng.randint(8, 20)),
                "paid_at": paid_at,
                "status": status,
                "quantity": qty,
                "pay_amount": pay_amount if status == "paid" else 0.0,
            }
        )
        item_rows.append(
            {
                "item_id": item_id,
                "order_id": order_id,
                "product_id": product["product_id"],
                "quantity": qty,
                "item_amount": pay_amount,
            }
        )
        item_id += 1
        order_id += 1

        if rng.random() < 0.75:
            event_rows.append(
                {
                    "event_id": event_id,
                    "user_id": user["user_id"],
                    "event_name": rng.choice(["view", "click", "add_to_cart", "search"]),
                    "event_time": _dt(order_day, rng.randint(7, 23)),
                    "page": rng.choice(["home", "search", "detail", "cart", "checkout"]),
                }
            )
            event_id += 1

    with engine.begin() as conn:
        conn.execute(channels.insert(), channel_rows)
        conn.execute(metadata.tables["products"].insert(), product_rows)
        conn.execute(metadata.tables["users"].insert(), user_rows)
        conn.execute(metadata.tables["orders"].insert(), order_rows)
        conn.execute(metadata.tables["order_items"].insert(), item_rows)
        conn.execute(metadata.tables["user_events"].insert(), event_rows)

    return db_path


def write_metadata_files(output_dir: Path) -> None:
    schema = {
        "users": {
            "description": "用户基础信息表",
            "primary_key": "user_id",
            "columns": {
                "user_id": "用户ID",
                "register_date": "注册时间",
                "region": "所属区域",
                "channel_id": "来源渠道ID",
            },
            "joins": {"channel_id": "channels.channel_id"},
        },
        "orders": {
            "description": "订单主表",
            "primary_key": "order_id",
            "columns": {
                "order_id": "订单ID",
                "user_id": "用户ID",
                "product_id": "商品ID",
                "channel_id": "渠道ID",
                "order_date": "下单时间",
                "paid_at": "支付时间",
                "status": "订单状态",
                "quantity": "件数",
                "pay_amount": "支付金额",
            },
            "joins": {
                "user_id": "users.user_id",
                "product_id": "products.product_id",
                "channel_id": "channels.channel_id",
            },
        },
        "products": {
            "description": "商品维表",
            "primary_key": "product_id",
            "columns": {
                "product_id": "商品ID",
                "product_name": "商品名称",
                "category": "商品品类",
                "unit_price": "商品单价",
            },
        },
        "channels": {
            "description": "渠道维表",
            "primary_key": "channel_id",
            "columns": {
                "channel_id": "渠道ID",
                "channel_name": "渠道名称",
                "channel_type": "渠道类型",
            },
        },
        "order_items": {
            "description": "订单明细表",
            "primary_key": "item_id",
            "columns": {
                "item_id": "明细ID",
                "order_id": "订单ID",
                "product_id": "商品ID",
                "quantity": "数量",
                "item_amount": "明细金额",
            },
        },
        "user_events": {
            "description": "用户行为事件表",
            "primary_key": "event_id",
            "columns": {
                "event_id": "事件ID",
                "user_id": "用户ID",
                "event_name": "事件名",
                "event_time": "事件时间",
                "page": "页面",
            },
        },
    }

    metrics = {
        "gmv": {
            "definition": "已支付订单金额之和，不含退款和取消",
            "expression": "SUM(orders.pay_amount)",
            "filters": ["orders.status = 'paid'"],
        },
        "order_count": {
            "definition": "订单数量",
            "expression": "COUNT(DISTINCT orders.order_id)",
            "filters": ["orders.status = 'paid'"],
        },
        "active_user_count": {
            "definition": "期间内有行为事件的去重用户数",
            "expression": "COUNT(DISTINCT user_events.user_id)",
            "filters": [],
        },
        "aov": {
            "definition": "平均客单价",
            "expression": "AVG(orders.pay_amount)",
            "filters": ["orders.status = 'paid'"],
        },
        "item_quantity": {
            "definition": "商品件数",
            "expression": "SUM(orders.quantity)",
            "filters": ["orders.status = 'paid'"],
        },
    }
    (output_dir / "schema_dictionary.json").write_text(
        json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "metric_dictionary.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
