import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.ttk import Progressbar
import pandas as pd
from datetime import datetime, timedelta
import threading
import logging
from miniqmt_duckdb import MiniqmtDuckDB

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("沪深A股数据查询系统")
        self.root.geometry("1200x700")
        
        # 数据库连接
        self.db = None
        self.init_database()
        
        # 创建界面
        self.create_widgets()
        
    def init_database(self):
        """初始化数据库连接"""
        try:
            self.db = MiniqmtDuckDB()
            logger.info("数据库连接成功")
        except Exception as e:
            messagebox.showerror("错误", f"数据库连接失败: {e}")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 查询区域
        query_frame = ttk.LabelFrame(main_frame, text="数据查询", padding="10")
        query_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 股票代码输入
        ttk.Label(query_frame, text="股票代码:").grid(row=0, column=0, sticky=tk.W)
        self.stock_code_var = tk.StringVar(value="000001.SZ")
        stock_entry = ttk.Entry(query_frame, textvariable=self.stock_code_var, width=15)
        stock_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        
        # 开始日期
        ttk.Label(query_frame, text="开始日期:").grid(row=0, column=2, sticky=tk.W)
        self.start_date_var = tk.StringVar(value="2024-01-01")
        start_date_entry = ttk.Entry(query_frame, textvariable=self.start_date_var, width=12)
        start_date_entry.grid(row=0, column=3, sticky=tk.W, padx=(5, 10))
        
        # 结束日期
        ttk.Label(query_frame, text="结束日期:").grid(row=0, column=4, sticky=tk.W)
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(query_frame, textvariable=self.end_date_var, width=12)
        end_date_entry.grid(row=0, column=5, sticky=tk.W, padx=(5, 10))
        
        # 复权方式选择
        ttk.Label(query_frame, text="复权方式:").grid(row=1, column=0, sticky=tk.W, pady=(10, 0))
        self.dividend_type_var = tk.StringVar(value="front")
        dividend_combo = ttk.Combobox(query_frame, textvariable=self.dividend_type_var, 
                                    values=["none", "front", "back", "front_ratio", "back_ratio"],
                                    state="readonly", width=12)
        dividend_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 10), pady=(10, 0))
        
        # 查询按钮
        query_button = ttk.Button(query_frame, text="查询数据", command=self.query_data)
        query_button.grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 测试按钮
        test_button = ttk.Button(query_frame, text="测试", command=self.test_function)
        test_button.grid(row=1, column=3, sticky=tk.W, padx=(10, 0), pady=(10, 0))
        
        # 数据更新区域
        update_frame = ttk.LabelFrame(main_frame, text="数据更新", padding="10")
        update_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 更新按钮
        self.update_button = ttk.Button(update_frame, text="增量更新数据", command=self.update_data)
        self.update_button.grid(row=0, column=0, sticky=tk.W)
        
        self.download_all_button = ttk.Button(update_frame, text="下载所有A股", command=self.download_all_data)
        self.download_all_button.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = Progressbar(update_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(10, 0))
        update_frame.columnconfigure(2, weight=1)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(update_frame, textvariable=self.status_var)
        self.status_label.grid(row=0, column=3, sticky=tk.W, padx=(10, 0))
        
        # 数据显示区域
        data_frame = ttk.LabelFrame(main_frame, text="数据显示", padding="10")
        data_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        data_frame.columnconfigure(0, weight=1)
        data_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示数据
        columns = ("日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "昨收")
        self.tree = ttk.Treeview(data_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(data_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 统计信息区域
        stats_frame = ttk.LabelFrame(main_frame, text="统计信息", padding="10")
        stats_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.stats_var = tk.StringVar(value="请查询数据以显示统计信息")
        self.stats_label = ttk.Label(stats_frame, textvariable=self.stats_var)
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
    
    def query_data(self):
        """查询股票数据"""
        try:
            # 清空之前的数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            stock_code = self.stock_code_var.get().upper()
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            dividend_type = self.dividend_type_var.get()
            
            if not stock_code:
                messagebox.showwarning("警告", "请输入股票代码")
                return
            
            # 查询数据
            self.status_var.set("正在查询数据...")
            self.root.update()
            
            data = self.db.get_market_data(
                stock_list=[stock_code],
                field_list=["open", "close", "high", "low", "volume", "amount", "preclose"],
                start_time=start_date,
                end_time=end_date,
                dividend_type=dividend_type
            )
            
            if data and "close" in data and stock_code in data["close"]:
                # 组合数据
                df_data = []
                for field in ["open", "close", "high", "low", "volume", "amount", "preclose"]:
                    if field in data and stock_code in data[field]:
                        df_data.append(data[field][stock_code])
                
                if df_data:
                    # 创建DataFrame
                    df = pd.concat(df_data, axis=1)
                    df.columns = ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "昨收"]
                    df = df.sort_index()
                    
                    # 添加到表格
                    for date, row in df.iterrows():
                        # 格式化数据
                        formatted_row = [
                            date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date),
                            f"{row['开盘']:.2f}" if pd.notna(row['开盘']) else "N/A",
                            f"{row['收盘']:.2f}" if pd.notna(row['收盘']) else "N/A",
                            f"{row['最高']:.2f}" if pd.notna(row['最高']) else "N/A",
                            f"{row['最低']:.2f}" if pd.notna(row['最低']) else "N/A",
                            f"{int(row['成交量'])}" if pd.notna(row['成交量']) else "N/A",
                            f"{row['成交额']:.0f}" if pd.notna(row['成交额']) else "N/A",
                            f"{row['昨收']:.2f}" if pd.notna(row['昨收']) else "N/A"
                        ]
                        self.tree.insert("", "end", values=formatted_row)
                    
                    # 更新统计信息
                    self.update_stats(df, stock_code)
                    self.status_var.set(f"查询完成，共 {len(df)} 条记录")
                else:
                    messagebox.showinfo("信息", f"股票 {stock_code} 在指定日期范围内无数据")
                    self.status_var.set("无数据")
            else:
                messagebox.showinfo("信息", f"未找到股票 {stock_code} 的数据，请检查股票代码或先下载数据")
                self.status_var.set("无数据")
                
        except Exception as e:
            messagebox.showerror("错误", f"查询数据时出错: {e}")
            self.status_var.set("查询失败")
            logger.error(f"查询数据失败: {e}")
    
    def update_stats(self, df, stock_code):
        """更新统计信息"""
        if df.empty:
            return
        
        try:
            start_price = df['收盘'].iloc[0] if len(df) > 0 else 0
            end_price = df['收盘'].iloc[-1] if len(df) > 0 else 0
            max_price = df['最高'].max()
            min_price = df['最低'].min()
            avg_volume = df['成交量'].mean()
            
            change = end_price - start_price
            change_pct = (change / start_price * 100) if start_price != 0 else 0
            
            stats_text = (f"{stock_code} | "
                         f"期间涨跌: {change:.2f}({change_pct:+.2f}%) | "
                         f"最高: {max_price:.2f} | 最低: {min_price:.2f} | "
                         f"平均成交量: {avg_volume:.0f}")
            
            self.stats_var.set(stats_text)
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def update_data(self):
        """增量更新数据"""
        def update_thread():
            try:
                self.update_button.config(state="disabled")
                self.status_var.set("正在增量更新...")
                self.progress_var.set(0)
                
                # 模拟进度更新
                for i in range(0, 101, 10):
                    self.progress_var.set(i)
                    self.root.update()
                    
                    if i == 50:
                        # 执行实际更新
                        self.db.incremental_update()
                
                self.status_var.set("增量更新完成")
                messagebox.showinfo("成功", "数据更新完成")
                
            except Exception as e:
                messagebox.showerror("错误", f"更新数据时出错: {e}")
                self.status_var.set("更新失败")
            finally:
                self.update_button.config(state="normal")
                self.progress_var.set(0)
        
        # 在新线程中执行更新
        thread = threading.Thread(target=update_thread)
        thread.daemon = True
        thread.start()
    
    def download_all_data(self):
        """下载所有A股数据"""
        result = messagebox.askyesno("确认", 
                                   "下载所有A股数据可能需要很长时间，确定要继续吗？")
        if not result:
            return
        
        def download_thread():
            try:
                self.download_all_button.config(state="disabled")
                self.update_button.config(state="disabled")
                self.status_var.set("正在下载所有A股数据...")
                
                # 获取股票列表
                stock_list = self.db.get_all_a_stocks()
                total_stocks = len(stock_list)
                
                if total_stocks == 0:
                    messagebox.showwarning("警告", "未获取到股票列表")
                    return
                
                # 分批下载
                batch_size = 100
                completed = 0
                
                # 定义进度回调函数
                def progress_callback(message, progress):
                    self.status_var.set(message)
                    self.progress_var.set(progress)
                    self.root.update()  # 强制更新GUI
                
                # 使用多线程下载，提高速度
                success_count, failed_stocks = self.db.download_all_a_stocks_multithread(
                    start_time="20240101",
                    max_workers=8,
                    batch_size=200,
                    progress_callback=progress_callback
                )
                
                self.status_var.set(f"下载完成，成功 {success_count} 只，失败 {len(failed_stocks)} 只")
                messagebox.showinfo("成功", f"A股数据下载完成！成功 {success_count} 只，失败 {len(failed_stocks)} 只")
                
            except Exception as e:
                messagebox.showerror("错误", f"下载数据时出错: {e}")
                self.status_var.set("下载失败")
            finally:
                self.download_all_button.config(state="normal")
                self.update_button.config(state="normal")
                self.progress_var.set(0)
        
        # 在新线程中执行下载
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def test_function(self):
        """测试功能函数"""
        pass
    
    def __del__(self):
        """析构函数，关闭数据库连接"""
        if self.db:
            self.db.close()

def main():
    root = tk.Tk()
    app = StockGUI(root)
    
    # 处理窗口关闭事件
    def on_closing():
        if app.db:
            app.db.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()