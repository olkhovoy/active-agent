# -*- coding: utf-8 -*-
import os
import time
import json
import requests
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import pandas as pd

@dataclass
class TokenInfo:
    """Структура для хранения базовой информации о токене."""
    contract_address: str
    name: str = "Unknown"
    symbol: str = "N/A"
    coingecko_id: Optional[str] = None
    market_cap_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    price_usd: Optional[float] = None
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    launch_date: Optional[str] = None
    platform: str = "ethereum"
    discovery_method: str = "unknown"
    source: str = "unknown" # coingecko, etherscan, etc.

class TokenDiscoveryAgent:
    """
    Агент для автоматического обнаружения новых и релевантных ERC-20 токенов.
    """
    def __init__(self, config: Dict):
        self.config = config.get('discovery', {})
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        
        self.base_urls = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'etherscan': 'https://api.etherscan.io/api'
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TokenDiscoveryAgent/1.0'})
        print("Token Discovery Agent initialized.")

    async def run(self, limit: int = 20) -> List[TokenInfo]:
        """
        Основной метод для запуска обнаружения токенов.
        Собирает токены из всех доступных источников и возвращает уникальный список.
        """
        tasks = []
        if self.config.get('coingecko', {}).get('enabled', True):
            tasks.append(self._discover_coingecko())
        
        # TODO: Добавить Etherscan discovery
        # if self.config.get('etherscan', {}).get('enabled', False):
        #     tasks.append(self._discover_etherscan())

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_tokens = []
        for res in results:
            if isinstance(res, list):
                all_tokens.extend(res)
            elif isinstance(res, Exception):
                print(f"[Warning] Error during token discovery: {res}")
        
        # Удаление дубликатов
        unique_tokens = self._remove_duplicates(all_tokens)
        
        # Возвращаем запрошенное количество токенов
        return unique_tokens[:limit]

    async def _discover_coingecko(self) -> List[TokenInfo]:
        """Обнаружение токенов через CoinGecko API."""
        print("Discovering tokens via CoinGecko...")
        loop = asyncio.get_event_loop()
        
        try:
            # Используем run_in_executor для выполнения синхронного кода в async
            response = await loop.run_in_executor(
                None, 
                self._fetch_coingecko_market_data
            )
            
            if not response:
                return []
                
            tokens = [
                TokenInfo(
                    contract_address=t.get('platforms', {}).get('ethereum', ''),
                    name=t.get('name'),
                    symbol=t.get('symbol').upper(),
                    coingecko_id=t.get('id'),
                    market_cap_usd=t.get('market_cap'),
                    volume_24h_usd=t.get('total_volume'),
                    price_usd=t.get('current_price'),
                    circulating_supply=t.get('circulating_supply'),
                    total_supply=t.get('total_supply'),
                    source='coingecko'
                )
                for t in response 
                if t.get('platforms', {}).get('ethereum')
            ]
            print(f"Discovered {len(tokens)} tokens from CoinGecko.")
            return tokens

        except Exception as e:
            print(f"[Error] Failed to discover tokens from CoinGecko: {e}")
            return []

    def _fetch_coingecko_market_data(self) -> Optional[List[Dict]]:
        """Синхронный метод для запроса данных с CoinGecko."""
        url = f"{self.base_urls['coingecko']}/coins/markets"
        params = {
            'vs_currency': 'usd',
            'category': 'ethereum-ecosystem',
            'order': 'market_cap_desc',
            'per_page': self.config.get('coingecko',{}).get('max_tokens_per_request', 100),
            'page': 1,
            'sparkline': 'false',
            'locale': 'en',
            'x_cg_demo_api_key': self.coingecko_api_key
        }
        try:
            res = self.session.get(url, params=params)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as e:
            print(f"[Error] CoinGecko API request failed: {e}")
            return None

    def _remove_duplicates(self, tokens: List[TokenInfo]) -> List[TokenInfo]:
        """Удаляет дубликаты токенов по адресу контракта."""
        seen = set()
        unique_tokens = []
        for token in tokens:
            # Пропускаем токены без адреса контракта
            if not token.contract_address or not isinstance(token.contract_address, str):
                continue
                
            addr_lower = token.contract_address.lower()
            if addr_lower not in seen:
                seen.add(addr_lower)
                unique_tokens.append(token)
        return unique_tokens

    async def _discover_etherscan(self) -> List[TokenInfo]:
        """
        (Placeholder) Обнаружение токенов через сканирование блоков Etherscan.
        """
        print("Etherscan discovery is not yet implemented.")
        # Здесь будет логика сканирования последних блоков на предмет
        # создания новых контрактов, которые могут быть ERC-20 токенами.
        await asyncio.sleep(0) # для асинхронности
        return []

# Пример использования
async def main():
    print("--- Running Token Discovery Agent Standalone ---")
    
    # Загружаем мок-конфигурацию, т.к. orchestrator не запущен
    config = {
        'discovery': {
            'coingecko': { 'enabled': True, 'max_tokens_per_request': 50 },
            'etherscan': { 'enabled': False }
        }
    }
    
    agent = TokenDiscoveryAgent(config)
    tokens = await agent.run(limit=10)
    
    if tokens:
        print("\n--- Discovered Tokens ---")
        for token in tokens:
            print(f"- {token.name} ({token.symbol}): MC ${token.market_cap_usd:,.0f}")
    else:
        print("\nNo tokens discovered.")

if __name__ == "__main__":
    asyncio.run(main())
