# -*- coding: utf-8 -*-
import argparse
import json
import yaml
import os
import asyncio
from typing import List, Dict

# Локальные импорты из текущего проекта
from .token_discovery import TokenDiscoveryAgent, TokenInfo
from .user_profile import UserProfile, UserProfileManager
from .information_retrieval_agent import InformationRetrievalAgent
from .onchain_analysis_agent import OnchainAnalysisAgent
from .umc_scoring_agent import UMCScoringAgent
from ..orchestrator import LLMClient, load_config

class TokenOrchestrator:
    """
    Оркестратор для комплексной, агент-ориентированной оценки ERC-20 токенов
    с использованием UMC-методологии и персонализации.
    """
    def __init__(self, config_path: str, profile_path: str):
        self.config = load_config(config_path)
        self.user_profile = UserProfileManager(profile_path).load_profile()
        
        # Инициализация LLM клиента для всех агентов
        self.llm = LLMClient()
        
        # Инициализация агентов
        self.discovery_agent = TokenDiscoveryAgent(self.config)
        self.retrieval_agent = InformationRetrievalAgent(self.llm, self.config)
        self.onchain_agent = OnchainAnalysisAgent(self.config)
        self.scoring_agent = UMCScoringAgent(self.llm, self.config, self.user_profile)
        
        print("Оркестратор инициализирован с профилем пользователя:")
        print(yaml.dump(self.user_profile.to_dict(), allow_unicode=True))

    async def run(self, max_tokens: int = 10):
        """
        Запускает полный цикл обнаружения, анализа и оценки токенов.
        """
        print("\n--- 1. Обнаружение токенов ---")
        discovered_tokens = await self.discovery_agent.run(limit=max_tokens)
        
        if not discovered_tokens:
            print("Не удалось обнаружить новые токены. Завершение работы.")
            return
            
        print(f"Обнаружено {len(discovered_tokens)} токенов для анализа.")
        for token in discovered_tokens[:5]:
             print(f"  - {token.name} ({token.symbol})")

        print("\n--- 2. Сбор информации (Web, Документация) ---")
        informational_data = await self.retrieval_agent.run(discovered_tokens)

        print("\n--- 3. Анализ ончейн-данных ---")
        onchain_data = await self.onchain_agent.run(discovered_tokens)

        print("\n--- 4. UMC Оценка и Персонализация ---")
        final_assessments = await self.scoring_agent.run(informational_data, onchain_data)
        
        print("\n--- Результаты Оценки ---")
        print(json.dumps(final_assessments, indent=2, ensure_ascii=False))
        
        self.save_results(final_assessments)

    def save_results(self, results: List[Dict]):
        """Сохраняет финальные оценки в JSON файл."""
        output_dir = self.config.get("export", {}).get("output_directory", "token_evaluation_export")
        os.makedirs(output_dir, exist_ok=True)
        
        # Используем timestamp для уникальности имени файла
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(output_dir, f"umc_assessment_{timestamp}.json")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"Результаты сохранены в {file_path}")


async def main():
    parser = argparse.ArgumentParser(description="Запуск системы оценки ERC-20 токенов.")
    parser.add_argument('--config', type=str, default='config.yaml', help='Путь к файлу конфигурации.')
    parser.add_argument('--profile', type=str, default='user_profile.yaml', help='Путь к файлу профиля пользователя.')
    parser.add_argument('--max-tokens', type=int, default=3, help='Максимальное количество токенов для анализа.')
    args = parser.parse_args()

    # Убедимся, что пути к файлам находятся в директории erc20
    base_dir = os.path.dirname(__file__)
    config_path = os.path.join(base_dir, args.config)
    profile_path = os.path.join(base_dir, args.profile)

    if not os.path.exists(config_path):
        print(f"[ERROR] Config file not found at {config_path}")
        return
        
    if not os.path.exists(profile_path):
        print(f"[INFO] Profile file not found at {profile_path}, creating a default one.")
        UserProfileManager(profile_path).save_profile(UserProfile())

    orchestrator = TokenOrchestrator(config_path, profile_path)
    await orchestrator.run(max_tokens=args.max_tokens)


if __name__ == "__main__":
    asyncio.run(main())
