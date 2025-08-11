import os
import time
import json
import sqlite3
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
import logging
from pathlib import Path
import schedule

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TokenEvent:
    """Событие, связанное с токеном"""
    event_type: str  # 'created', 'transfer', 'liquidity_added', 'liquidity_removed'
    contract_address: str
    block_number: int
    transaction_hash: str
    timestamp: datetime
    event_data: Dict
    processed: bool = False

@dataclass
class TokenIndex:
    """Индексированная информация о токене"""
    contract_address: str
    name: str
    symbol: str
    decimals: int
    total_supply: str
    first_seen: datetime
    last_updated: datetime
    transaction_count: int
    holder_count: int
    liquidity_usd: float
    market_cap_usd: float
    is_scam: bool = False
    risk_score: float = 0.0
    tags: List[str] = None

class TokenMonitor:
    """Агент для мониторинга и индексации новых ERC-20 токенов"""
    
    def __init__(self, db_path: str = "token_monitor.db"):
        self.db_path = db_path
        self.etherscan_api_key = os.getenv('ETHERSCAN_API_KEY')
        self.infura_api_key = os.getenv('INFURA_API_KEY')
        self.coingecko_api_key = os.getenv('COINGECKO_API_KEY')
        
        # Инициализация базы данных
        self.init_database()
        
        # Кэш для избежания дублирования
        self.known_tokens: Set[str] = set()
        self.load_known_tokens()
        
        # Настройки мониторинга
        self.monitoring_active = False
        self.last_processed_block = 0
        self.block_interval = 100  # Количество блоков для сканирования
        
    def init_database(self):
        """Инициализация базы данных SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица токенов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                contract_address TEXT PRIMARY KEY,
                name TEXT,
                symbol TEXT,
                decimals INTEGER,
                total_supply TEXT,
                first_seen TIMESTAMP,
                last_updated TIMESTAMP,
                transaction_count INTEGER DEFAULT 0,
                holder_count INTEGER DEFAULT 0,
                liquidity_usd REAL DEFAULT 0,
                market_cap_usd REAL DEFAULT 0,
                is_scam BOOLEAN DEFAULT FALSE,
                risk_score REAL DEFAULT 0,
                tags TEXT
            )
        ''')
        
        # Таблица событий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                contract_address TEXT,
                block_number INTEGER,
                transaction_hash TEXT,
                timestamp TIMESTAMP,
                event_data TEXT,
                processed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (contract_address) REFERENCES tokens (contract_address)
            )
        ''')
        
        # Таблица держателей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_holders (
                contract_address TEXT,
                holder_address TEXT,
                balance TEXT,
                last_updated TIMESTAMP,
                PRIMARY KEY (contract_address, holder_address),
                FOREIGN KEY (contract_address) REFERENCES tokens (contract_address)
            )
        ''')
        
        # Индексы для быстрого поиска
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens_risk ON tokens (risk_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens_market_cap ON tokens (market_cap_usd)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_contract ON token_events (contract_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_block ON token_events (block_number)')
        
        conn.commit()
        conn.close()
        logger.info("База данных инициализирована")
    
    def load_known_tokens(self):
        """Загрузка известных токенов из базы данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT contract_address FROM tokens')
        rows = cursor.fetchall()
        self.known_tokens = {row[0] for row in rows}
        conn.close()
        logger.info(f"Загружено {len(self.known_tokens)} известных токенов")
    
    async def start_monitoring(self):
        """Запуск мониторинга в фоновом режиме"""
        if self.monitoring_active:
            logger.warning("Мониторинг уже запущен")
            return
        
        self.monitoring_active = True
        logger.info("Запуск мониторинга токенов...")
        
        # Запускаем задачи мониторинга
        tasks = [
            asyncio.create_task(self.monitor_new_tokens()),
            asyncio.create_task(self.monitor_liquidity_changes()),
            asyncio.create_task(self.update_token_metrics()),
            asyncio.create_task(self.cleanup_old_data())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Ошибка в мониторинге: {e}")
        finally:
            self.monitoring_active = False
    
    async def monitor_new_tokens(self):
        """Мониторинг новых токенов"""
        while self.monitoring_active:
            try:
                # Получаем последний обработанный блок
                latest_block = await self.get_latest_block()
                if latest_block > self.last_processed_block:
                    # Сканируем новые блоки
                    await self.scan_blocks_for_tokens(
                        self.last_processed_block + 1, 
                        min(latest_block, self.last_processed_block + self.block_interval)
                    )
                    self.last_processed_block = min(latest_block, self.last_processed_block + self.block_interval)
                
                await asyncio.sleep(15)  # Пауза между сканированиями
                
            except Exception as e:
                logger.error(f"Ошибка при мониторинге новых токенов: {e}")
                await asyncio.sleep(60)  # Увеличенная пауза при ошибке
    
    async def scan_blocks_for_tokens(self, start_block: int, end_block: int):
        """Сканирование блоков на предмет новых токенов"""
        logger.info(f"Сканирую блоки {start_block} - {end_block}")
        
        for block_num in range(start_block, end_block + 1):
            try:
                # Получаем блок
                block_data = await self.get_block_data(block_num)
                if not block_data:
                    continue
                
                # Анализируем транзакции в блоке
                for tx in block_data.get('transactions', []):
                    if await self.is_token_creation_transaction(tx):
                        await self.process_token_creation(tx, block_num)
                    elif await self.is_token_transfer_transaction(tx):
                        await self.process_token_transfer(tx, block_num)
                
                await asyncio.sleep(0.1)  # Уважаем rate limits
                
            except Exception as e:
                logger.error(f"Ошибка при сканировании блока {block_num}: {e}")
    
    async def is_token_creation_transaction(self, tx: Dict) -> bool:
        """Проверка, является ли транзакция созданием токена"""
        # Проверяем на ERC-20 конструктор
        input_data = tx.get('input', '')
        return (
            input_data.startswith('0x60806040') or  # Конструктор
            input_data.startswith('0x61016060') or  # Конструктор с параметрами
            len(input_data) > 10000  # Длинный input может быть развертыванием контракта
        )
    
    async def is_token_transfer_transaction(self, tx: Dict) -> bool:
        """Проверка, является ли транзакция переводом токена"""
        input_data = tx.get('input', '')
        return input_data.startswith('0xa9059cbb')  # transfer(address,uint256)
    
    async def process_token_creation(self, tx: Dict, block_number: int):
        """Обработка создания нового токена"""
        try:
            contract_address = tx.get('to', '')
            if not contract_address or contract_address in self.known_tokens:
                return
            
            # Получаем информацию о токене
            token_info = await self.get_token_info(contract_address)
            if not token_info:
                return
            
            # Сохраняем в базу данных
            await self.save_token_to_db(token_info)
            
            # Добавляем в кэш
            self.known_tokens.add(contract_address)
            
            # Создаем событие
            event = TokenEvent(
                event_type='created',
                contract_address=contract_address,
                block_number=block_number,
                transaction_hash=tx.get('hash', ''),
                timestamp=datetime.fromtimestamp(int(tx.get('timestamp', 0))),
                event_data={'token_info': asdict(token_info)}
            )
            await self.save_event_to_db(event)
            
            logger.info(f"Обнаружен новый токен: {token_info.name} ({token_info.symbol})")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке создания токена: {e}")
    
    async def process_token_transfer(self, tx: Dict, block_number: int):
        """Обработка перевода токена"""
        try:
            contract_address = tx.get('to', '')
            if not contract_address:
                return
            
            # Создаем событие перевода
            event = TokenEvent(
                event_type='transfer',
                contract_address=contract_address,
                block_number=block_number,
                transaction_hash=tx.get('hash', ''),
                timestamp=datetime.fromtimestamp(int(tx.get('timestamp', 0))),
                event_data={'from': tx.get('from', ''), 'to': tx.get('to', '')}
            )
            await self.save_event_to_db(event)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке перевода токена: {e}")
    
    async def get_token_info(self, contract_address: str) -> Optional[TokenIndex]:
        """Получение информации о токене"""
        try:
            # Получаем базовую информацию через Etherscan
            token_data = await self.get_erc20_data(contract_address)
            if not token_data:
                return None
            
            # Получаем дополнительную информацию через CoinGecko
            coingecko_data = await self.get_coingecko_data(contract_address)
            
            # Создаем объект токена
            token = TokenIndex(
                contract_address=contract_address,
                name=token_data.get('name', 'Unknown'),
                symbol=token_data.get('symbol', 'UNKNOWN'),
                decimals=token_data.get('decimals', 18),
                total_supply=token_data.get('totalSupply', '0'),
                first_seen=datetime.now(),
                last_updated=datetime.now(),
                transaction_count=0,
                holder_count=0,
                liquidity_usd=coingecko_data.get('liquidity_usd', 0.0),
                market_cap_usd=coingecko_data.get('market_cap_usd', 0.0),
                tags=[]
            )
            
            # Анализируем риск
            risk_score = await self.calculate_risk_score(token)
            token.risk_score = risk_score
            token.is_scam = risk_score > 0.7
            
            return token
            
        except Exception as e:
            logger.error(f"Ошибка при получении информации о токене: {e}")
            return None
    
    async def get_erc20_data(self, contract_address: str) -> Optional[Dict]:
        """Получение ERC-20 данных через Etherscan"""
        if not self.etherscan_api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'contract',
                    'action': 'getabi',
                    'address': contract_address,
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') == '1':
                            # Здесь нужно проанализировать ABI и получить данные токена
                            # Пока возвращаем заглушку
                            return {
                                'name': f'Token_{contract_address[:8]}',
                                'symbol': 'UNKNOWN',
                                'decimals': 18,
                                'totalSupply': '1000000000000000000000000'
                            }
        except Exception as e:
            logger.error(f"Ошибка при получении ERC-20 данных: {e}")
        
        return None
    
    async def get_coingecko_data(self, contract_address: str) -> Dict:
        """Получение данных через CoinGecko"""
        # Заглушка - в реальности нужно использовать CoinGecko API
        return {
            'liquidity_usd': 0.0,
            'market_cap_usd': 0.0
        }
    
    async def calculate_risk_score(self, token: TokenIndex) -> float:
        """Расчет скора риска для токена"""
        risk_score = 0.0
        
        # Проверяем подозрительные имена
        suspicious_patterns = ['moon', 'safe', 'elon', 'inu', 'doge', 'shib']
        name_lower = token.name.lower()
        for pattern in suspicious_patterns:
            if pattern in name_lower:
                risk_score += 0.2
        
        # Проверяем ликвидность
        if token.liquidity_usd < 10000:  # < $10K
            risk_score += 0.3
        
        # Проверяем market cap
        if token.market_cap_usd < 100000:  # < $100K
            risk_score += 0.2
        
        # Проверяем количество держателей
        if token.holder_count < 100:
            risk_score += 0.2
        
        return min(1.0, risk_score)
    
    async def save_token_to_db(self, token: TokenIndex):
        """Сохранение токена в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tokens 
                (contract_address, name, symbol, decimals, total_supply, 
                 first_seen, last_updated, transaction_count, holder_count,
                 liquidity_usd, market_cap_usd, is_scam, risk_score, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token.contract_address, token.name, token.symbol, token.decimals,
                token.total_supply, token.first_seen, token.last_updated,
                token.transaction_count, token.holder_count, token.liquidity_usd,
                token.market_cap_usd, token.is_scam, token.risk_score,
                json.dumps(token.tags) if token.tags else '[]'
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении токена: {e}")
        finally:
            conn.close()
    
    async def save_event_to_db(self, event: TokenEvent):
        """Сохранение события в базу данных"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO token_events 
                (event_type, contract_address, block_number, transaction_hash, 
                 timestamp, event_data, processed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_type, event.contract_address, event.block_number,
                event.transaction_hash, event.timestamp, json.dumps(event.event_data),
                event.processed
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении события: {e}")
        finally:
            conn.close()
    
    async def get_latest_block(self) -> int:
        """Получение номера последнего блока"""
        if not self.etherscan_api_key:
            return 0
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'proxy',
                    'action': 'eth_blockNumber',
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('result'):
                            return int(data['result'], 16)
        except Exception as e:
            logger.error(f"Ошибка при получении последнего блока: {e}")
        
        return 0
    
    async def get_block_data(self, block_number: int) -> Optional[Dict]:
        """Получение данных блока"""
        if not self.etherscan_api_key:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.etherscan.io/api"
                params = {
                    'module': 'proxy',
                    'action': 'eth_getBlockByNumber',
                    'tag': hex(block_number),
                    'boolean': 'true',
                    'apikey': self.etherscan_api_key
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('result')
        except Exception as e:
            logger.error(f"Ошибка при получении блока {block_number}: {e}")
        
        return None
    
    async def monitor_liquidity_changes(self):
        """Мониторинг изменений ликвидности"""
        while self.monitoring_active:
            try:
                # Обновляем данные о ликвидности каждые 5 минут
                await self.update_liquidity_data()
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Ошибка при мониторинге ликвидности: {e}")
                await asyncio.sleep(60)
    
    async def update_liquidity_data(self):
        """Обновление данных о ликвидности"""
        # Заглушка - в реальности нужно обновлять данные через DEX APIs
        pass
    
    async def update_token_metrics(self):
        """Обновление метрик токенов"""
        while self.monitoring_active:
            try:
                # Обновляем метрики каждые 10 минут
                await self.update_token_holder_counts()
                await self.update_transaction_counts()
                await asyncio.sleep(600)
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении метрик: {e}")
                await asyncio.sleep(60)
    
    async def update_token_holder_counts(self):
        """Обновление количества держателей токенов"""
        # Заглушка
        pass
    
    async def update_transaction_counts(self):
        """Обновление количества транзакций"""
        # Заглушка
        pass
    
    async def cleanup_old_data(self):
        """Очистка старых данных"""
        while self.monitoring_active:
            try:
                # Очищаем данные старше 30 дней каждые 24 часа
                await self.cleanup_old_events()
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Ошибка при очистке данных: {e}")
                await asyncio.sleep(3600)
    
    async def cleanup_old_events(self):
        """Очистка старых событий"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Удаляем события старше 30 дней
            cutoff_date = datetime.now() - timedelta(days=30)
            cursor.execute('DELETE FROM token_events WHERE timestamp < ?', (cutoff_date,))
            deleted_count = cursor.rowcount
            
            if deleted_count > 0:
                logger.info(f"Удалено {deleted_count} старых событий")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при очистке событий: {e}")
        finally:
            conn.close()
    
    def get_tokens_by_risk(self, risk_threshold: float = 0.5) -> List[TokenIndex]:
        """Получение токенов по уровню риска"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT * FROM tokens 
                WHERE risk_score >= ? 
                ORDER BY risk_score DESC
            ''', (risk_threshold,))
            
            rows = cursor.fetchall()
            tokens = []
            
            for row in rows:
                token = TokenIndex(
                    contract_address=row[0],
                    name=row[1],
                    symbol=row[2],
                    decimals=row[3],
                    total_supply=row[4],
                    first_seen=datetime.fromisoformat(row[5]),
                    last_updated=datetime.fromisoformat(row[6]),
                    transaction_count=row[7],
                    holder_count=row[8],
                    liquidity_usd=row[9],
                    market_cap_usd=row[10],
                    is_scam=bool(row[11]),
                    risk_score=row[12],
                    tags=json.loads(row[13]) if row[13] else []
                )
                tokens.append(token)
            
            return tokens
            
        except Exception as e:
            logger.error(f"Ошибка при получении токенов по риску: {e}")
            return []
        finally:
            conn.close()
    
    def export_tokens_to_csv(self, filename: str = None):
        """Экспорт токенов в CSV файл"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"monitored_tokens_{timestamp}.csv"
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('SELECT * FROM tokens', conn)
        conn.close()
        
        df.to_csv(filename, index=False)
        logger.info(f"Экспортировано {len(df)} токенов в {filename}")
        return filename

def main():
    """Тестирование монитора токенов"""
    monitor = TokenMonitor()
    
    # Запускаем мониторинг
    print("Запуск мониторинга токенов...")
    print("Нажмите Ctrl+C для остановки")
    
    try:
        asyncio.run(monitor.start_monitoring())
    except KeyboardInterrupt:
        print("\nОстановка мониторинга...")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
