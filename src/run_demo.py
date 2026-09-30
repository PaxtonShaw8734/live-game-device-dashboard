from dashboard_service import DashboardClient, DeviceStatus, moderation_state


def main() -> None:
    status = DeviceStatus("arcade-7", "player-42", 3, 0.91)
    print({"device": status.device_id, "decision": moderation_state(status), "capability": "realtime.publish"})
    client = DashboardClient()
    client.create_channel("game-devices")
    token = client.issue_token("dashboard-browser", "game-devices")
    client.publish_status("game-devices", status, "game-ops")
    print({"dashboard_token": token.get("data")})


if __name__ == "__main__":
    main()

