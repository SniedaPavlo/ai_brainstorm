import json
from datetime import datetime
from agents import AGENTS, Agent
from llm import chat
from config import MAX_ROUNDS

# ── Системный промпт модератора ──
MODERATOR_SYSTEM = (
    "Ты — модератор стратегической сессии. Твоя задача после каждого раунда:\n"
    "1. Выделить 2-3 КЛЮЧЕВЫХ КОНФЛИКТА или разногласия между экспертами.\n"
    "2. Отметить СЛЕПЫЕ ЗОНЫ — что эксперты упустили или недостаточно раскрыли.\n"
    "3. Сформулировать ФОКУС следующего раунда — конкретные вопросы, на которые эксперты должны ответить.\n"
    "Будь жёстким и конкретным. Не хвали — направляй."
)

FINAL_SYSTEM = (
    "Ты — опытный продакт-менеджер. На основе полной дискуссии экспертов "
    "составь финальный action-plan. Ответь строго в JSON без markdown-обёрток:\n"
    '{\n'
    '  "title": "короткое название",\n'
    '  "summary": "итог в 2-3 абзаца",\n'
    '  "key_decisions": ["решение 1", ...],\n'
    '  "action_plan": [\n'
    '    {"priority": "P0/P1/P2", "action": "что делать", "owner_role": "кто", "timeframe": "срок"}\n'
    '  ],\n'
    '  "risks": ["риск 1", ...],\n'
    '  "open_questions": ["вопрос 1", ...]\n'
    '}'
)


def _moderate(history: str, round_num: int, total_rounds: int) -> str:
    """Модератор анализирует раунд и задаёт фокус для следующего."""
    prompt = (
        f"{history}\n---\n"
        f"Раунд {round_num} из {total_rounds} завершён.\n"
        f"Выдели ключевые конфликты, слепые зоны и сформулируй "
        f"конкретные вопросы для следующего раунда."
    )
    return chat(prompt=prompt, role_system=MODERATOR_SYSTEM)


def _make_agent_prompt(history: str, agent: Agent, round_num: int, total_rounds: int, moderator_focus: str) -> str:
    """Формирует промпт для агента с учётом фокуса модератора."""
    is_final = round_num == total_rounds
    parts = [
        f"{history}\n---\n",
        f"Ты — {agent.role}. Раунд {round_num} из {total_rounds}.\n",
    ]
    if moderator_focus:
        parts.append(
            f"МОДЕРАТОР ЗАДАЛ ФОКУС ЭТОГО РАУНДА:\n{moderator_focus}\n"
            f"Обязательно ответь на вопросы модератора с позиции своей роли.\n"
        )
    parts.append(
        "Проанализируй всю дискуссию. Критикуй конкретные слабые места "
        "в ответах других экспертов, предложи улучшения.\n"
    )
    if is_final:
        parts.append("Это ФИНАЛЬНЫЙ раунд — дай итоговые рекомендации, расставь приоритеты.")
    return "".join(parts)


def run_debate(idea: str, agent_names: list[str] | None = None, rounds: int = MAX_ROUNDS) -> str:
    agents: list[Agent] = []
    for name in (agent_names or list(AGENTS.keys())):
        if name not in AGENTS:
            raise ValueError(f"Агент '{name}' не найден. Доступны: {list(AGENTS.keys())}")
        agents.append(AGENTS[name])

    full_log = {
        "idea": idea,
        "agents": [{"name": a.name, "role": a.role} for a in agents],
        "started_at": datetime.now().isoformat(),
        "rounds": [],
    }

    history = f"## Исходная идея\n{idea}\n"
    moderator_focus = ""
    print(f"\n{'='*60}\n📌 Идея: {idea}\n{'='*60}")

    for round_num in range(1, rounds + 1):
        print(f"\n{'─'*60}\n🔄 РАУНД {round_num}/{rounds}")
        if moderator_focus:
            print(f"🎯 Фокус модератора:\n{moderator_focus[:300]}...")

        round_data = {"round": round_num, "moderator_focus": moderator_focus, "responses": []}

        # ── Агенты отвечают ──
        for agent in agents:
            prompt = _make_agent_prompt(history, agent, round_num, rounds, moderator_focus)
            print(f"\n🤖 [{agent.role}] думает...")
            response = agent.respond(prompt)
            history += f"\n### [{agent.role}] (раунд {round_num})\n{response}\n"
            print(f"✅ [{agent.role}]:\n{response[:200]}...")

            round_data["responses"].append({
                "agent": agent.name, "role": agent.role, "response": response,
            })

        # ── Модератор направляет (кроме последнего раунда) ──
        if round_num < rounds:
            print(f"\n🧑‍⚖️ Модератор анализирует раунд {round_num}...")
            moderator_focus = _moderate(history, round_num, rounds)
            history += f"\n### [Модератор] (после раунда {round_num})\n{moderator_focus}\n"
            print(f"🎯 Модератор:\n{moderator_focus[:300]}...")
            round_data["moderator_summary"] = moderator_focus

        full_log["rounds"].append(round_data)

    full_log["finished_at"] = datetime.now().isoformat()

    # ── Сохраняем полный лог ──
    with open("debate_full_log.json", "w", encoding="utf-8") as f:
        json.dump(full_log, f, ensure_ascii=False, indent=2)
    print("\n💾 Полный лог → debate_full_log.json")

    # ── Финальный синтез ──
    print("\n🧠 Генерирую финальный action-plan...")
    final_prompt = f"{history}\n---\nСоставь финальный action-plan на основе всей дискуссии."
    final_raw = chat(prompt=final_prompt, role_system=FINAL_SYSTEM)

    clean = final_raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        final_data = json.loads(clean)
    except json.JSONDecodeError:
        final_data = {"raw_summary": clean}

    final_output = {
        "idea_original": idea,
        "generated_at": datetime.now().isoformat(),
        "final_version": final_data,
    }

    with open("debate_final.json", "w", encoding="utf-8") as f:
        json.dump(final_output, f, ensure_ascii=False, indent=2)
    print("💾 Финальный план → debate_final.json")

    return history