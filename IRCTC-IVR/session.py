sessions = {}

def get_session(session_id):

    if session_id not in sessions:

        sessions[session_id] = {
            "state": "welcome",
            "origin": None,
            "destination": None,
            "date": None,
            "selected_train": None,
            "pnr": None
        }

    return sessions[session_id]