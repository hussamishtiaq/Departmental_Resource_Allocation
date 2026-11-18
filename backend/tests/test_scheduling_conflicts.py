def test_create_valid_schedule(client, admin_headers, room, faculty):
    response = client.post(
        "/api/v1/schedules",
        headers=admin_headers,
        json={
            "resource_id": room.id,
            "faculty_id": faculty.id,
            "course_name": "Database Systems",
            "class_name": "BSSE Semester 4 Section A",
            "day_of_week": 0,
            "start_time": "09:00:00",
            "end_time": "10:30:00",
            "start_date": "2026-11-16",
            "end_date": "2027-02-15",
        },
    )
    assert response.status_code == 201


def test_reject_invalid_time(client, admin_headers, room, faculty):
    response = client.post(
        "/api/v1/schedules",
        headers=admin_headers,
        json={
            "resource_id": room.id,
            "faculty_id": faculty.id,
            "course_name": "Database Systems",
            "class_name": "BSSE Semester 4 Section A",
            "day_of_week": 0,
            "start_time": "11:00:00",
            "end_time": "09:00:00",
            "start_date": "2026-11-16",
            "end_date": "2027-02-15",
        },
    )
    assert response.status_code == 422


# Add tests for:
# - same room overlap -> 409
# - same faculty overlap -> 409
# - adjacent slots -> both accepted
# - unavailable or non-room resource -> rejected
# - approved reservation conflict in both directions -> rejected
# - update conflict, cancellation, and authorization -> 403