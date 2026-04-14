try:
    from app.services.chat_history_service import ChatHistoryService
    from app.models.database import ChatSession
    print("SUCCESS: Service and Model imported correctly.")
except Exception as e:
    print(f"FAILURE: {e}")
