from intent import detect_intent, extract_booking_details, extract_date


def handle_flow(session, user_text):

    state = session["state"]
    intent = detect_intent(user_text)

    # -------- CONTEXT CORRECTION --------

    if intent == "change_destination":

        city = user_text.split("to")[-1].strip().capitalize()

        session["destination"] = city

        return f"Destination updated to {city}. Please provide travel date."


    if intent == "change_date":

        new_date = extract_date(user_text)

        if new_date:
            session["date"] = new_date
            return f"Travel date updated to {new_date}."

        return "Please tell the correct travel date."


    # -------- GLOBAL INTENTS --------

    if intent == "pnr_status":

        session["state"] = "get_pnr"
        return "Please enter your 10 digit PNR number."


    if intent == "cancel_ticket":

        session["state"] = "cancel_ticket"
        return "Please provide your PNR or booking reference."


    if intent == "book_ticket":

        origin, destination = extract_booking_details(user_text)
        date = extract_date(user_text)

        if origin and destination:

            session["origin"] = origin
            session["destination"] = destination

            if date:
                session["date"] = date
                session["state"] = "train_results"
                return f"Searching trains from {origin} to {destination} on {date}..."

            session["state"] = "get_date"
            return f"Booking from {origin} to {destination}. What is your travel date?"

        session["state"] = "get_origin"
        return "Sure. From which city are you travelling?"


    # -------- BOOKING FLOW --------

    if state == "get_origin":

        session["origin"] = user_text
        session["state"] = "get_destination"

        return f"Travelling from {user_text}. Where do you want to go?"


    elif state == "get_destination":

        session["destination"] = user_text
        session["state"] = "get_date"

        return f"Travelling to {user_text}. What is your travel date?"


    elif state == "get_date":

        session["date"] = user_text
        session["state"] = "train_results"

        return f"Searching trains from {session['origin']} to {session['destination']} on {session['date']}..."


    elif state == "train_results":

        session["selected_train"] = "Telangana Express – 18:30"
        session["state"] = "confirm"

        return (
            "3 trains available:\n"
            "1️⃣ Telangana Express – 18:30\n"
            "2️⃣ AP Express – 20:10\n"
            "3️⃣ Duronto Express – 22:00\n"
            "Do you want to confirm booking?"
        )


    elif state == "confirm":

        if any(word in user_text.lower() for word in ["yes", "confirm", "ok"]):

            session["state"] = "booked"

            return f"Your ticket has been booked on {session['selected_train']}."

        else:

            session["state"] = "welcome"
            return "Booking cancelled."


    elif state == "booked":

        if intent == "seat_check":
            return "Seats are available in Sleeper and AC 3 Tier."

        if "which train" in user_text.lower():
            return f"Your ticket is booked on {session['selected_train']}."

        return "Your ticket is booked. You can ask for seat availability, PNR status, or cancel booking."


    # -------- PNR --------

    if state == "get_pnr":

        session["pnr"] = user_text
        session["state"] = "welcome"

        return f"PNR {user_text} status: Confirmed. Train departs at 18:30."


    # -------- CANCEL --------

    if state == "cancel_ticket":

        session["state"] = "welcome"

        return "Your booking has been cancelled successfully."


    return "How can I assist you?"