import duckdb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from xtquant import xtdata
import time
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import queue

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MiniqmtDuckDB:
    def __init__(self, db_path='miniqmt_data.db'):
        self.db_path = db_path
        self.conn = duckdb.connect(database=db_path, read_only=False)
        self._create_tables()
        self._lock = threading.Lock()  # 数据库操作锁
    
    def _create_tables(self):
        """创建数据库表结构"""
        # 原始行情数据表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS stock_daily_raw (
            code VARCHAR,
            date DATE,
            open FLOAT,
            close FLOAT,
            high FLOAT,
            low FLOAT,
            volume BIGINT,
            amount FLOAT,
            preclose FLOAT,
            PRIMARY KEY (code, date)
        )
        """)
        
        # 除权除息数据表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS divid_factors (
            code VARCHAR,
            date DATE,
            stockBonus FLOAT,
            stockGift FLOAT,
            allotNum FLOAT,
            allotPrice FLOAT,
            interest FLOAT,
            dr FLOAT,
            PRIMARY KEY (code, date)
        )
        """)
        
        # 数据更新记录表
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS update_log (
            code VARCHAR,
            last_update DATE,
            PRIMARY KEY (code)
        )
        """)
        
        logger.info("数据库表初始化完成")
    
    def download_raw_data_multithread(self, stock_list, start_time=None, end_time=None, max_workers=8, progress_callback=None):
        """多线程下载原始未复权数据"""
        if start_time is None:
            start_time = "20100101"
        if end_time is None:
            end_time = datetime.now().strftime("%Y%m%d")
        
        logger.info(f"开始多线程下载数据: {len(stock_list)} 只股票，线程数: {max_workers}")
        
        # 首先批量下载历史数据（这一步无法并行）
        try:
            logger.info("正在批量下载历史数据...")
            if progress_callback:
                progress_callback("正在批量下载历史数据...", 0)
            
            xtdata.download_history_data2(
                stock_list=stock_list,
                period="1d",
                start_time=start_time,
                end_time=end_time
            )
            time.sleep(3)  # 等待下载完成
            logger.info("批量下载完成，开始并行处理数据...")
            if progress_callback:
                progress_callback("批量下载完成，开始并行处理数据...", 10)
        except Exception as e:
            logger.error(f"批量数据下载失败: {e}")
            return
        
        # 使用线程池并行处理每只股票的数据
        success_count = 0
        failed_stocks = []
        total_stocks = len(stock_list)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_stock = {
                executor.submit(self._download_single_stock_thread, stock, start_time, end_time): stock 
                for stock in stock_list
            }
            
            # 处理完成的任务
            completed = 0
            for future in as_completed(future_to_stock):
                stock = future_to_stock[future]
                completed += 1
                try:
                    result = future.result()
                    if result > 0:
                        success_count += 1
                    else:
                        failed_stocks.append(stock)
                except Exception as exc:
                    logger.error(f"股票 {stock} 处理失败: {exc}")
                    failed_stocks.append(stock)
                
                # 更新进度
                if progress_callback:
                    progress = 10 + (completed / total_stocks) * 90  # 10-100%
                    progress_callback(f"处理中... {completed}/{total_stocks}", progress)
        
        logger.info(f"多线程下载完成: 成功 {success_count} 只，失败 {len(failed_stocks)} 只")
        if failed_stocks:
            logger.warning(f"失败的股票: {failed_stocks[:10]}...")  # 只显示前10只
        
        if progress_callback:
            progress_callback(f"完成: 成功 {success_count} 只，失败 {len(failed_stocks)} 只", 100)
        
        return success_count, failed_stocks
    
    def download_raw_data(self, stock_list, start_time=None, end_time=None):
        """下载原始未复权数据"""
        if start_time is None:
            start_time = "20100101"
        if end_time is None:
            end_time = datetime.now().strftime("%Y%m%d")
        
        # logger.info(f"开始下载原始数据: {stock_list}, 时间范围: {start_time} - {end_time}")
        
        try:
            # 检查xtquant连接
            # logger.info("检查xtquant服务连接...")
            test_data = xtdata.get_market_data(
                field_list=["close"],
                stock_list=[stock_list[0]],
                period="1d",
                start_time=start_time,
                end_time=start_time,
                dividend_type="none"
            )
            # logger.info("xtquant服务连接正常")
        except Exception as e:
            logger.error(f"xtquant服务连接失败: {e}")
            logger.error("请确保QMT-投研版或QMT-极简版已启动")
            return
        
        # 使用xtdata下载未复权数据
        try:
            xtdata.download_history_data2(
                stock_list=stock_list,
                period="1d",
                start_time=start_time,
                end_time=end_time,
                # callback=lambda data: logger.info(f"下载进度: {data['finished']}/{data['total']}")
            )
            
            # 等待下载完成
            time.sleep(5)
            # logger.info("数据下载完成，开始存储到数据库...")
        except Exception as e:
            logger.error(f"数据下载失败: {e}")
            return
        
        # 获取原始数据并存储到数据库
        for stock in stock_list:
            try:
                # 获取K线数据
                data = xtdata.get_market_data(
                    field_list=["open", "close", "high", "low", "volume", "amount", "preclose"],
                    stock_list=[stock],
                    period="1d",
                    start_time=start_time,
                    end_time=end_time,
                    dividend_type="none"  # 不复权
                )
                
                # logger.info(f"获取到的数据类型: {type(data)}")
                # if data:
                #     logger.info(f"数据键: {list(data.keys())}")
                # else:
                #     logger.warning(f"获取 {stock} 数据为空")
                
                if data and 'close' in data:
                    # logger.info(f"close数据类型: {type(data['close'])}")
                    
                    # xtdata返回的是DataFrame格式，股票代码作为行索引，日期作为列
                    if isinstance(data['close'], pd.DataFrame) and stock in data['close'].index:
                        # logger.info(f"{stock} close数据长度: {len(data['close'].columns)}")
                        # logger.info(f"{stock} 数据日期范围: {data['close'].columns[0]} - {data['close'].columns[-1]}")
                        
                        # 转换数据格式：从wide format转为long format
                        stock_data_list = []
                        for field in ["open", "close", "high", "low", "volume", "amount", "preclose"]:
                            if field in data and stock in data[field].index:
                                # 获取该股票该字段的数据（横向的时间序列）
                                field_series = data[field].loc[stock]
                                field_series.name = field
                                stock_data_list.append(field_series)
                        
                        if stock_data_list:
                            # 合并所有字段数据
                            df = pd.concat(stock_data_list, axis=1)
                            df = df.reset_index()
                            
                            # 检查列名和数据类型
                            # logger.info(f"合并后的列名: {df.columns.tolist()}")
                            # logger.info(f"前几行数据: \n{df.head()}")
                            
                            # 重命名索引列为time
                            if df.columns[0] == 'index':
                                df = df.rename(columns={'index': 'time'})
                            elif df.columns[0] not in ['time', 'date']:
                                df = df.rename(columns={df.columns[0]: 'time'})
                            
                            df['code'] = stock
                            
                            # 确保time列是字符串格式，然后转换为日期
                            try:
                                df['time'] = df['time'].astype(str)
                                df['date'] = pd.to_datetime(df['time'], format='%Y%m%d').dt.date
                            except Exception as date_error:
                                logger.error(f"日期转换错误: {date_error}")
                                # logger.info(f"time列数据类型: {df['time'].dtype}")
                                # logger.info(f"time列示例数据: {df['time'].head().tolist()}")
                                continue
                            
                            # 重新排列列顺序
                            final_columns = ['code', 'date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'preclose']
                            available_columns = [col for col in final_columns if col in df.columns]
                            df = df[available_columns]
                            
                            # logger.info(f"最终数据结构: {df.columns.tolist()}")
                            # logger.info(f"数据行数: {len(df)}")
                            
                            # 存储到数据库
                            self._upsert_raw_data(df)
                            
                            # 更新记录
                            self._update_log(stock, df['date'].max())
                            
                            logger.info(f"成功存储 {stock} 的 {len(df)} 条原始数据")
                        else:
                            logger.warning(f"未找到 {stock} 的有效数据字段")
                    else:
                        logger.warning(f"数据中不包含 {stock} 或格式不正确")
                        # logger.info(f"DataFrame索引: {data['close'].index.tolist()}")
                
                # 获取除权除息数据
                try:
                    divid_data = xtdata.get_divid_factors(stock)
                    if divid_data is not None and not divid_data.empty:
                        # logger.info(f"获取到 {stock} 除权除息数据，形状: {divid_data.shape}")
                        # logger.info(f"除权除息数据列名: {divid_data.columns.tolist()}")
                        # logger.info(f"除权除息数据索引类型: {type(divid_data.index)}")
                        # logger.info(f"除权除息数据前几行:\n{divid_data.head()}")
                        self._upsert_divid_data(stock, divid_data)
                        # logger.info(f"成功存储 {stock} 的除权除息数据")
                    else:
                        # logger.info(f"{stock} 没有除权除息数据")
                        pass
                except Exception as divid_error:
                    logger.error(f"获取 {stock} 除权除息数据失败: {divid_error}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    
            except Exception as e:
                logger.error(f"下载 {stock} 数据失败: {e}")
    
    def _upsert_raw_data(self, df):
        """插入或更新原始数据（线程安全）"""
        if df.empty:
            return
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO stock_daily_raw
            SELECT * FROM df
            """)
    
    def _upsert_divid_data(self, stock, divid_df):
        """插入或更新除权除息数据（线程安全）"""
        if divid_df.empty:
            return
        
        try:
            df = divid_df.copy()
            df = df.reset_index()
            df['code'] = stock
            
            # 检查日期列名，可能是'date'、索引或其他名称
            date_column = None
            if 'date' in df.columns:
                date_column = 'date'
            elif df.columns[0] in ['index', 'time']:
                # 如果第一列是索引或时间列，重命名为date
                date_column = df.columns[0]
                df = df.rename(columns={date_column: 'date'})
                date_column = 'date'
            else:
                # 假设第一列是日期列
                date_column = df.columns[0]
                df = df.rename(columns={date_column: 'date'})
                date_column = 'date'
            
            # 转换日期格式
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date']).dt.date
            
            # 只选择数据库表中存在的列，按照表结构顺序
            required_columns = ['code', 'date', 'stockBonus', 'stockGift', 'allotNum', 'allotPrice', 'interest', 'dr']
            available_columns = [col for col in required_columns if col in df.columns]
            
            if len(available_columns) < len(required_columns):
                missing_cols = set(required_columns) - set(available_columns)
                logger.warning(f"缺少列: {missing_cols}")
                # 对于缺少的列，添加默认值
                for col in missing_cols:
                    if col not in ['code', 'date']:
                        df[col] = 0.0
                available_columns = required_columns
            
            df = df[available_columns]
            # logger.info(f"除权除息数据处理完成，最终列名: {df.columns.tolist()}")
            # logger.info(f"数据行数: {len(df)}")
            
        except Exception as e:
            logger.error(f"除权除息数据处理失败: {e}")
            # logger.info(f"原始数据结构: {divid_df.columns.tolist()}")
            # logger.info(f"原始数据索引: {divid_df.index}")
            return
        
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO divid_factors
            SELECT * FROM df
            """)
    
    def _update_log(self, stock, last_date):
        """更新数据更新记录（线程安全）"""
        with self._lock:
            self.conn.execute("""
            INSERT OR REPLACE INTO update_log (code, last_update)
            VALUES (?, ?)
            """, [stock, last_date])
    
    def get_market_data(self, stock_list, start_time=None, end_time=None, 
                       field_list=None, dividend_type='none'):
        """获取行情数据，支持指定复权方式"""
        if field_list is None:
            field_list = ['open', 'close', 'high', 'low', 'volume']
        
        # 从数据库获取原始数据
        stock_list_str = "', '".join(stock_list)
        where_clause = f"code IN ('{stock_list_str}')"
        
        if start_time:
            where_clause += f" AND date >= '{start_time}'"
        if end_time:
            where_clause += f" AND date <= '{end_time}'"
        
        query = f"""
        SELECT * FROM stock_daily_raw 
        WHERE {where_clause}
        ORDER BY code, date
        """
        
        raw_data = self.conn.execute(query).df()
        
        if raw_data.empty:
            logger.warning("未找到原始数据")
            return {}
        
        result = {}
        
        for stock in stock_list:
            stock_data = raw_data[raw_data['code'] == stock].copy()
            if stock_data.empty:
                continue
            
            stock_data = stock_data.set_index('date')
            
            # 根据复权类型处理数据
            if dividend_type != 'none':
                # 获取除权除息数据
                divid_query = f"""
                SELECT * FROM divid_factors 
                WHERE code = '{stock}'
                ORDER BY date
                """
                divid_data = self.conn.execute(divid_query).df()
                
                if not divid_data.empty:
                    divid_data = divid_data.set_index('date')
                    
                    # 应用复权算法
                    for field in ['open', 'close', 'high', 'low']:
                        if field in field_list and field in stock_data.columns:
                            price_data = stock_data[[field]]
                            
                            if dividend_type == 'front':
                                # 前复权
                                stock_data[field] = self._process_forward(price_data, divid_data)[field]
                            elif dividend_type == 'back':
                                # 后复权
                                stock_data[field] = self._process_backward(price_data, divid_data)[field]
                            elif dividend_type == 'front_ratio':
                                # 等比前复权
                                stock_data[field] = self._process_forward_ratio(price_data, divid_data)[field]
                            elif dividend_type == 'back_ratio':
                                # 等比后复权
                                stock_data[field] = self._process_backward_ratio(price_data, divid_data)[field]
            
            # 构建返回结果
            for field in field_list:
                if field in stock_data.columns:
                    if field not in result:
                        result[field] = {}
                    result[field][stock] = stock_data[field]
        
        return result
    
    def _gen_divid_ratio(self, quote_datas, divid_datas):
        """生成除权比例"""
        drl = []
        dr = 1.0
        qi = 0
        qdl = len(quote_datas)
        di = 0
        ddl = len(divid_datas)
        
        while qi < qdl and di < ddl:
            qd = quote_datas.iloc[qi]
            dd = divid_datas.iloc[di]
            if qd.name >= dd.name:
                dr *= dd['dr']
                di += 1
            if qd.name <= dd.name:
                drl.append(dr)
                qi += 1
        
        while qi < qdl:
            drl.append(dr)
            qi += 1
        
        return pd.DataFrame(drl, index=quote_datas.index, columns=quote_datas.columns)
    
    def _process_forward_ratio(self, quote_datas, divid_datas):
        """等比前复权"""
        drl = self._gen_divid_ratio(quote_datas, divid_datas)
        drlf = drl / drl.iloc[-1]
        result = (quote_datas * drlf).apply(lambda x: round(x, 2))
        return result
    
    def _process_backward_ratio(self, quote_datas, divid_datas):
        """等比后复权"""
        drl = self._gen_divid_ratio(quote_datas, divid_datas)
        result = (quote_datas * drl).apply(lambda x: round(x, 2))
        return result
    
    def _process_forward(self, quote_datas1, divid_datas):
        """前复权"""
        quote_datas = quote_datas1.copy()
        
        def calc_front(v, d):
            return ((v - d['interest'] + d['allotPrice'] * d['allotNum'])
                   / (1 + d['allotNum'] + d['stockBonus'] + d['stockGift']))
        
        for qi in range(len(quote_datas)):
            q = quote_datas.iloc[qi]
            for di in range(len(divid_datas)):
                d = divid_datas.iloc[di]
                if d.name <= q.name:
                    continue
                q.iloc[0] = calc_front(q.iloc[0], d)
        
        return quote_datas
    
    def _process_backward(self, quote_datas1, divid_datas):
        """后复权"""
        quote_datas = quote_datas1.copy()
        
        def calc_back(v, d):
            return ((v * (1.0 + d['stockGift'] + d['stockBonus'] + d['allotNum'])
                    + d['interest'] - d['allotNum'] * d['allotPrice']))
        
        for qi in range(len(quote_datas)):
            q = quote_datas.iloc[qi]
            for di in range(len(divid_datas) - 1, -1, -1):
                d = divid_datas.iloc[di]
                if d.name > q.name:
                    continue
                q.iloc[0] = calc_back(q.iloc[0], d)
        
        return quote_datas
    
    def incremental_update(self, stock_list=None):
        """增量更新数据"""
        if stock_list is None:
            # 获取所有已有股票代码
            result = self.conn.execute("SELECT DISTINCT code FROM update_log").df()
            if result.empty:
                logger.warning("没有找到需要更新的股票，将更新所有A股")
                stock_list = self.get_all_a_stocks()
            else:
                stock_list = result['code'].tolist()
        
        # logger.info(f"开始增量更新: {len(stock_list)} 只股票")
        
        # 分批处理增量更新
        batch_size = 50  # 增量更新每批50只
        total_batches = (len(stock_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(stock_list), batch_size):
            batch_stocks = stock_list[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            # logger.info(f"增量更新第 {batch_num}/{total_batches} 批，共 {len(batch_stocks)} 只股票")
            
            for stock in batch_stocks:
                try:
                    # 获取最后更新日期
                    last_update_result = self.conn.execute("""
                    SELECT last_update FROM update_log WHERE code = ?
                    """, [stock]).df()
                    
                    if not last_update_result.empty:
                        last_date = last_update_result['last_update'].iloc[0]
                        start_time = (pd.to_datetime(last_date) + timedelta(days=1)).strftime("%Y%m%d")
                    else:
                        # 如果没有记录，从一年前开始更新
                        start_time = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
                    
                    end_time = datetime.now().strftime("%Y%m%d")
                    
                    if start_time <= end_time:
                        # 只更新单只股票，避免批量下载的复杂性
                        self._download_single_stock(stock, start_time, end_time)
                        # logger.info(f"完成 {stock} 增量更新 ({start_time} - {end_time})")
                    else:
                        # logger.info(f"{stock} 数据已是最新，无需更新")
                        pass
                    
                except Exception as e:
                    logger.error(f"更新 {stock} 失败: {e}")
            
            # 批次间短暂休息
            import time
            time.sleep(1)
    
    def _download_single_stock(self, stock, start_time, end_time):
        """下载单只股票数据（用于增量更新）"""
        try:
            # 获取K线数据
            data = xtdata.get_market_data(
                field_list=["open", "close", "high", "low", "volume", "amount", "preclose"],
                stock_list=[stock],
                period="1d",
                start_time=start_time,
                end_time=end_time,
                dividend_type="none"
            )
            
            if data and 'close' in data and isinstance(data['close'], pd.DataFrame) and stock in data['close'].index:
                # 转换数据格式
                stock_data_list = []
                for field in ["open", "close", "high", "low", "volume", "amount", "preclose"]:
                    if field in data and stock in data[field].index:
                        field_series = data[field].loc[stock]
                        field_series.name = field
                        stock_data_list.append(field_series)
                
                if stock_data_list:
                    # 合并所有字段数据
                    df = pd.concat(stock_data_list, axis=1)
                    df = df.reset_index()
                    
                    if df.columns[0] == 'index':
                        df = df.rename(columns={'index': 'time'})
                    elif df.columns[0] not in ['time', 'date']:
                        df = df.rename(columns={df.columns[0]: 'time'})
                    
                    df['code'] = stock
                    df['time'] = df['time'].astype(str)
                    df['date'] = pd.to_datetime(df['time'], format='%Y%m%d').dt.date
                    
                    final_columns = ['code', 'date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'preclose']
                    available_columns = [col for col in final_columns if col in df.columns]
                    df = df[available_columns]
                    
                    if not df.empty:
                        # 存储到数据库
                        self._upsert_raw_data(df)
                        # 更新记录
                        self._update_log(stock, df['date'].max())
                        return len(df)
            
            return 0
            
        except Exception as e:
            logger.error(f"单只股票 {stock} 数据下载失败: {e}")
            return 0
    
    def _download_single_stock_thread(self, stock, start_time, end_time):
        """单只股票数据下载（线程安全版本）"""
        try:
            # 获取K线数据
            data = xtdata.get_market_data(
                field_list=["open", "close", "high", "low", "volume", "amount", "preclose"],
                stock_list=[stock],
                period="1d",
                start_time=start_time,
                end_time=end_time,
                dividend_type="none"
            )
            
            if data and 'close' in data and isinstance(data['close'], pd.DataFrame) and stock in data['close'].index:
                # 转换数据格式：从wide format转为long format
                stock_data_list = []
                for field in ["open", "close", "high", "low", "volume", "amount", "preclose"]:
                    if field in data and stock in data[field].index:
                        field_series = data[field].loc[stock]
                        field_series.name = field
                        stock_data_list.append(field_series)
                
                if stock_data_list:
                    # 合并所有字段数据
                    df = pd.concat(stock_data_list, axis=1)
                    df = df.reset_index()
                    
                    # 重命名索引列为time
                    if df.columns[0] == 'index':
                        df = df.rename(columns={'index': 'time'})
                    elif df.columns[0] not in ['time', 'date']:
                        df = df.rename(columns={df.columns[0]: 'time'})
                    
                    df['code'] = stock
                    
                    # 确保time列是字符串格式，然后转换为日期
                    try:
                        df['time'] = df['time'].astype(str)
                        df['date'] = pd.to_datetime(df['time'], format='%Y%m%d').dt.date
                    except Exception as date_error:
                        logger.error(f"日期转换错误: {date_error}")
                        return 0
                    
                    # 重新排列列顺序
                    final_columns = ['code', 'date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'preclose']
                    available_columns = [col for col in final_columns if col in df.columns]
                    df = df[available_columns]
                    
                    if not df.empty:
                        # 存储到数据库（线程安全）
                        self._upsert_raw_data(df)
                        
                        # 获取除权除息数据
                        try:
                            divid_data = xtdata.get_divid_factors(stock)
                            if divid_data is not None and not divid_data.empty:
                                self._upsert_divid_data(stock, divid_data)
                        except Exception as divid_error:
                            logger.error(f"获取 {stock} 除权除息数据失败: {divid_error}")
                        
                        # 更新记录
                        self._update_log(stock, df['date'].max())
                        return len(df)
            
            return 0
            
        except Exception as e:
            logger.error(f"单只股票 {stock} 数据下载失败: {e}")
            return 0
    
    def schedule_daily_update(self, stock_list, update_time="09:30"):
        """定期每日更新（需要安装schedule: pip install schedule）"""
        try:
            import schedule
        except ImportError:
            logger.error("请先安装schedule模块: pip install schedule")
            return
            
        def job():
            logger.info("开始定期数据更新")
            self.incremental_update(stock_list)
        
        schedule.every().day.at(update_time).do(job)
        logger.info(f"已设置每日 {update_time} 定期更新")
        
        # 运行调度器
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def get_update_status(self):
        """获取数据更新状态"""
        result = self.conn.execute("""
        SELECT code, last_update 
        FROM update_log 
        ORDER BY last_update DESC
        """).df()
        return result
    
    def get_all_a_stocks(self):
        """获取所有沪深A股股票列表"""
        try:
            # 直接获取沪深A股列表
            a_stocks = xtdata.get_stock_list_in_sector('沪深A股')
            
            if a_stocks and len(a_stocks) > 0:
                logger.info(f"获取到A股数量: {len(a_stocks)}")
                return sorted(a_stocks)
            else:
                # 备选方案：获取主要指数成分股
                logger.warning("无法获取沪深A股列表，尝试获取指数成分股...")
                all_stocks = []
                
                try:
                    # 获取沪深300成分股
                    hs300 = xtdata.get_stock_list_in_sector('沪深300')
                    # 获取中证500成分股
                    zz500 = xtdata.get_stock_list_in_sector('中证500')
                    # 获取创业板指成分股
                    cyb = xtdata.get_stock_list_in_sector('创业板指')
                    # 获取科创50成分股
                    kc50 = xtdata.get_stock_list_in_sector('科创50')
                    
                    if hs300:
                        all_stocks.extend(hs300)
                    if zz500:
                        all_stocks.extend(zz500)
                    if cyb:
                        all_stocks.extend(cyb)
                    if kc50:
                        all_stocks.extend(kc50)
                    
                    # 去重
                    a_stocks = sorted(list(set(all_stocks)))
                    logger.info(f"通过指数成分股获取到 {len(a_stocks)} 只股票")
                    return a_stocks
                    
                except Exception as e:
                    logger.error(f"获取指数成分股失败: {e}")
                    # 返回默认的主要A股列表
                    return [
                        "000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "000858.SZ",
                        "002594.SZ", "600519.SH", "000596.SZ", "601318.SH", "300001.SZ",
                        "688001.SH", "688012.SH"  # 包含创业板和科创板样本
                    ]
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            # 返回默认的主要A股列表
            return [
                "000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "000858.SZ",
                "002594.SZ", "600519.SH", "000596.SZ", "601318.SH", "300001.SZ",
                "688001.SH", "688012.SH"
            ]
    
    def download_all_a_stocks_multithread(self, start_time=None, max_workers=8, batch_size=200, progress_callback=None):
        """多线程下载所有A股数据"""
        if start_time is None:
            start_time = "20240101"
        
        # 获取所有A股列表
        stock_list = self.get_all_a_stocks()
        logger.info(f"准备多线程下载 {len(stock_list)} 只A股数据，线程数: {max_workers}，批次大小: {batch_size}")
        
        # 分批处理，避免一次性下载过多
        total_batches = (len(stock_list) + batch_size - 1) // batch_size
        total_success = 0
        total_failed = []
        
        for i in range(0, len(stock_list), batch_size):
            batch_stocks = stock_list[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"开始处理第 {batch_num}/{total_batches} 批股票数据，共 {len(batch_stocks)} 只")
            
            # 批次进度回调
            def batch_progress_callback(msg, progress):
                if progress_callback:
                    # 计算整体进度
                    batch_progress = ((batch_num - 1) / total_batches) * 100
                    current_batch_progress = (progress / 100) * (100 / total_batches)
                    total_progress = batch_progress + current_batch_progress
                    
                    progress_callback(f"第{batch_num}/{total_batches}批: {msg}", total_progress)
            
            # 使用多线程处理当前批次
            success_count, failed_stocks = self.download_raw_data_multithread(
                batch_stocks, start_time, max_workers=max_workers, 
                progress_callback=batch_progress_callback
            )
            
            total_success += success_count
            total_failed.extend(failed_stocks)
            
            logger.info(f"第 {batch_num} 批完成: 成功 {success_count} 只，失败 {len(failed_stocks)} 只")
            
            # 短暂休息，避免对服务器造成过大压力
            if batch_num < total_batches:
                time.sleep(2)
        
        logger.info(f"所有A股多线程下载完成: 总成功 {total_success} 只，总失败 {len(total_failed)} 只")
        if progress_callback:
            progress_callback(f"全部完成: 成功 {total_success} 只，失败 {len(total_failed)} 只", 100)
        return total_success, total_failed
    
    def download_all_a_stocks(self, start_time=None):
        """下载所有A股数据"""
        if start_time is None:
            start_time = "20240101"
        # 获取所有A股列表
        stock_list = self.get_all_a_stocks()
        # logger.info(f"准备下载 {len(stock_list)} 只A股数据")
        
        # 批量下载数据（分批处理，避免一次性下载过多）
        batch_size = 100  # 每批100只股票
        total_batches = (len(stock_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(stock_list), batch_size):
            batch_stocks = stock_list[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            
            # logger.info(f"开始下载第 {batch_num}/{total_batches} 批股票数据，共 {len(batch_stocks)} 只")
            self.download_raw_data(batch_stocks, start_time)
            
            # 短暂休息，避免对服务器造成过大压力
            import time
            time.sleep(2)
        
        # logger.info(f"所有A股数据下载完成")
    
    def close(self):
        """关闭数据库连接"""
        self.conn.close()
        logger.info("数据库连接已关闭")


# 沪深A股数据获取脚本
if __name__ == "__main__":
    # 初始化数据库
    db = MiniqmtDuckDB()
    
    print("=== 开始获取沪深A股数据 ===")
    
    # 获取所有A股并下载数据
    print("正在获取A股列表...")
    a_stocks = db.get_all_a_stocks()
    print(f"找到 {len(a_stocks)} 只A股")
    
    # 显示前10只股票作为示例
    print("前10只股票示例:")
    for i, stock in enumerate(a_stocks[:10]):
        print(f"  {i+1}. {stock}")
    
    # 开始下载所有A股数据
    print(f"\n开始下载所有 {len(a_stocks)} 只A股的历史数据...")
    print("下载起始时间: 2024年1月1日")
    print("这可能需要较长时间，请耐心等待...\n")
    
    try:
        db.download_all_a_stocks(start_time="20240101")
        print("✅ 所有A股数据下载完成！")
        
        # 查看更新状态
        print("\n数据库统计:")
        status_df = db.get_update_status()
        print(f"成功下载股票数量: {len(status_df)}")
        print(f"最新更新日期: {status_df['last_update'].max() if not status_df.empty else '无数据'}")
        
    except Exception as e:
        print(f"❌ 下载过程中出现错误: {e}")
        print("你可以稍后运行增量更新来补充缺失的数据")
    
    # 关闭连接
    db.close()
    print("\n数据库连接已关闭")
    print("\n=== 后续使用说明 ===")
    print("1. 每日更新数据:")
    print("   db = MiniqmtDuckDB()")
    print("   db.incremental_update()")
    print("   db.close()")
    print("\n2. 查询前复权数据:")
    print("   data = db.get_market_data(")
    print("       stock_list=['000001.SZ'],")
    print("       field_list=['close'],")
    print("       start_time='2024-01-01',")
    print("       dividend_type='front'")
    print("   )")