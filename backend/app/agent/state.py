# backend/app/agent/state.py

from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    # تاريخ المحادثة كامل
    messages: Annotated[List[BaseMessage], operator.add]

    # معلومات البيشنت
    patient_id: Optional[int]
    patient_name: Optional[str]
    patient_phone: Optional[str]

    # معلومات الحجز اللي بيتجمع أثناء المحادثة
    booking_doctor_id: Optional[int]
    booking_date: Optional[str]
    booking_time: Optional[str]
    booking_notes: Optional[str]

    # حالة الـ Agent
    intent: Optional[str]        # "booking" | "query" | "cancel" | "other"
    booking_step: Optional[str]  # "ask_doctor" | "ask_date" | "ask_time" | "confirm"
    is_complete: bool