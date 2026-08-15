from dataclasses import dataclass

@dataclass(slots=True)
class FlowStepLink:
    target: str


@dataclass(slots=True)
class FlowStepStaticLink(FlowStepLink):
    pass

@dataclass(slots=True)
class FlowStepConditionalLink(FlowStepLink):
    condition: str


@dataclass(slots=True)
class FlowStepFallbackLink(FlowStepLink):
    pass
