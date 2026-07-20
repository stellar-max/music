"""Provides API routes for creating and managing collaborative listening rooms."""

import sqlite3
import uuid

from flask import Blueprint, jsonify, request, session

from common import DB_FILE, get_current_user, login_required


rooms_bp = Blueprint("rooms", __name__)


def get_connection():
    connection = sqlite3.connect(DB_FILE)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@rooms_bp.route("", methods=["GET"])
def get_rooms():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                r.*,
                u.nickname AS host_nickname,
                u.display_name AS host_display_name,
                COUNT(DISTINCT rm.user_id) AS members_count
            FROM rooms AS r
            LEFT JOIN users AS u
                ON u.id = r.host_id
            LEFT JOIN room_members AS rm
                ON rm.room_id = r.id
            GROUP BY r.id
            ORDER BY r.created_at DESC
            """
        ).fetchall()

        return jsonify([dict(row) for row in rows])

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>", methods=["GET"])
def get_room(room_id):
    connection = get_connection()

    try:
        room = connection.execute(
            """
            SELECT
                r.*,
                u.nickname AS host_nickname,
                u.display_name AS host_display_name
            FROM rooms AS r
            LEFT JOIN users AS u
                ON u.id = r.host_id
            WHERE r.id = ?
            """,
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        members = connection.execute(
            """
            SELECT
                u.id,
                u.nickname,
                u.display_name,
                u.avatar_url,
                rm.joined_at
            FROM room_members AS rm
            JOIN users AS u
                ON u.id = rm.user_id
            WHERE rm.room_id = ?
            ORDER BY rm.joined_at ASC
            """,
            (room_id,),
        ).fetchall()

        queue = connection.execute(
            """
            SELECT
                rq.id AS queue_id,
                rq.sort_order,
                rq.added_by_id,
                rq.created_at,
                t.*
            FROM room_queue AS rq
            JOIN tracks AS t
                ON t.id = rq.track_id
            WHERE rq.room_id = ?
            ORDER BY rq.sort_order ASC, rq.id ASC
            """,
            (room_id,),
        ).fetchall()

        result = dict(room)
        result["members"] = [dict(member) for member in members]
        result["queue"] = [dict(item) for item in queue]

        return jsonify(result)

    finally:
        connection.close()


@rooms_bp.route("", methods=["POST"])
@login_required
def create_room():
    data = request.get_json(silent=True) or {}
    name = str(data.get("name", "")).strip()

    if not name:
        return jsonify({"error": "Room name is required"}), 400

    room_id = uuid.uuid4().hex[:12]
    user_id = session["user_id"]

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO rooms (
                id,
                name,
                host_id
            )
            VALUES (?, ?, ?)
            """,
            (
                room_id,
                name,
                user_id,
            ),
        )

        connection.execute(
            """
            INSERT OR IGNORE INTO room_members (
                room_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                room_id,
                user_id,
            ),
        )

        connection.commit()

        return jsonify(
            {
                "success": True,
                "id": room_id,
                "name": name,
            }
        ), 201

    except Exception as error:
        connection.rollback()
        print(f"Failed to create room: {error}")
        return jsonify({"error": "Failed to create room"}), 500

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>/join", methods=["POST"])
@login_required
def join_room_api(room_id):
    user_id = session["user_id"]
    connection = get_connection()

    try:
        room = connection.execute(
            "SELECT id FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        connection.execute(
            """
            INSERT OR IGNORE INTO room_members (
                room_id,
                user_id
            )
            VALUES (?, ?)
            """,
            (
                room_id,
                user_id,
            ),
        )

        connection.commit()
        return jsonify({"success": True})

    except Exception as error:
        connection.rollback()
        print(f"Failed to join room: {error}")
        return jsonify({"error": "Failed to join room"}), 500

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>/leave", methods=["POST"])
@login_required
def leave_room_api(room_id):
    user_id = session["user_id"]
    connection = get_connection()

    try:
        room = connection.execute(
            "SELECT host_id FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        if room["host_id"] == user_id:
            return jsonify(
                {"error": "Room host cannot leave without deleting the room"}
            ), 400

        connection.execute(
            """
            DELETE FROM room_members
            WHERE room_id = ?
              AND user_id = ?
            """,
            (
                room_id,
                user_id,
            ),
        )

        connection.commit()
        return jsonify({"success": True})

    except Exception as error:
        connection.rollback()
        print(f"Failed to leave room: {error}")
        return jsonify({"error": "Failed to leave room"}), 500

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>/queue", methods=["POST"])
@login_required
def add_to_queue(room_id):
    data = request.get_json(silent=True) or {}
    track_id = data.get("track_id")
    user_id = session["user_id"]

    if not track_id:
        return jsonify({"error": "track_id is required"}), 400

    connection = get_connection()

    try:
        member = connection.execute(
            """
            SELECT 1
            FROM room_members
            WHERE room_id = ?
              AND user_id = ?
            """,
            (
                room_id,
                user_id,
            ),
        ).fetchone()

        if member is None:
            return jsonify({"error": "Join the room first"}), 403

        track = connection.execute(
            "SELECT id FROM tracks WHERE id = ?",
            (track_id,),
        ).fetchone()

        if track is None:
            return jsonify({"error": "Track not found"}), 404

        maximum_order = connection.execute(
            """
            SELECT COALESCE(MAX(sort_order), 0)
            FROM room_queue
            WHERE room_id = ?
            """,
            (room_id,),
        ).fetchone()[0]

        connection.execute(
            """
            INSERT INTO room_queue (
                room_id,
                track_id,
                added_by_id,
                sort_order
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                room_id,
                track_id,
                user_id,
                maximum_order + 1,
            ),
        )

        connection.commit()
        return jsonify({"success": True}), 201

    except Exception as error:
        connection.rollback()
        print(f"Failed to add room queue item: {error}")
        return jsonify({"error": "Failed to add track"}), 500

    finally:
        connection.close()


