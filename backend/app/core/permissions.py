from typing import Literal

Role = Literal["OWNER", "MANAGER", "HOST", "WAITER"]


def can_edit_floor(role: str) -> bool:
    return role in ("OWNER", "MANAGER")


def can_manage_users(role: str) -> bool:
    return role == "OWNER"


def can_manage_menu(role: str) -> bool:
    return role in ("OWNER", "MANAGER")


def can_manage_reservations(role: str) -> bool:
    return role in ("OWNER", "MANAGER", "HOST")
