#!/usr/bin/env python3
"""
Multi-Agent Debate MVP
Запуск: python main.py

Настройки в config.py: IDEA, MAX_ROUNDS, модель, ключ.
"""
from config import IDEA
from debate import run_debate


def main():
    result = run_debate(IDEA)

    print("\n" + "=" * 60)
    print("📋 ПОЛНЫЙ ПРОТОКОЛ ДИСКУССИИ")
    print("=" * 60)
    print(result)

    with open("debate_result.md", "w") as f:
        f.write(result)
    print("\n💾 Результат сохранён в debate_result.md")


if __name__ == "__main__":
    main()