from abc import ABC, abstractmethod
import logging

class BaseTask(ABC):
    def __init__(self):
        self.name = "未命名任务"
        self.description = "无描述"
        self.priority = 0
        self.logger = logging.getLogger('HwlloETS')

    @abstractmethod
    async def execute(self, **kwargs):
        pass

    def get_info(self):
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority
        }
