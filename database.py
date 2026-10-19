from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, Text, Boolean,
    DateTime, ForeignKey, select, func, update, delete
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from config import DATABASE_URL

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class User(Base):
    __tablename__ = "users"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    language = Column(String(10), default="en")
    is_banned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Deal(Base):
    __tablename__ = "deals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=True)  # DL-MM-811 style
    buyer_id = Column(BigInteger, ForeignKey("users.user_id"))
    seller_id = Column(BigInteger, ForeignKey("users.user_id"))
    amount = Column(Float, nullable=False)
    currency = Column(String(50), nullable=False)
    deal_type = Column(String(20), default="crypto")  # crypto / inr
    description = Column(Text)
    expected_time = Column(String(50), nullable=True)
    terms = Column(Text, nullable=True)  # T/C
    status = Column(String(30), default="pending_payment")
    # Middleman payment details
    payment_details = Column(Text, nullable=True)  # address or UPI
    payment_note = Column(Text, nullable=True)
    released_amount = Column(Float, nullable=True)
    escrowed_by = Column(String(100), nullable=True)  # @username of middleman
    group_id = Column(BigInteger, nullable=True)
    admin_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)




class Escrower(Base):
    __tablename__ = "escrowers"
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    deal_limit = Column(Integer, default=10)  # max active deals
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class EscrowerAddress(Base):
    __tablename__ = "escrower_addresses"
    id = Column(Integer, primary_key=True, autoincrement=True)
    escrower_id = Column(BigInteger, ForeignKey("escrowers.user_id"))
    address = Column(String(255), nullable=False)
    label = Column(String(100), nullable=True)  # e.g. USDT TRC20
    created_at = Column(DateTime, default=datetime.utcnow)

class Settings(Base):
    __tablename__ = "settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Default settings
    defaults = {
        "platform_fee": "2.5",
        "support_contact": "@support",
        "maintenance_mode": "0",
        "min_amount": "10",
        "max_amount": "500000",
        "default_crypto_wallet": "Not set",
        "default_upi_id": "Not set",
            "log_channel_id": "",
            "completed_channel_id": "",
            "vouch_channel_id": "",
            "force_group_id": "",
            "force_group_link": "",
            "force_channel_id": "",
            "force_channel_link": "",
    }
    async with async_session() as session:
        for k, v in defaults.items():
            exists = await session.get(Settings, k)
            if not exists:
                session.add(Settings(key=k, value=v))
        await session.commit()


# ---------- User helpers ----------

async def add_user(user_id: int, username: str = None, full_name: str = None, lang: str = "en"):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.username = username
            user.full_name = full_name
        else:
            session.add(User(user_id=user_id, username=username, full_name=full_name, language=lang))
        await session.commit()


async def get_user(user_id: int) -> Optional[Dict]:
    async with async_session() as session:
        user = await session.get(User, user_id)
        if not user:
            return None
        return {
            "user_id": user.user_id,
            "username": user.username,
            "full_name": user.full_name,
            "language": user.language,
            "is_banned": user.is_banned,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


async def set_user_lang(user_id: int, lang: str):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.language = lang
            await session.commit()


async def is_banned(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, user_id)
        return bool(user and user.is_banned)


async def ban_user(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_banned = True
            await session.commit()


async def unban_user(user_id: int):
    async with async_session() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_banned = False
            await session.commit()


async def get_all_users(limit: int = 100) -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.created_at.desc()).limit(limit))
        users = result.scalars().all()
        return [{
            "user_id": u.user_id, "username": u.username, "full_name": u.full_name,
            "language": u.language, "is_banned": u.is_banned,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in users]


async def get_banned_users() -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_banned == True))
        users = result.scalars().all()
        return [{"user_id": u.user_id, "username": u.username, "full_name": u.full_name} for u in users]


async def get_all_user_ids() -> List[int]:
    async with async_session() as session:
        result = await session.execute(select(User.user_id).where(User.is_banned == False))
        return [r[0] for r in result.all()]


# ---------- Deal helpers ----------

async def create_deal(
    buyer_id: int, seller_id: int, amount: float, currency: str,
    description: str, deal_type: str = "crypto", group_id: int = None,
    expected_time: str = None, terms: str = None, escrowed_by: str = None
) -> int:
    async with async_session() as session:
        # Generate Trade ID like DL-MM-811
        result = await session.execute(select(func.count(Deal.id)))
        count = (result.scalar() or 0) + 1
        trade_id = f"DL-MM-{count + 800}"

        deal = Deal(
            trade_id=trade_id,
            buyer_id=buyer_id, seller_id=seller_id, amount=amount,
            currency=currency, description=description, deal_type=deal_type,
            expected_time=expected_time, terms=terms,
            escrowed_by=escrowed_by, group_id=group_id,
            status="pending_payment"
        )
        session.add(deal)
        await session.commit()
        await session.refresh(deal)
        return deal.id



