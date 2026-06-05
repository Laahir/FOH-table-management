"""Initial data matching frontend/src/mock/data.ts"""

DEMO_PASSWORD = "demo1234"

DEMO_USERS = [
    {"id": "u-owner", "name": "Alex Owner", "email": "owner@foh.demo", "role": "OWNER"},
    {"id": "u-manager", "name": "Morgan Manager", "email": "manager@foh.demo", "role": "MANAGER"},
    {"id": "u-host", "name": "Hannah Host", "email": "host@foh.demo", "role": "HOST"},
    {"id": "u-waiter", "name": "Wade Waiter", "email": "waiter@foh.demo", "role": "WAITER"},
]

INITIAL_FLOOR = {
    "id": "floor-1",
    "name": "Main Dining",
    "width": 1000,
    "height": 620,
    "sections": [
        {
            "id": "sec-indoor",
            "name": "Indoor",
            "color": "#818cf8",
            "bounds": {"x": 40, "y": 48, "width": 580, "height": 300},
        },
        {
            "id": "sec-outdoor",
            "name": "Outdoor",
            "color": "#38bdf8",
            "bounds": {"x": 40, "y": 380, "width": 420, "height": 200},
        },
        {
            "id": "sec-bar",
            "name": "Bar",
            "color": "#fbbf24",
            "bounds": {"x": 680, "y": 48, "width": 280, "height": 300},
        },
    ],
    "labels": [
        {
            "id": "lbl-entrance",
            "kind": "ENTRANCE",
            "text": "Entrance",
            "bounds": {"x": 400, "y": 564, "width": 200, "height": 44},
        },
        {
            "id": "lbl-kitchen",
            "kind": "KITCHEN",
            "text": "Kitchen",
            "bounds": {"x": 860, "y": 12, "width": 120, "height": 44},
        },
    ],
    "tables": [
        {"id": "t-1", "sectionId": "sec-indoor", "number": "1", "capacity": 2, "type": "STANDARD", "shape": "CIRCLE", "status": "AVAILABLE", "x": 120, "y": 120, "width": 64, "height": 64, "rotation": 0},
        {"id": "t-2", "sectionId": "sec-indoor", "number": "2", "capacity": 4, "type": "STANDARD", "shape": "RECTANGLE", "status": "AVAILABLE", "x": 220, "y": 110, "width": 90, "height": 70, "rotation": 0},
        {"id": "t-3", "sectionId": "sec-indoor", "number": "3", "capacity": 6, "type": "BOOTH", "shape": "RECTANGLE", "status": "RESERVED", "x": 360, "y": 100, "width": 110, "height": 85, "rotation": 0},
        {"id": "t-4", "sectionId": "sec-indoor", "number": "4", "capacity": 8, "type": "VIP", "shape": "RECTANGLE", "status": "AVAILABLE", "x": 520, "y": 95, "width": 120, "height": 95, "rotation": 0},
        {"id": "t-5", "sectionId": "sec-indoor", "number": "5", "capacity": 4, "type": "STANDARD", "shape": "RECTANGLE", "status": "AVAILABLE", "x": 120, "y": 230, "width": 88, "height": 72, "rotation": 0},
        {"id": "t-6", "sectionId": "sec-outdoor", "number": "P1", "capacity": 4, "type": "STANDARD", "shape": "RECTANGLE", "status": "AVAILABLE", "x": 120, "y": 400, "width": 92, "height": 72, "rotation": 0},
        {"id": "t-7", "sectionId": "sec-outdoor", "number": "P2", "capacity": 2, "type": "STANDARD", "shape": "CIRCLE", "status": "AVAILABLE", "x": 250, "y": 410, "width": 64, "height": 64, "rotation": 0},
        {"id": "t-8", "sectionId": "sec-bar", "number": "B1", "capacity": 2, "type": "BAR", "shape": "CIRCLE", "status": "AVAILABLE", "x": 780, "y": 140, "width": 56, "height": 56, "rotation": 0},
        {"id": "t-9", "sectionId": "sec-bar", "number": "B2", "capacity": 2, "type": "BAR", "shape": "CIRCLE", "status": "CLEANING", "x": 860, "y": 140, "width": 56, "height": 56, "rotation": 0},
        {"id": "t-10", "sectionId": "sec-bar", "number": "B3", "capacity": 2, "type": "BAR", "shape": "CIRCLE", "status": "AVAILABLE", "x": 820, "y": 220, "width": 56, "height": 56, "rotation": 0},
    ],
}
