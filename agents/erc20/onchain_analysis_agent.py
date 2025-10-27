# -*- coding: utf-8 -*-
import os
import asyncio
from typing import List, Dict, Any
import requests
from .token_discovery import TokenInfo

class OnchainAnalysisAgent:
    """
    Агент для сбора и анализа ончейн-данных по токенам.
    Использует Etherscan API для получения информации о контракте,
    транзакциях и держателях.
    """
    def __init__(self, config: Dict):
        self.config = config.get('onchain_analysis', {})
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.base_url = 'https://api.etherscan.io/api'
        self.session = requests.Session()
        print("Onchain Analysis Agent initialized.")

    async def run(self, tokens: List[TokenInfo]) -> Dict[str, Dict[str, Any]]:
        """
        Запускает асинхронный сбор ончейн-данных для списка токенов.
        """
        tasks = [self.get_onchain_data(token) for token in tokens]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        final_data = {}
        for i, res in enumerate(results):
            token_address = tokens[i].contract_address
            if isinstance(res, Exception):
                print(f"[Warning] Error analyzing onchain data for {tokens[i].symbol}: {res}")
                final_data[token_address] = {"error": str(res)}
            else:
                final_data[token_address] = res
        
        return final_data

    async def get_onchain_data(self, token: TokenInfo) -> Dict[str, Any]:
        """
        Собирает ончейн-данные для одного токена.
        """
        print(f"Analyzing onchain data for {token.name} ({token.symbol})...")
        contract_address = token.contract_address
        
        # Асинхронно выполняем все запросы к Etherscan
        tasks = {
            'source_code': self._get_contract_source_code(contract_address),
            'holders': self._get_top_holders(contract_address),
            'transactions': self._get_transaction_count(contract_address)
        }
        
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Собираем результаты
        onchain_metrics = dict(zip(tasks.keys(), results))
        
        # Обрабатываем ошибки, если они были
        for key, value in onchain_metrics.items():
            if isinstance(value, Exception):
                print(f"[Warning] Etherscan API call failed for {key} on {token.symbol}: {value}")
                onchain_metrics[key] = {"error": str(value)}
        
        # Добавляем базовую информацию
        onchain_metrics['token_info'] = token
        
        print(f"  > Onchain analysis complete for {token.symbol}.")
        
        return onchain_metrics

    async def _api_request(self, params: Dict) -> Any:
        """Универсальная обертка для запросов к Etherscan API."""
        if not self.etherscan_api_key:
            raise ValueError("Etherscan API key is not configured.")
        
        params['apikey'] = self.etherscan_api_key
        
        loop = asyncio.get_event_loop()
        try:
            # Выполняем синхронный запрос в отдельном потоке
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.get(self.base_url, params=params, timeout=20)
            )
            response.raise_for_status()
            data = response.json()
            
            # Проверка ответа от Etherscan
            if data.get('status') == '1' or (isinstance(data.get('result'), list) and data.get('message') == 'OK'):
                return data['result']
            else:
                # Etherscan часто возвращает ошибку в поле 'result', если это 'Max rate limit reached'
                error_message = data.get('result', data.get('message', 'Unknown Etherscan API error'))
                raise ConnectionError(f"Etherscan API error: {error_message}")
                
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Network error during Etherscan request: {e}")

    async def _get_contract_source_code(self, address: str) -> Dict:
        """Получает исходный код контракта и проверяет верификацию."""
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address
        }
        result = await self._api_request(params)
        source_info = result[0] if isinstance(result, list) and len(result) > 0 else {}
        
        is_verified = bool(source_info.get('SourceCode'))
        # TODO: Добавить парсинг ABI для поиска опасных функций (mint, pause, etc.)
        
        return {
            "is_verified": is_verified,
            "contract_name": source_info.get('ContractName', 'N/A'),
            "compiler_version": source_info.get('CompilerVersion', 'N/A'),
            "license": source_info.get('LicenseType', 'N/A')
        }

    async def _get_top_holders(self, contract_address: str, top_n: int = 10) -> Dict:
        """Получает топ-N держателей токена (информация доступна не для всех токенов)."""
        # Этот эндпоинт доступен только в платных тарифах Etherscan.
        # В бесплатной версии придется парсить страницу.
        # Пока возвращаем заглушку.
        await asyncio.sleep(0) # для асинхронности
        return {
            "top_holders_note": "Data requires Etherscan Pro or web scraping.",
            "holders": []
        }

    async def _get_transaction_count(self, contract_address: str) -> Dict:
        """Получает общее количество транзакций для контракта."""
        # Etherscan не предоставляет прямого способа получить кол-во транзакций для токена.
        # Нужно получать список транзакций и смотреть их количество, что очень затратно.
        # Пока возвращаем заглушку.
        await asyncio.sleep(0) # для асинхронности
        return {
            "total_transactions_note": "Data requires paginating all transactions, which is resource-intensive.",
            "transaction_count": None
        }


# Пример использования
async def main():
    print("--- Running Onchain Analysis Agent Standalone ---")
    if not os.getenv('ETHERSCAN_API_KEY'):
        print("\n[ERROR] ETHERSCAN_API_KEY environment variable is not set. Exiting.")
        return

    config = {'onchain_analysis': {}}
    test_tokens = [
        TokenInfo(contract_address="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", name="Uniswap", symbol="UNI"),
        # Пример неверифицированного контракта (может измениться)
        TokenInfo(contract_address="0x0000000000000000000000000000000000000001", name="Burn Address", symbol="BURN"),
    ]
    
    agent = OnchainAnalysisAgent(config=config)
    results = await agent.run(test_tokens)

    print("\n--- Onchain Analysis Results ---")
    for contract, data in results.items():
        if "error" in data:
            print(f"\nToken: {contract}")
            print(f"  Error: {data['error']}")
            continue
            
        print(f"\nToken: {data['token_info'].symbol}")
        source_code_info = data.get('source_code', {})
        if "error" not in source_code_info:
            print(f"  Contract Name: {source_code_info.get('contract_name')}")
            print(f"  Is Verified: {source_code_info.get('is_verified')}")
            print(f"  License: {source_code_info.get('license')}")
        else:
            print(f"  Could not retrieve source code: {source_code_info['error']}")

if __name__ == "__main__":
    asyncio.run(main())
