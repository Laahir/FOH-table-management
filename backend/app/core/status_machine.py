from typing import Literal

TableStatus = Literal[
    "AVAILABLE",
    "RESERVED",
    "SEATED",
    "ACTIVE",
    "BILLING",
    "PAID",
    "CLEANING",
]

STATUS_TRANSITIONS: dict[str, list[str]] = {
    "AVAILABLE": ["RESERVED"],
    "RESERVED": ["AVAILABLE"],
    "SEATED": ["ACTIVE", "BILLING"],
    "ACTIVE": ["BILLING"],
    "BILLING": ["PAID"],
    "PAID": ["CLEANING"],
    "CLEANING": ["AVAILABLE"],
}

ACTIVE_SESSION_STATUSES = {"SEATED", "ACTIVE", "BILLING", "PAID"}


def is_valid_transition(current: str, target: str) -> bool:
    return target in STATUS_TRANSITIONS.get(current, [])
