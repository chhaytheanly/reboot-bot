def validate_seed_data(data):
    tenants = data.get("tenants", [])

    seen_tenants = set()
    seen_rooms = set()

    for t in tenants:
        tenant_id = t.get("tenant_id")
        room = t.get("room")

        if tenant_id in seen_tenants:
            raise ValueError(f"Duplicate tenant_id: {tenant_id}")

        if room in seen_rooms:
            raise ValueError(f"Multiple tenants assigned to room: {room}")

        seen_tenants.add(tenant_id)
        seen_rooms.add(room)