@rooms_bp.route(
    "/<string:room_id>/queue/<int:queue_id>",
    methods=["DELETE"],
)
@login_required
def remove_from_queue(room_id, queue_id):
    user_id = session["user_id"]
    connection = get_connection()

    try:
        room = connection.execute(
            "SELECT host_id FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        queue_item = connection.execute(
            """
            SELECT added_by_id
            FROM room_queue
            WHERE id = ?
              AND room_id = ?
            """,
            (
                queue_id,
                room_id,
            ),
        ).fetchone()

        if queue_item is None:
            return jsonify({"error": "Queue item not found"}), 404

        if (
            room["host_id"] != user_id
            and queue_item["added_by_id"] != user_id
        ):
            return jsonify({"error": "Forbidden"}), 403

        connection.execute(
            """
            DELETE FROM room_queue
            WHERE id = ?
              AND room_id = ?
            """,
            (
                queue_id,
                room_id,
            ),
        )

        connection.commit()
        return jsonify({"success": True})

    except Exception as error:
        connection.rollback()
        print(f"Failed to remove queue item: {error}")
        return jsonify({"error": "Failed to remove track"}), 500

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>/state", methods=["PUT"])
@login_required
def update_room_state(room_id):
    current_user = get_current_user()

    if current_user is None:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    connection = get_connection()

    try:
        room = connection.execute(
            "SELECT host_id FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        if room["host_id"] != current_user["id"]:
            return jsonify({"error": "Only the host can update playback"}), 403

        current_track_id = data.get("current_track_id")
        is_playing = 1 if data.get("is_playing", False) else 0

        try:
            current_time = max(
                0.0,
                float(data.get("current_time", 0.0)),
            )
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid current_time"}), 400

        connection.execute(
            """
            UPDATE rooms
            SET current_track_id = ?,
                is_playing = ?,
                current_time = ?
            WHERE id = ?
            """,
            (
                current_track_id,
                is_playing,
                current_time,
                room_id,
            ),
        )

        connection.commit()
        return jsonify({"success": True})

    except Exception as error:
        connection.rollback()
        print(f"Failed to update room state: {error}")
        return jsonify({"error": "Failed to update room"}), 500

    finally:
        connection.close()


@rooms_bp.route("/<string:room_id>", methods=["DELETE"])
@login_required
def delete_room(room_id):
    user_id = session["user_id"]
    connection = get_connection()

    try:
        room = connection.execute(
            "SELECT host_id FROM rooms WHERE id = ?",
            (room_id,),
        ).fetchone()

        if room is None:
            return jsonify({"error": "Room not found"}), 404

        if room["host_id"] != user_id:
            return jsonify({"error": "Only the host can delete the room"}), 403

        connection.execute(
            "DELETE FROM room_queue WHERE room_id = ?",
            (room_id,),
        )

        connection.execute(
            "DELETE FROM room_members WHERE room_id = ?",
            (room_id,),
        )

        connection.execute(
            "DELETE FROM rooms WHERE id = ?",
            (room_id,),
        )

        connection.commit()
        return jsonify({"success": True})

    except Exception as error:
        connection.rollback()
        print(f"Failed to delete room: {error}")
        return jsonify({"error": "Failed to delete room"}), 500

    finally:
        connection.close()
