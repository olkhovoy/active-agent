# -*- coding: utf-8 -*-
import asyncio
from typing import List, Dict, Any
from aiohttp import ClientSession
from duckduckgo_search import AsyncDDGS
from ..orchestrator import LLMClient
from .token_discovery import TokenInfo

class InformationRetrievalAgent:
    """
    Агент для сбора текстовой информации о токенах из веба.
    Использует поиск DuckDuckGo для нахождения новостей, статей и документации.
    """
    def __init__(self, llm_client: LLMClient, config: Dict):
        self.config = config.get('retrieval', {})
        self.llm = llm_client
        self.search_client = AsyncDDGS()
        print("Information Retrieval Agent initialized.")

    async def run(self, tokens: List[TokenInfo]) -> Dict[str, Dict[str, Any]]:
        """
        Запускает асинхронный поиск информации для списка токенов.
        
        Возвращает словарь, где ключ - адрес контракта, 
        а значение - собранная информация.
        """
        tasks = [self.get_information_for_token(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем результаты в словарь
        final_data = {}
        for i, res in enumerate(results):
            token_address = tokens[i].contract_address
            if isinstance(res, Exception):
                print(f"[Warning] Error retrieving info for {tokens[i].symbol}: {res}")
                final_data[token_address] = {"error": str(res), "docs": []}
            else:
                final_data[token_address] = res
        
        return final_data

    async def get_information_for_token(self, token: TokenInfo) -> Dict[str, Any]:
        """
        Собирает и обрабатывает информацию для одного токена.
        """
        print(f"Retrieving information for {token.name} ({token.symbol})...")
        max_results = self.config.get('max_search_results_per_query', 5)
        
        # Формируем поисковые запросы
        queries = [
            f"{token.name} ({token.symbol}) crypto review",
            f"{token.name} token official documentation whitepaper",
            f"{token.name} ({token.symbol}) news announcements",
            f"what is {token.name} ({token.symbol})",
            f"{token.symbol} token contract audit"
        ]
        
        # Ищем по всем запросам
        search_tasks = [self.search_client.atext(q, max_results=max_results) for q in queries]
        search_results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Собираем уникальные ссылки и их содержимое
        unique_urls = set()
        docs = []
        for i, results in enumerate(search_results_list):
            if isinstance(results, Exception):
                print(f"[Warning] Search query failed for {token.symbol}: {queries[i]}")
                continue
            
            for res in results:
                url = res.get('href')
                if url and url not in unique_urls:
                    unique_urls.add(url)
                    docs.append({
                        "source": url,
                        "title": res.get('title', 'N/A'),
                        "snippet": res.get('body', ''),
                        "query": queries[i]
                    })
        
        # TODO: Добавить логику скрапинга полного текста со страниц
        
        print(f"  > Found {len(docs)} unique documents for {token.symbol}.")

        # Используем LLM для саммаризации и выделения ключевой информации
        summary = await self.summarize_docs(token, docs)
        
        return {
            "token_info": token,
            "summary": summary,
            "docs": docs
        }

    async def summarize_docs(self, token: TokenInfo, docs: List[Dict]) -> str:
        """
        Использует LLM для создания краткой выжимки из найденных документов.
        """
        if not docs:
            return "No information found."
            
        # Формируем контекст для LLM
        context = "\n\n".join([f"Source: {d['source']}\nTitle: {d['title']}\nSnippet: {d['snippet']}" for d in docs])
        
        # Ограничиваем размер контекста, чтобы не превысить лимит модели
        max_context_len = self.config.get('llm_max_context_length', 8000)
        context = context[:max_context_len]

        system_prompt = """
        You are a crypto analyst. Based on the provided search results, create a concise summary for the token. 
        Focus on the project's purpose, its technology, recent news, and any mention of team or partnerships.
        Ignore advertisements and irrelevant content. Start with a one-sentence overview.
        """
        user_prompt = f"Token to summarize: {token.name} ({token.symbol})\n\nSearch Results:\n{context}"

        try:
            # Используем базовый метод complete, а не complete_json, т.к. нам нужен текст
            resp = self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                temperature=0.1,
                max_tokens=self.config.get('llm_summary_max_tokens', 500)
            )
            summary_text = resp.choices[0].message.content.strip()
            return summary_text
        except Exception as e:
            print(f"[Error] LLM summarization failed for {token.symbol}: {e}")
            return "Failed to generate summary."

# Пример использования
async def main():
    print("--- Running Information Retrieval Agent Standalone ---")
    
    # Мок-объекты для автономного запуска
    class MockLLMClient:
        class MockChatCompletion:
            def __init__(self, text):
                self.choices = [type('Choice', (), {'message': type('Message', (), {'content': text})})()]
        def __init__(self):
            self.model = "mock_model"
            self.client = type('Client', (), {
                'chat': type('Chat', (), {
                    'completions': type('Completions', (), {'create': self.mock_create})
                })
            })()
        def mock_create(self, **kwargs):
            return self.MockChatCompletion("This is a test summary from the mock LLM.")

    config = {
        'retrieval': {
            'max_search_results_per_query': 3,
            'llm_max_context_length': 4000,
            'llm_summary_max_tokens': 150
        }
    }
    
    test_tokens = [
        TokenInfo(contract_address="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", name="Uniswap", symbol="UNI"),
        TokenInfo(contract_address="0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", name="Aave", symbol="AAVE")
    ]

    agent = InformationRetrievalAgent(llm_client=MockLLMClient(), config=config)
    results = await agent.run(test_tokens)

    print("\n--- Retrieval Results ---")
    for contract, data in results.items():
        print(f"\nToken: {data['token_info'].symbol}")
        print(f"Summary: {data['summary']}")
        print(f"Documents Found: {len(data['docs'])}")
        # for doc in data['docs'][:2]:
        #     print(f"  - {doc['title']}")

if __name__ == "__main__":
    asyncio.run(main())
