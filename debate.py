import json
from datetime import datetime
from agents import AGENTS, Agent
from llm import chat
from config import MAX_ROUNDS


def run_debate(idea: str, agent_names: list[str] | None = None, rounds: int = MAX_ROUNDS) -> str:
    """
    Запускает рекурсивную дискуссию агентов.
    Сохраняет:
      - debate_full_log.json  — полный протокол всех ответов
      - debate_final.json     — финальная улучшенная версия идеи
    """
    agents: list[Agent] = []
    for name in (agent_names or list(AGENTS.keys())):
        if name not in AGENTS:
            raise ValueError(f"Агент '{name}' не найден. Доступны: {list(AGENTS.keys())}")
        agents.append(AGENTS[name])

    # ── Структура для полного лога ──
    full_log = {
        "idea": idea,
        "agents": [{"name": a.name, "role": a.role} for a in agents],
        "started_at": datetime.now().isoformat(),
        "rounds": [],
    }

    history = f"## Исходная идея\n{idea}\n"
    print(f"\n{'='*60}\n📌 Идея: {idea}\n{'='*60}")

    for round_num in range(1, rounds + 1):
        print(f"\n--- Раунд {round_num}/{rounds} ---")
        round_data = {"round": round_num, "responses": []}

        for agent in agents:
            is_final = round_num == rounds
            prompt = (
                f"{history}\n---\n"
                f"Ты — {agent.role}. Это раунд {round_num} из {rounds}.\n"
                f"Проанализируй всю дискуссию выше. "
                f"Критикуй слабые стороны предыдущих ответов, "
                f"предложи конкретные улучшения идеи с позиции своей роли.\n"
                f"{'Это финальный раунд — дай итоговую сводку своих рекомендаций.' if is_final else ''}"
            )
            print(f"\n🤖 [{agent.role}] думает...")
            response = agent.respond(prompt)
            history += f"\n### [{agent.role}] (раунд {round_num})\n{response}\n"
            print(f"✅ [{agent.role}]:\n{response[:200]}...")

            round_data["responses"].append({
                "agent": agent.name,
                "role": agent.role,
                "response": response,
            })

        full_log["rounds"].append(round_data)

    full_log["finished_at"] = datetime.now().isoformat()

    # ── Сохраняем полный лог ──
    with open("debate_full_log.json", "w", encoding="utf-8") as f:
        json.dump(full_log, f, ensure_ascii=False, indent=2)
    print("\n💾 Полный лог → debate_full_log.json")

    # ── Генерируем финальную сводку через LLM ──
    print("\n🧠 Генерирую финальную версию идеи...")
    summary_prompt = (
        f"{history}\n---\n"
        f"Ты — модератор. Выше — полная дискуссия экспертов по идее.\n"
        f"Составь ФИНАЛЬНУЮ улучшенную версию идеи, объединив лучшие предложения всех участников.\n"
        f"Ответь строго в JSON:\n"
        f'{{\n'
        f'  "title": "короткое название идеи",\n'
        f'  "summary": "описание улучшенной идеи в 2-3 абзаца",\n'
        f'  "key_features": ["фича 1", "фича 2", ...],\n'
        f'  "target_audience": "целевая аудитория",\n'
        f'  "monetization": "модель монетизации",\n'
        f'  "tech_stack": "рекомендуемый стек",\n'
        f'  "risks": ["риск 1", "риск 2"],\n'
        f'  "next_steps": ["шаг 1", "шаг 2", "шаг 3"]\n'
        f'}}\n'
        f"Только JSON, без markdown-обёрток."
    )

    final_raw = chat(prompt=summary_prompt, role_system="Ты — опытный модератор и продакт-менеджер.")

    # Пробуем распарсить JSON, если LLM обернул в ```
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
    print("💾 Финальная версия → debate_final.json")

    return history