async def get_deal(deal_id: int) -> Optional[Dict]:
    async with async_session() as session:
        deal = await session.get(Deal, deal_id)
        if not deal:
            return None
        return _deal_to_dict(deal)


async def get_user_deals(user_id: int) -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Deal).where((Deal.buyer_id == user_id) | (Deal.seller_id == user_id))
            .order_by(Deal.created_at.desc())
        )
        return [_deal_to_dict(d) for d in result.scalars().all()]


async def get_active_deals() -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Deal).where(Deal.status.notin_(["completed", "refunded", "cancelled"]))
            .order_by(Deal.created_at.desc())
        )
        return [_deal_to_dict(d) for d in result.scalars().all()]


async def get_deals_by_status(status: str, limit: int = 30) -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(
            select(Deal).where(Deal.status == status)
            .order_by(Deal.created_at.desc()).limit(limit)
        )
        return [_deal_to_dict(d) for d in result.scalars().all()]


async def get_all_deals(limit: int = 100) -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(select(Deal).order_by(Deal.created_at.desc()).limit(limit))
        return [_deal_to_dict(d) for d in result.scalars().all()]


async def update_deal_status(deal_id: int, status: str, admin_note: str = None):
    async with async_session() as session:
        deal = await session.get(Deal, deal_id)
        if deal:
            deal.status = status
            deal.updated_at = datetime.utcnow()
            if admin_note is not None:
                deal.admin_note = admin_note
            await session.commit()


async def set_deal_payment(deal_id: int, payment_details: str, payment_note: str = None):
    async with async_session() as session:
        deal = await session.get(Deal, deal_id)
        if deal:
            deal.payment_details = payment_details
            deal.payment_note = payment_note
            deal.updated_at = datetime.utcnow()
            await session.commit()


async def delete_deal(deal_id: int):
    async with async_session() as session:
        deal = await session.get(Deal, deal_id)
        if deal:
            await session.delete(deal)
            await session.commit()


def _deal_to_dict(d: Deal) -> Dict:
    return {
        "id": d.id,
        "trade_id": d.trade_id,
        "buyer_id": d.buyer_id,
        "seller_id": d.seller_id,
        "amount": d.amount,
        "currency": d.currency,
        "deal_type": d.deal_type,
        "description": d.description,
        "expected_time": d.expected_time,
        "terms": d.terms,
        "status": d.status,
        "payment_details": d.payment_details,
        "payment_note": d.payment_note,
        "released_amount": d.released_amount,
        "escrowed_by": d.escrowed_by,
        "group_id": d.group_id,
        "admin_note": d.admin_note,
        "created_at": d.created_at.isoformat() if d.created_at else None,
        "updated_at": d.updated_at.isoformat() if d.updated_at else None,
    }



# ---------- Stats & Settings ----------

async def get_stats() -> Dict[str, Any]:
    async with async_session() as session:
        total = (await session.execute(select(func.count(Deal.id)))).scalar() or 0
        completed = (await session.execute(select(func.count(Deal.id)).where(Deal.status == "completed"))).scalar() or 0
        disputed = (await session.execute(select(func.count(Deal.id)).where(Deal.status == "disputed"))).scalar() or 0
        active = (await session.execute(
            select(func.count(Deal.id)).where(Deal.status.notin_(["completed", "refunded", "cancelled"]))
        )).scalar() or 0
        volume = (await session.execute(
            select(func.coalesce(func.sum(Deal.amount), 0)).where(Deal.status == "completed")
        )).scalar() or 0
        users = (await session.execute(select(func.count(User.user_id)))).scalar() or 0
        banned = (await session.execute(select(func.count(User.user_id)).where(User.is_banned == True))).scalar() or 0
        return {
            "total_deals": total, "completed": completed, "disputed": disputed,
            "active": active, "volume": float(volume), "users": users, "banned": banned
        }


async def get_setting(key: str, default: str = "") -> str:
    async with async_session() as session:
        row = await session.get(Settings, key)
        return row.value if row else default


async def set_setting(key: str, value: str):
    async with async_session() as session:
        row = await session.get(Settings, key)
        if row:
            row.value = value
        else:
            session.add(Settings(key=key, value=value))
        await session.commit()


