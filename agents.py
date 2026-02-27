from dataclasses import dataclass
from llm import chat


@dataclass
class Agent:
    name: str
    role: str            # короткое описание роли
    system_prompt: str   # полный системный промпт
    model: str = ""      # можно задать свою модель на агента

    def respond(self, prompt: str, model_override: str = "") -> str:
        model = model_override or self.model or ""
        kwargs = {"prompt": prompt, "role_system": self.system_prompt}
        if model:
            kwargs["model"] = model
        return chat(**kwargs)


# ── Реестр агентов (добавляй новых здесь) ────────────────────────

AGENTS: dict[str, Agent] = {}


def register(name: str, role: str, system_prompt: str, model: str = ""):
    AGENTS[name] = Agent(name=name, role=role, system_prompt=system_prompt, model=model)


# --- Встроенные агенты ---

register(
    "marketer",
    role="Маркетолог",
    system_prompt=(
        "Ты — опытный маркетолог. Оценивай идеи с точки зрения рынка, "
        "целевой аудитории, позиционирования и монетизации. "
        "Критикуй слабые места и предлагай конкретные улучшения."
    ),
)

register(
    "developer",
    role="Программист",
    system_prompt=(
        "Ты — senior-разработчик. Оценивай техническую реализуемость идей, "
        "стек технологий, архитектуру, сроки и риски. "
        "Критикуй нереалистичное и предлагай практичные альтернативы."
    ),
)

register(
    "creative",
    role="Креативный идеатор",
    system_prompt=(
        "Ты — креативный директор. Ищи нестандартные углы, wow-эффекты, "
        "уникальные фичи и способы выделиться. "
        "Критикуй скучное и генерируй свежие идеи."
    ),
)