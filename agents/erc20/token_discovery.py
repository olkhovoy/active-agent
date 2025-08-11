import os
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """Структура для хранения информации о токене"""
    name: str
    symbol: str
    contract_address: str
    coingecko_id: Optional[str] = None
    market_cap_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    price_usd: Optional[float] = None
    total_supply: Optional[float] = None
    circulating_supply: Optional[float] = None
    launch_date: Optional[str] = None
    platform: str = "ethereum"
    discovery_method: str = "unknown"
    risk_score: Optional[float] = None

class TokenDiscoveryAgent:
    """Агент для автоматического обнаружения новых ERC-20 токенов"""
    
    def __init__(self):
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.base_urls = {
            'coingecko': 'https://api.coingecko.com/api/v3',
            'etherscan': 'https://api.etherscan.io/api'
        }
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TokenDiscoveryAgent/1.0'})
        
    def discover_new_tokens_coingecko(self, min_market_cap: float = 1000000, 
                                    max_age_days: int = 30) -> List[TokenInfo]:
        """Обнаружение новых токенов через CoinGecko API"""
        logger.info("Начинаю поиск новых токенов через CoinGecko...")
        
        tokens = []
        page = 1
        max_pages = 10  # Ограничиваем количество страниц
        
        try:
            while page <= max_pages:
                # Получаем список токенов с пагинацией
                url = f"{self.base_urls['coingecko']}/coins/markets"
                params = {
                    'vs_currency': 'usd',
                    'order': 'market_cap_desc',
                    'per_page': 250,
                    'page': page,
                    'sparkline': False,
                    'platform': 'ethereum'
                }
                
                if self.coingecko_api_key:
                    params['x_cg_demo_api_key'] = self.coingecko_api_key
                
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"CoinGecko API вернул статус {response.status_code}")
                    break
                
                data = response.json()
                if not data:
                    break
                
                for coin in data:
                    # Проверяем критерии для новых токенов
                    market_cap = coin.get('market_cap', 0)
                    if market_cap < min_market_cap:
                        continue
                    
                    # Получаем детальную информацию о токене
                    token_detail = self._get_token_details(coin['id'])
                    if not token_detail:
                        continue
                    
                    # Проверяем возраст токена
                    if not self._is_recent_token(token_detail, max_age_days):
                        continue
                    
                    token_info = TokenInfo(
                        name=coin['name'],
                        symbol=coin['symbol'].upper(),
                        contract_address=token_detail.get('contract_address', ''),
                        coingecko_id=coin['id'],
                        market_cap_usd=market_cap,
                        volume_24h_usd=coin.get('total_volume', 0),
                        price_usd=coin.get('current_price', 0),
                        total_supply=token_detail.get('total_supply'),
                        circulating_supply=coin.get('circulating_supply'),
                        launch_date=token_detail.get('genesis_date'),
                        discovery_method='coingecko_api'
                    )
                    
                    tokens.append(token_info)
                    logger.info(f"Обнаружен новый токен: {token_info.name} ({token_info.symbol})")
                
                page += 1
                time.sleep(1)  # Уважаем rate limits
                
        except Exception as e:
            logger.error(f"Ошибка при поиске через CoinGecko: {e}")
        
        logger.info(f"Обнаружено {len(tokens)} новых токенов через CoinGecko")
        return tokens
    
    def discover_tokens_etherscan(self, min_holders: int = 100, 
                                min_transactions: int = 1000) -> List[TokenInfo]:
        """Обнаружение токенов через сканирование Ethereum блокчейна"""
        logger.info("Начинаю сканирование Ethereum блокчейна...")
        
        if not self.etherscan_api_key:
            logger.warning("Etherscan API ключ не найден, пропускаю сканирование блокчейна")
            return []
        
        tokens = []
        
        try:
            # Получаем последние блоки и ищем токен-транзакции
            latest_block_url = f"{self.base_urls['etherscan']}"
            params = {
                'module': 'proxy',
                'action': 'eth_blockNumber',
                'apikey': self.etherscan_api_key
            }
            
            response = self.session.get(latest_block_url, params=params, timeout=30)
            if response.status_code != 200:
                logger.warning(f"Etherscan API вернул статус {response.status_code}")
                return tokens
            
            data = response.json()
            if data.get('status') != '1':
                return tokens
            
            # Сканируем последние 100 блоков на предмет токен-транзакций
            latest_block = int(data['result'], 16)
            start_block = max(0, latest_block - 100)
            
            for block_num in range(start_block, latest_block + 1):
                block_params = {
                    'module': 'proxy',
                    'action': 'eth_getBlockByNumber',
                    'tag': hex(block_num),
                    'boolean': 'true',
                    'apikey': self.etherscan_api_key
                }
                
                block_response = self.session.get(latest_block_url, params=block_params, timeout=30)
                if block_response.status_code != 200:
                    continue
                
                block_data = block_response.json()
                if not block_data.get('result'):
                    continue
                
                # Анализируем транзакции в блоке
                for tx in block_data['result'].get('transactions', []):
                    if self._is_token_transaction(tx):
                        token_info = self._extract_token_from_transaction(tx)
                        if token_info and self._meets_criteria(token_info, min_holders, min_transactions):
                            tokens.append(token_info)
                            logger.info(f"Обнаружен токен в блоке: {token_info.name} ({token_info.symbol})")
                
                time.sleep(0.1)  # Уважаем rate limits
                
        except Exception as e:
            logger.error(f"Ошибка при сканировании блокчейна: {e}")
        
        logger.info(f"Обнаружено {len(tokens)} токенов через сканирование блокчейна")
        return tokens
    
    def _get_token_details(self, coin_id: str) -> Optional[Dict]:
        """Получение детальной информации о токене"""
        try:
            url = f"{self.base_urls['coingecko']}/coins/{coin_id}"
            params = {}
            if self.coingecko_api_key:
                params['x_cg_demo_api_key'] = self.coingecko_api_key
            
            response = self.session.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.debug(f"Не удалось получить детали для {coin_id}: {e}")
        return None
    
    def _is_recent_token(self, token_detail: Dict, max_age_days: int) -> bool:
        """Проверка, является ли токен недавно созданным"""
        genesis_date = token_detail.get('genesis_date')
        if not genesis_date:
            return False
        
        try:
            launch_date = datetime.strptime(genesis_date, '%Y-%m-%d')
            age_days = (datetime.now() - launch_date).days
            return age_days <= max_age_days
        except ValueError:
            return False
    
    def _is_token_transaction(self, tx: Dict) -> bool:
        """Проверка, является ли транзакция токен-транзакцией"""
        # Проверяем на ERC-20 transfer события
        input_data = tx.get('input', '')
        return input_data.startswith('0xa9059cbb')  # transfer(address,uint256) signature
    
    def _extract_token_from_transaction(self, tx: Dict) -> Optional[TokenInfo]:
        """Извлечение информации о токене из транзакции"""
        try:
            # Получаем информацию о контракте токена
            contract_address = tx.get('to', '')
            if not contract_address:
                return None
            
            # Получаем базовую информацию о токене
            token_info = self._get_erc20_info(contract_address)
            if token_info:
                token_info.discovery_method = 'blockchain_scan'
                return token_info
                
        except Exception as e:
            logger.debug(f"Не удалось извлечь информацию о токене: {e}")
        
        return None
    
    def _get_erc20_info(self, contract_address: str) -> Optional[TokenInfo]:
        """Получение базовой информации о ERC-20 токене"""
        try:
            # Получаем имя, символ и общее предложение токена
            params = {
                'module': 'contract',
                'action': 'getabi',
                'address': contract_address,
                'apikey': self.etherscan_api_key
            }
            
            response = self.session.get(self.base_urls['etherscan'], params=params, timeout=30)
            if response.status_code != 200:
                return None
            
            data = response.json()
            if data.get('status') != '1':
                return None
            
            # Здесь можно добавить более детальный анализ ABI
            # Пока возвращаем базовую информацию
            return TokenInfo(
                name=f"Token_{contract_address[:8]}",
                symbol="UNKNOWN",
                contract_address=contract_address
            )
            
        except Exception as e:
            logger.debug(f"Не удалось получить ERC-20 информацию: {e}")
            return None
    
    def _meets_criteria(self, token: TokenInfo, min_holders: int, min_transactions: int) -> bool:
        """Проверка соответствия токена критериям"""
        # Здесь можно добавить более сложную логику проверки
        return True
    
    def save_discovered_tokens(self, tokens: List[TokenInfo], filename: str = None):
        """Сохранение обнаруженных токенов в CSV файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discovered_tokens_{timestamp}.csv"
        
        # Конвертируем в DataFrame
        data = []
        for token in tokens:
            data.append({
                'name': token.name,
                'symbol': token.symbol,
                'contract_address': token.contract_address,
                'coingecko_id': token.coingecko_id,
                'market_cap_usd': token.market_cap_usd,
                'volume_24h_usd': token.volume_24h_usd,
                'price_usd': token.price_usd,
                'total_supply': token.total_supply,
                'circulating_supply': token.circulating_supply,
                'launch_date': token.launch_date,
                'platform': token.platform,
                'discovery_method': token.discovery_method,
                'risk_score': token.risk_score
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logger.info(f"Сохранено {len(tokens)} токенов в {filename}")
        return filename

def main():
    """Основная функция для тестирования агента обнаружения"""
    discovery_agent = TokenDiscoveryAgent()
    
    # Обнаружение через CoinGecko
    coingecko_tokens = discovery_agent.discover_new_tokens_coingecko(
        min_market_cap=1000000,  # Минимум $1M market cap
        max_age_days=30          # Токены не старше 30 дней
    )
    
    # Обнаружение через сканирование блокчейна
    blockchain_tokens = discovery_agent.discover_tokens_etherscan(
        min_holders=100,         # Минимум 100 держателей
        min_transactions=1000    # Минимум 1000 транзакций
    )
    
    # Объединяем результаты
    all_tokens = coingecko_tokens + blockchain_tokens
    
    # Убираем дубликаты по адресу контракта
    unique_tokens = {}
    for token in all_tokens:
        if token.contract_address not in unique_tokens:
            unique_tokens[token.contract_address] = token
    
    final_tokens = list(unique_tokens.values())
    
    # Сохраняем результаты
    if final_tokens:
        filename = discovery_agent.save_discovered_tokens(final_tokens)
        print(f"Обнаружено {len(final_tokens)} уникальных токенов")
        print(f"Результаты сохранены в {filename}")
    else:
        print("Токены не обнаружены")

if __name__ == "__main__":
    main()