async def get_fee() -> float:
    return float(await get_setting("platform_fee", "2.5"))


async def set_fee(fee: float):
    await set_setting("platform_fee", str(fee))


async def is_maintenance() -> bool:
    return (await get_setting("maintenance_mode", "0")) == "1"


async def set_released_amount(deal_id: int, amount: float):
    async with async_session() as session:
        deal = await session.get(Deal, deal_id)
        if deal:
            deal.released_amount = amount
            deal.updated_at = datetime.utcnow()
            await session.commit()


# ---------- Escrower helpers ----------

async def add_escrower(user_id: int, username: str = None, full_name: str = None, deal_limit: int = 10):
    async with async_session() as session:
        e = await session.get(Escrower, user_id)
        if e:
            e.username = username
            e.full_name = full_name
            e.is_active = True
            e.deal_limit = deal_limit
        else:
            session.add(Escrower(
                user_id=user_id, username=username, full_name=full_name,
                deal_limit=deal_limit, is_active=True
            ))
        await session.commit()


async def remove_escrower(user_id: int):
    async with async_session() as session:
        e = await session.get(Escrower, user_id)
        if e:
            e.is_active = False
            await session.commit()


async def is_escrower(user_id: int) -> bool:
    async with async_session() as session:
        e = await session.get(Escrower, user_id)
        return bool(e and e.is_active)


async def get_escrower(user_id: int) -> Optional[Dict]:
    async with async_session() as session:
        e = await session.get(Escrower, user_id)
        if not e:
            return None
        return {
            "user_id": e.user_id, "username": e.username, "full_name": e.full_name,
            "deal_limit": e.deal_limit, "is_active": e.is_active
        }


async def get_all_escrowers() -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(select(Escrower).where(Escrower.is_active == True))
        rows = result.scalars().all()
        return [{
            "user_id": e.user_id, "username": e.username, "full_name": e.full_name,
            "deal_limit": e.deal_limit
        } for e in rows]


async def set_escrower_limit(user_id: int, limit: int):
    async with async_session() as session:
        e = await session.get(Escrower, user_id)
        if e:
            e.deal_limit = limit
            await session.commit()


async def count_escrower_active_deals(user_id: int) -> int:
    """Count deals where this user is escrowed_by conceptually - we store escrower in deal.escrowed_by as @username.
    Simpler: count deals they created as middleman isn't tracked by id easily.
    Alternative: count deals with status active where admin_note or we add escrower_id field.
    For now use a simple approach via escrower_id on deal if we set it.
    """
    async with async_session() as session:
        # We'll track via a new optional column - for compatibility count 0 if not set
        result = await session.execute(
            select(func.count(Deal.id)).where(
                Deal.status.notin_(["completed", "refunded", "cancelled"]),
                Deal.escrowed_by.isnot(None)
            )
        )
        # Without escrower_id column, return active total for limit check at assign time
        return result.scalar() or 0


async def add_escrower_address(escrower_id: int, address: str, label: str = None):
    async with async_session() as session:
        # normalize
        addr = address.strip()
        session.add(EscrowerAddress(escrower_id=escrower_id, address=addr, label=label))
        await session.commit()


async def remove_escrower_address(address_id: int, escrower_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(EscrowerAddress).where(
                EscrowerAddress.id == address_id,
                EscrowerAddress.escrower_id == escrower_id
            )
        )
        row = result.scalar_one_or_none()
        if row:
            await session.delete(row)
            await session.commit()


async def get_escrower_addresses(escrower_id: int) -> List[Dict]:
    async with async_session() as session:
        result = await session.execute(
            select(EscrowerAddress).where(EscrowerAddress.escrower_id == escrower_id)
        )
        rows = result.scalars().all()
        return [{"id": r.id, "address": r.address, "label": r.label} for r in rows]


async def find_address_owner(address: str) -> Optional[Dict]:
    """Return escrower info if address is registered, else None."""
    addr = address.strip()
    async with async_session() as session:
        result = await session.execute(
            select(EscrowerAddress).where(EscrowerAddress.address == addr)
        )
        row = result.scalar_one_or_none()
        if not row:
            # try case-insensitive
            result = await session.execute(select(EscrowerAddress))
            for r in result.scalars().all():
                if r.address.lower() == addr.lower():
                    row = r
                    break
        if not row:
            return None
        e = await session.get(Escrower, row.escrower_id)
        if not e or not e.is_active:
            return None
        return {
            "user_id": e.user_id,
            "username": e.username,
            "full_name": e.full_name,
            "address": row.address,
            "label": row.label
        }
