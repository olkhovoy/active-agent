# -*- coding: utf-8 -*-
import json
from typing import List, Dict, Any
from ..orchestrator import LLMClient
from .user_profile import UserProfile
from .token_discovery import TokenInfo

class UMCScoringAgent:
    """
    Агент для оценки токенов по методологии UMC (Coherence/Stimulation),
    с учетом профиля пользователя для персонализации.
    """
    def __init__(self, llm_client: LLMClient, config: Dict, user_profile: UserProfile):
        self.config = config.get('scoring', {})
        self.llm = llm_client
        self.user_profile = user_profile
        # Загружаем промпты для оценки
        self.coherence_prompt = self._load_prompt('prompts/coherence_prompt.md')
        self.stimulation_prompt = self._load_prompt('prompts/stimulation_prompt.md')
        print("UMC Scoring Agent initialized.")

    def _load_prompt(self, file_path: str) -> str:
        """Загружает текст промпта из файла."""
        try:
            # Путь относительно текущего файла
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, '..', file_path) # Выходим из erc20 в agents
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[Warning] Prompt file not found at {full_path}. Using default prompt.")
            # Возвращаем дефолтный промпт, если файл не найден
            if 'coherence' in file_path:
                return "Analyze the coherence of the provided information."
            else:
                return "Analyze the stimulation potential based on the user profile and token data."

    async def run(self, informational_data: Dict, onchain_data: Dict) -> List[Dict]:
        """
        Запускает оценку для всех токенов, по которым были собраны данные.
        """
        assessments = []
        for contract_address, info_item in informational_data.items():
            onchain_item = onchain_data.get(contract_address)
            
            if not onchain_item or "error" in info_item or "error" in onchain_item:
                print(f"Skipping scoring for {contract_address} due to missing data.")
                continue

            token_info = info_item.get('token_info')
            print(f"Scoring token: {token_info.name} ({token_info.symbol})")
            
            # Собираем все данные в один контекст
            full_context = {
                "token_info": info_item['token_info'].__dict__,
                "web_summary": info_item['summary'],
                "web_docs_count": len(info_item['docs']),
                "onchain_analysis": {
                    "source_code": onchain_item.get('source_code', {}),
                    "holders": onchain_item.get('holders', {}),
                    "transactions": onchain_item.get('transactions', {})
                }
            }
            
            # 1. Оценка Coherence
            coherence_score = await self.rate_coherence(full_context)
            
            # 2. Оценка Stimulation
            stimulation_score = await self.rate_stimulation(full_context)
            
            assessments.append({
                "contract_address": contract_address,
                "symbol": token_info.symbol,
                "name": token_info.name,
                "scores": {
                    "coherence": coherence_score,
                    "stimulation": stimulation_score,
                },
                "final_recommendation": self._generate_recommendation(coherence_score, stimulation_score)
            })
            
        return assessments

    async def rate_coherence(self, context: Dict) -> Dict:
        """Оценивает связность и непротиворечивость информации о токене."""
        user_prompt = json.dumps(context, indent=2, ensure_ascii=False)
        
        try:
            result = self.llm.complete_json(system=self.coherence_prompt, user=user_prompt)
            # Валидация результата
            return {
                "score": max(0, min(100, int(result.get("score", 50)))),
                "rationale": result.get("rationale", "No rationale provided."),
                "positive_points": result.get("positive_points", []),
                "negative_points": result.get("negative_points", [])
            }
        except Exception as e:
            print(f"[Error] Coherence rating failed: {e}")
            return {"score": 0, "rationale": "Failed to process.", "positive_points": [], "negative_points": []}

    async def rate_stimulation(self, context: Dict) -> Dict:
        """Оценивает потенциал и релевантность токена для пользователя."""
        # Добавляем профиль пользователя в контекст
        full_context = {
            "user_profile": self.user_profile.to_dict(),
            "token_data": context
        }
        user_prompt = json.dumps(full_context, indent=2, ensure_ascii=False)
        
        try:
            result = self.llm.complete_json(system=self.stimulation_prompt, user=user_prompt)
            # Валидация результата
            return {
                "score": max(0, min(100, int(result.get("score", 50)))),
                "rationale": result.get("rationale", "No rationale provided."),
                "alignment_with_interests": result.get("alignment_with_interests", "N/A"),
                "risk_assessment": result.get("risk_assessment", "N/A")
            }
        except Exception as e:
            print(f"[Error] Stimulation rating failed: {e}")
            return {"score": 0, "rationale": "Failed to process.", "alignment_with_interests": "N/A", "risk_assessment": "N/A"}

    def _generate_recommendation(self, coherence: Dict, stimulation: Dict) -> str:
        """Генерирует финальную рекомендацию на основе скорингов."""
        cs = coherence['score']
        ss = stimulation['score']

        if cs < 40:
            return "AVOID: Low coherence suggests internal inconsistencies or lack of transparency."
        if cs < 60 and ss < 60:
            return "NEUTRAL: The project appears somewhat consistent but lacks a strong stimulation factor for you."
        if cs >= 60 and ss >= 75:
            return "TOP PICK: High coherence and strong alignment with your profile. Worth deeper investigation."
        if cs >= 70 and ss >= 60:
            return "INTERESTING: Appears to be a solid and relevant project."
        
        return "NEUTRAL: Requires further review."

# Для автономного запуска и тестирования нам нужны мок-объекты
import os

class MockLLMClient:
    def complete_json(self, system: str, user: str) -> Dict:
        if "coherence" in system.lower():
            return { "score": 75, "rationale": "Test coherence rationale.", "positive_points": ["Verified contract"], "negative_points": ["Low social media activity"]}
        else:
            return { "score": 80, "rationale": "Test stimulation rationale.", "alignment_with_interests": "High", "risk_assessment": "Medium"}

async def main():
    print("--- Running UMC Scoring Agent Standalone ---")
    
    config = {'scoring': {}}
    user_profile = UserProfile()
    llm_client = MockLLMClient()
    
    # Мок-данные от других агентов
    token_info_uni = TokenInfo(contract_address="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", name="Uniswap", symbol="UNI")
    informational_data = {
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": {
            "token_info": token_info_uni, "summary": "A leading decentralized exchange.", "docs": [{}]
        }
    }
    onchain_data = {
        "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984": {
            "source_code": {"is_verified": True}, "holders": {}, "transactions": {}
        }
    }

    # Создаем и запускаем агент
    agent = UMCScoringAgent(llm_client, config, user_profile)
    assessments = await agent.run(informational_data, onchain_data)

    print("\n--- Scoring Results ---")
    print(json.dumps(assessments, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
