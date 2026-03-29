from state_machine import StateMachine

def run_test(test_name, steps):
    print(f"\n--- Running Test: {test_name} ---")
    sm = StateMachine()
    session_id = f"test_{test_name.lower().replace(' ', '_')}"
    
    for i, step in enumerate(steps):
        print(f"\nStep {i+1}: User says '{step['input']}'")
        result = sm.process_input(session_id, step['input'], is_dtmf=step.get('is_dtmf', False))
        
        print(f"  -> System: {result['response']}")
        print(f"  -> State: {result['state']}")
        print(f"  -> Intent: {result['intent']}")
        
        # Assertions (optional, for more rigorous testing)
        assert result['state'] == step['expected_state'], f"Expected state {step['expected_state']}, but got {result['state']}"
        if 'expected_intent' in step:
            assert result['intent'] == step['expected_intent'], f"Expected intent {step['expected_intent']}, but got {result['intent']}"

if __name__ == "__main__":
    # Test 1: Full Booking Flow via Chat
    booking_chat_steps = [
        {"input": "Book ticket", "expected_state": "ASK_SOURCE", "expected_intent": "booking"},
        {"input": "Hyderabad", "expected_state": "ASK_DESTINATION"},
        {"input": "Delhi", "expected_state": "ASK_DATE"},
        {"input": "Tomorrow", "expected_state": "SHOW_TRAINS"},
        {"input": "Confirm", "expected_state": "ASK_CLASS"},
        {"input": "2A", "expected_state": "MAIN_MENU"},
    ]
    run_test("Full Booking Flow - Chat", booking_chat_steps)

    # Test 2: Full Booking Flow via DTMF
    booking_dtmf_steps = [
        {"input": "1", "is_dtmf": True, "expected_state": "ASK_SOURCE"},
        {"input": "Hyderabad", "expected_state": "ASK_DESTINATION"},
        {"input": "Delhi", "expected_state": "ASK_DATE"},
        {"input": "Tomorrow", "expected_state": "SHOW_TRAINS"},
        {"input": "Confirm", "expected_state": "ASK_CLASS"},
        {"input": "2", "is_dtmf": True, "expected_state": "MAIN_MENU"},
    ]
    run_test("Full Booking Flow - DTMF", booking_dtmf_steps)

    # Test 3: PNR Status Check
    pnr_steps = [
        {"input": "PNR Status", "expected_state": "PNR_STATUS", "expected_intent": "pnr_status"},
        {"input": "1234567890", "expected_state": "MAIN_MENU"},
    ]
    run_test("PNR Status Check", pnr_steps)

    # Test 4: Cancellation Flow
    cancel_steps = [
        {"input": "Cancel ticket", "expected_state": "CANCEL_TICKET", "expected_intent": "cancel_ticket"},
        {"input": "9876543210", "expected_state": "MAIN_MENU"},
    ]
    run_test("Cancellation Flow", cancel_steps)

    # Test 5: Mode Switching
    mode_switch_steps = [
        {"input": "Book ticket", "expected_state": "ASK_SOURCE"},
        {"input": "1", "is_dtmf": True, "expected_state": "ASK_SOURCE"}, # Should not break
        {"input": "Chennai", "expected_state": "ASK_DESTINATION"},
    ]
    run_test("Mode Switching", mode_switch_steps)

    print("\n--- All tests passed successfully! ---")
