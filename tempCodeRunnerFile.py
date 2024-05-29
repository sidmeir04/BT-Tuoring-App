sessions_where_teach_MH = [MessageHistory.query.get(session.message_history_id) for session in sessions_where_teach]
    sess