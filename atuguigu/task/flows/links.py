"""
流程步骤边

1.顺序边 -- next:str
2.条件边 -- if "表达式" then str
3.兜底边 -- else   str
"""

from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class FlowStepLink:
    """
    抽象基类(边）
    """
    target: str

    @classmethod
    def from_dict(cls, link_data: str | list[dict[str, Any]]) -> "list[FlowStepLink]":
        loaded_links: list[FlowStepLink] = []
        if isinstance(link_data, str):
            loaded_links.append(FlowStepStaticLink(target=link_data))
        else:
            for link_dict in link_data:
                if "if" in link_dict:
                    loaded_links.append(FlowStepConditionLink(condition=link_dict['if'], target=link_dict['then']))
                else:
                    loaded_links.append(FlowStepFallbackLink(target=link_dict['else']))
        return loaded_links


@dataclass(slots=True)
class FlowStepStaticLink(FlowStepLink):
    pass

@dataclass(slots=True)
class FlowStepConditionLink(FlowStepLink):
    condition: str

@dataclass(slots=True)
class FlowStepFallbackLink(FlowStepLink):
    pass





