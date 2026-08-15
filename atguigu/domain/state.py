import datetime
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Any
from atguigu.domain.contexts import TaskContext, SystemContext
from atguigu.domain.messages import FocusedObject, UserMessage, BotMessage



@dataclass(slots=True)
class Turn:
    turn_id:str
    user_message:UserMessage
    bot_messages:list[BotMessage]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_message": self.user_message.to_dict(),
            "bot_message": [bot_message.to_dict() for bot_message in self.bot_messages],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Turn":

        return cls(
            turn_id = data["turn_id"],
            user_message = UserMessage.from_dict(data["user_message"]),
            bot_messages = [BotMessage.from_dict(bot_message) for bot_message in data["bot_messages"]],
        )

@dataclass(slots=True)
class Session:
    session_id:str
    started_at:float
    last_activity_at:float
    closed_at:float | None = None
    turns:list[Turn] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "last_activity_at": self.last_activity_at,
            "closed_at": self.closed_at,
            "turns": [turn.to_dict() for turn in self.turns],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id = data["session_id"],
            started_at = data["started_at"],
            last_activity_at = data["last_activity_at"],
            closed_at = data["closed_at"],
            turns = [Turn.from_dict(turn) for turn in data["turns"]],
        )

@dataclass(slots=True)
class DialogueState:
    sender_id:str
    active_task:TaskContext | None = None
    paused_tasks:list[TaskContext]  = field(default_factory=list)
    active_system_task:SystemContext | None = None
    focused_object:FocusedObject | None = None
    sessions:list[Session] = field(default_factory=list)
    current_session_id:str | None = None
    pending_turn:Turn | None = None


    def to_dict(self) -> Dict[str, Any]:
        return {
            "sender_id": self.sender_id,
            "active_task": self.active_task.to_dict() if self.active_task else None,
            "paused_tasks": [paused_task.to_dict() for paused_task in self.paused_tasks],
            "active_system_task": self.active_system_task.to_dict() if self.active_system_task else None,
            "focused_object": self.focused_object.to_dict() if self.focused_object else None,
            "sessions": [session_context.to_dict() for session_context in self.sessions],
            "current_session_id": self.current_session_id,
            "pending_turn": self.pending_turn.to_dict() if self.pending_turn else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DialogueState":
        return cls(
            sender_id = data["sender_id"],
            active_task = TaskContext.from_dict(data["active_task"]) if data.get("active_task") else None,
            paused_tasks=[TaskContext.from_dict(paused_task_dict) for paused_task_dict in data['paused_tasks']],
            active_system_task=SystemContext.from_dict(data['active_system_task']) if data.get(
                'active_system_task') else None,
            focused_object=FocusedObject.from_dict(data['focused_object']) if data.get('focused_object') else None,
            sessions=[Session.from_dict(session_dict) for session_dict in data['sessions']],
            current_session_id=data.get('current_session_id'),
            pending_turn=Turn.from_dict(data['pending_turn']) if data.get('pending_turn') else None
        )


    def start_active_system_task(self, active_system_task: SystemContext):
        """
        开启系统流程
        :param active_system_task:
        :return:
        """
        self.active_system_task = active_system_task

    def end_active_system_task(self):
        """
        结束系统流程
        """
        self.active_system_task = None


    def start_active_task(self,active_task: TaskContext):
        """
        开启业务任务
        """
        self.active_task = active_task

    def end_active_task(self):
        """
        结束业务任务
        """
        self.active_task = None

    def interrupted_active_task(self):
        self.paused_tasks.append(self.active_task)
        self.active_task = None

    def resume_task(self,flow_id:str | None):
        """
        恢复业务流程：任务ID
        """
        if not flow_id:
            task = self.paused_tasks.pop()
            self.active_task = task
            return

        for task in self.paused_tasks:
            if task.flow_id == flow_id:
                self.active_task = task
                self.paused_tasks.remove(task)
                return

    def cancel_active_task(self):
      self.active_task = None
      self.active_system_task = None


    def set_slots(self,slots:Dict[str,Any]):
        """
        设置槽位
        """
        self.active_task.slots.update(slots)

    def remove_slot(self,slot_name:str):
        self.active_task.slots.pop(slot_name)

    def current_task(self):
        return self.active_system_task or self.active_task

    def current_session(self) -> Session | None:
       for session in self.sessions:
           if self.current_session_id == session.session_id:
               return session

       return None

    def start_session(self):
        """
        开启session
        """
        if self.current_session() is None:
            now = datetime.datetime.now()
            session = Session(session_id=str(uuid.uuid4()),started_at=now,last_activity_at=now)
            self.sessions.append(session)
            self.current_session_id = session.session_id

    def close_session(self):
        if self.current_session() is not None:
            self.current_session().closed_at = time.time()
            self.current_session_id = None


    def reset_running_state_for_new_session(self):
        """
            session会话超时（60min超时时间）
            :return:
            """
        self.active_task = None
        self.active_system_task = None
        self.paused_tasks = []
        self.focused_object = None
        self.pending_turn = None
        self.current_session_id = None

        # --------------turn相关的--------------------------

    def begin_turn(self, message: UserMessage):
        if self.current_session():
            turn = Turn(turn_id=str(uuid.uuid4()), user_message=message, bot_messages=[])
            self.pending_turn = turn

    def commit_turn(self):
        if self.current_session():
            self.current_session().turns.append(self.pending_turn)
            self.pending_turn = None

        # --------------FocusedObject相关的--------------------------

    def set_focused_object(self, focused_object: FocusedObject):
        self.focused_object = focused_object





















