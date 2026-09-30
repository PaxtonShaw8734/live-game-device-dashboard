from src.dashboard_service import DeviceStatus, moderation_state


def test_high_moderation_score_enters_review_queue() -> None:
    flagged = DeviceStatus("cabinet-1", "player-9", 2, 0.8)
    ordinary = DeviceStatus("cabinet-2", "player-9", 1, 0.79)
    assert moderation_state(flagged) == "review"
    assert moderation_state(ordinary) == "visible"

