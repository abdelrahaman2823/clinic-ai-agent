# backend/app/services/chat_service.py

from langchain_core.messages import HumanMessage, AIMessage
from app.agent.graph import agent_graph
from app.agent.state import AgentState
from app.models.chat import ChatMessage, MessageRole
from app.core.database import SessionLocal
import uuid


class ChatService:
    def process_message(
        self,
        patient_id: int,
        patient_name: str,
        message: str,
        session_id: str = None,
    ) -> dict:
        """معالجة رسالة المريض وإرجاع الرد"""

        if not session_id:
            session_id = str(uuid.uuid4())

        # جلب تاريخ المحادثة من الـ DB
        db = SessionLocal()
        try:
            history = db.query(ChatMessage).filter(
                ChatMessage.patient_id == patient_id,
                ChatMessage.session_id == session_id,
            ).order_by(ChatMessage.created_at).all()

            # تحويل التاريخ لـ LangChain messages
            lc_messages = []
            for msg in history:
                if msg.role == MessageRole.user:
                    lc_messages.append(HumanMessage(content=msg.content))
                else:
                    lc_messages.append(AIMessage(content=msg.content))

            # إضافة الرسالة الجديدة
            lc_messages.append(HumanMessage(content=message))

            # إنشاء الـ State
            initial_state: AgentState = {
                "messages": lc_messages,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "patient_phone": None,
                "booking_doctor_id": None,
                "booking_date": None,
                "booking_time": None,
                "booking_notes": None,
                "intent": None,
                "booking_step": None,
                "is_complete": False,
            }

            # تشغيل الـ Agent
            result = agent_graph.invoke(initial_state)

            # استخراج الرد
            final_messages = result["messages"]
            ai_response = ""
            for msg in reversed(final_messages):
                if isinstance(msg, AIMessage) and msg.content:
                    ai_response = msg.content
                    break

            # حفظ الرسالتين في الـ DB
            db.add(ChatMessage(
                patient_id=patient_id,
                session_id=session_id,
                role=MessageRole.user,
                content=message,
            ))
            db.add(ChatMessage(
                patient_id=patient_id,
                session_id=session_id,
                role=MessageRole.assistant,
                content=ai_response,
            ))
            db.commit()

            return {
                "session_id": session_id,
                "response": ai_response,
                "intent": result.get("intent", "other"),
            }

        finally:
            db.close()


chat_service = ChatService()