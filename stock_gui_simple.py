import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.ttk import Progressbar, Style
import pandas as pd
from datetime import datetime, timedelta
import threading
import logging
from miniqmt_duckdb import MiniqmtDuckDB
from color_config import get_color_scheme

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleStockGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("沪深A股数据查询系统 - 简化版")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 设置主题样式
        self.setup_styles()
        
        # 当前数据
        self.current_data = None
        self.current_stock = None
        
        # 创建界面
        self.create_widgets()
        
        # 数据库连接
        self.db = None
        self.init_database()
        
        # 绑定快捷键
        self.setup_shortcuts()
        
    def setup_styles(self):
        """设置现代化主题样式"""
        style = Style()
        
        # 设置主题
        try:
            style.theme_use('clam')
        except:
            style.theme_use('default')
        
        # 从颜色配置文件获取颜色方案
        color_scheme = get_color_scheme('green')
        colors = {
            'bg': color_scheme['bg'],
            'fg': color_scheme['fg'],
            'select_bg': color_scheme['select_bg'],
            'select_fg': 'white',
            'button_bg': color_scheme['button_bg'],
            'button_fg': 'white'
        }
        
        # 配置样式
        style.configure('TFrame', background=colors['bg'])
        style.configure('TLabelframe', background=colors['bg'], foreground=colors['fg'])
        style.configure('TLabelframe.Label', background=colors['bg'], foreground=colors['fg'], font=('Microsoft YaHei', 10, 'bold'))
        style.configure('TLabel', background=colors['bg'], foreground=colors['fg'], font=('Microsoft YaHei', 9))
        style.configure('TButton', background=colors['button_bg'], foreground=colors['button_fg'], 
                       font=('Microsoft YaHei', 9), borderwidth=0)
        style.map('TButton',
                 background=[('active', color_scheme['button_active']), ('pressed', color_scheme['button_pressed'])])
        style.configure('TEntry', fieldbackground='white', borderwidth=1, font=('Microsoft YaHei', 9))
        style.configure('TCombobox', fieldbackground='white', borderwidth=1, font=('Microsoft YaHei', 9))
        
        # Treeview样式
        style.configure('Treeview', background='white', foreground=colors['fg'], 
                       fieldbackground='white', font=('Microsoft YaHei', 9))
        style.configure('Treeview.Heading', background=colors['select_bg'], foreground='white', 
                       font=('Microsoft YaHei', 10, 'bold'))
        style.map('Treeview', 
                 background=[('selected', colors['select_bg'])],
                 foreground=[('selected', 'white')])
        
        # 设置根窗口背景
        self.root.configure(bg=colors['bg'])
        
    def init_database(self):
        """初始化数据库连接"""
        try:
            self.db = MiniqmtDuckDB()
            logger.info("数据库连接成功")
            self.show_status("数据库连接成功", "success")
        except Exception as e:
            messagebox.showerror("错误", f"数据库连接失败: {e}")
            self.show_status("数据库连接失败", "error")
    
    def create_widgets(self):
        """创建界面组件"""
        # 创建主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建顶部工具栏
        self.create_toolbar(main_container)
        
        # 创建查询区域
        self.create_query_area(main_container)
        
        # 创建数据表格区域
        self.create_data_table(main_container)
        
        # 创建底部状态栏
        self.create_status_bar(main_container)
        
    def create_toolbar(self, parent):
        """创建顶部工具栏"""
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 导出按钮
        export_btn = ttk.Button(toolbar_frame, text="📊 导出数据", command=self.export_data)
        export_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 刷新按钮
        refresh_btn = ttk.Button(toolbar_frame, text="🔄 刷新", command=self.refresh_data)
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空按钮
        clear_btn = ttk.Button(toolbar_frame, text="🗑️ 清空", command=self.clear_data)
        clear_btn.pack(side=tk.LEFT, padx=(0, 10))
        
    def create_query_area(self, parent):
        """创建查询区域"""
        query_frame = ttk.LabelFrame(parent, text="📈 数据查询", padding="15")
        query_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建网格布局
        for i in range(4):
            query_frame.columnconfigure(i, weight=1)
        
        # 第一行：股票代码和日期
        row = 0
        
        # 股票代码
        ttk.Label(query_frame, text="股票代码:").grid(row=row, column=0, sticky=tk.W, pady=(0, 5))
        self.stock_code_var = tk.StringVar(value="000001.SZ")
        stock_entry = ttk.Entry(query_frame, textvariable=self.stock_code_var, width=15)
        stock_entry.grid(row=row, column=1, sticky=tk.W, pady=(0, 5), padx=(5, 10))
        
        # 开始日期
        ttk.Label(query_frame, text="开始日期:").grid(row=row, column=2, sticky=tk.W, pady=(0, 5), padx=(10, 0))
        self.start_date_var = tk.StringVar(value="2024-01-01")
        start_date_entry = ttk.Entry(query_frame, textvariable=self.start_date_var, width=12)
        start_date_entry.grid(row=row, column=3, sticky=tk.W, pady=(0, 5), padx=(5, 10))
        
        # 第二行：结束日期和复权方式
        row = 1
        
        # 结束日期
        ttk.Label(query_frame, text="结束日期:").grid(row=row, column=0, sticky=tk.W, pady=(5, 0))
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(query_frame, textvariable=self.end_date_var, width=12)
        end_date_entry.grid(row=row, column=1, sticky=tk.W, pady=(5, 0), padx=(5, 10))
        
        # 复权方式
        ttk.Label(query_frame, text="复权方式:").grid(row=row, column=2, sticky=tk.W, pady=(5, 0), padx=(10, 0))
        self.dividend_type_var = tk.StringVar(value="front")
        dividend_combo = ttk.Combobox(query_frame, textvariable=self.dividend_type_var, 
                                    values=["none", "front", "back", "front_ratio", "back_ratio"],
                                    state="readonly", width=12)
        dividend_combo.grid(row=row, column=3, sticky=tk.W, pady=(5, 0), padx=(5, 10))
        
        # 第三行：查询按钮和数据更新
        row = 2
        
        # 按钮框架
        button_frame = ttk.Frame(query_frame)
        button_frame.grid(row=row, column=0, columnspan=4, pady=(10, 0))
        
        # 查询按钮
        query_btn = ttk.Button(button_frame, text="🔍 查询数据", command=self.query_data)
        query_btn.pack(side=tk.LEFT)
        
        # 增量更新按钮
        self.update_btn = ttk.Button(button_frame, text="📥 增量更新", command=self.update_data)
        self.update_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 下载所有A股按钮
        self.download_all_btn = ttk.Button(button_frame, text="📊 下载所有A股", command=self.download_all_data)
        self.download_all_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = Progressbar(button_frame, variable=self.progress_var, 
                                      maximum=100, length=200)
        self.progress_bar.pack(side=tk.LEFT, padx=(20, 10))
        
    def create_data_table(self, parent):
        """创建数据表格区域"""
        table_frame = ttk.LabelFrame(parent, text="📋 数据表格", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "昨收", "涨跌幅", "涨跌额")
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # 设置列标题和宽度
        column_widths = {"日期": 100, "开盘": 80, "收盘": 80, "最高": 80, "最低": 80, 
                        "成交量": 100, "成交额": 100, "昨收": 80, "涨跌幅": 80, "涨跌额": 80}
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=column_widths.get(col, 80))
        
        # 添加滚动条
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscroll=v_scrollbar.set, xscroll=h_scrollbar.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 配置网格权重
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        
        # 绑定右键菜单
        self.tree.bind("<Button-3>", self.show_context_menu)
        
        # 创建右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制选中行", command=self.copy_selected_row)
        self.context_menu.add_command(label="导出选中数据", command=self.export_selected_data)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="查看详情", command=self.show_row_details)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT)
        
        # 统计信息标签
        self.stats_var = tk.StringVar(value="请查询数据以显示统计信息")
        self.stats_label = ttk.Label(status_frame, textvariable=self.stats_var)
        self.stats_label.pack(side=tk.RIGHT)
        
    def setup_shortcuts(self):
        """设置快捷键"""
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-r>', lambda e: self.refresh_data())
        self.root.bind('<Control-e>', lambda e: self.export_data())
        self.root.bind('<F5>', lambda e: self.refresh_data())
        self.root.bind('<Return>', lambda e: self.query_data())
        
    def show_status(self, message, status_type="info"):
        """显示状态信息"""
        self.status_var.set(message)
        if status_type == "error":
            self.status_label.configure(foreground="red")
        elif status_type == "success":
            self.status_label.configure(foreground="green")
        else:
            self.status_label.configure(foreground="black")
        self.root.update()
        
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
            self.show_status("正在查询数据...", "info")
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
                    
                    # 计算涨跌幅和涨跌额
                    df['涨跌额'] = df['收盘'] - df['昨收']
                    df['涨跌幅'] = (df['涨跌额'] / df['昨收'] * 100).round(2)
                    
                    # 保存当前数据
                    self.current_data = df
                    self.current_stock = stock_code
                    
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
                            f"{row['昨收']:.2f}" if pd.notna(row['昨收']) else "N/A",
                            f"{row['涨跌幅']:+.2f}%" if pd.notna(row['涨跌幅']) else "N/A",
                            f"{row['涨跌额']:+.2f}" if pd.notna(row['涨跌额']) else "N/A"
                        ]
                        
                        # 根据涨跌幅设置颜色标签
                        tags = ()
                        if pd.notna(row['涨跌幅']):
                            if row['涨跌幅'] > 0:
                                tags = ('red',)
                            elif row['涨跌幅'] < 0:
                                tags = ('green',)
                        
                        self.tree.insert("", "end", values=formatted_row, tags=tags)
                    
                    # 设置标签颜色
                    self.tree.tag_configure('red', foreground='red')
                    self.tree.tag_configure('green', foreground='green')
                    
                    # 更新统计信息
                    self.update_stats(df, stock_code)
                    
                    self.show_status(f"查询完成，共 {len(df)} 条记录", "success")
                else:
                    messagebox.showinfo("信息", f"股票 {stock_code} 在指定日期范围内无数据")
                    self.show_status("无数据", "info")
            else:
                messagebox.showinfo("信息", f"未找到股票 {stock_code} 的数据，请检查股票代码或先下载数据")
                self.show_status("无数据", "info")
                
        except Exception as e:
            messagebox.showerror("错误", f"查询数据时出错: {e}")
            self.show_status("查询失败", "error")
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
            total_amount = df['成交额'].sum()
            
            change = end_price - start_price
            change_pct = (change / start_price * 100) if start_price != 0 else 0
            
            stats_text = (f"{stock_code} | "
                         f"期间涨跌: {change:+.2f}({change_pct:+.2f}%) | "
                         f"最高: {max_price:.2f} | 最低: {min_price:.2f} | "
                         f"平均成交量: {avg_volume:.0f} | 总成交额: {total_amount:.0f}")
            
            self.stats_var.set(stats_text)
        except Exception as e:
            logger.error(f"更新统计信息失败: {e}")
    
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def copy_selected_row(self):
        """复制选中行"""
        selected_items = self.tree.selection()
        if selected_items:
            item = self.tree.item(selected_items[0])
            values = item['values']
            text = '\t'.join(str(v) for v in values)
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.show_status("已复制到剪贴板", "success")
    
    def export_selected_data(self):
        """导出选中数据"""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择要导出的数据")
            return
        
        # 获取选中数据
        data = []
        for item in selected_items:
            values = self.tree.item(item)['values']
            data.append(values)
        
        # 导出到文件
        self.export_to_file(data)
    
    def show_row_details(self):
        """显示行详情"""
        selected_items = self.tree.selection()
        if selected_items:
            item = self.tree.item(selected_items[0])
            values = item['values']
            
            # 创建详情窗口
            detail_window = tk.Toplevel(self.root)
            detail_window.title("数据详情")
            detail_window.geometry("400x300")
            
            columns = ["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "昨收", "涨跌幅", "涨跌额"]
            
            for i, (col, val) in enumerate(zip(columns, values)):
                ttk.Label(detail_window, text=f"{col}:").grid(row=i, column=0, sticky=tk.W, padx=10, pady=5)
                ttk.Label(detail_window, text=str(val)).grid(row=i, column=1, sticky=tk.W, padx=10, pady=5)
    
    def sort_by_column(self, col):
        """按列排序"""
        # 这里可以实现列排序逻辑
        self.show_status(f"按{col}排序", "info")
    
    def export_data(self):
        """导出数据"""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        self.export_to_file(self.current_data)
    
    def export_to_file(self, data):
        """导出到文件"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV文件", "*.csv"), ("Excel文件", "*.xlsx"), ("所有文件", "*.*")]
            )
            
            if file_path:
                if isinstance(data, pd.DataFrame):
                    if file_path.endswith('.xlsx'):
                        data.to_excel(file_path, index=True)
                    else:
                        data.to_csv(file_path, index=True)
                else:
                    # 列表数据
                    df = pd.DataFrame(data)
                    if file_path.endswith('.xlsx'):
                        df.to_excel(file_path, index=False)
                    else:
                        df.to_csv(file_path, index=False)
                
                self.show_status(f"数据已导出到: {file_path}", "success")
                messagebox.showinfo("成功", "数据导出成功")
        except Exception as e:
            messagebox.showerror("错误", f"导出数据时出错: {e}")
            self.show_status("导出失败", "error")
    
    def refresh_data(self):
        """刷新数据"""
        if self.current_stock:
            self.query_data()
        else:
            self.show_status("请先查询数据", "info")
    
    def clear_data(self):
        """清空数据"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 清空当前数据
        self.current_data = None
        self.current_stock = None
        
        # 重置状态
        self.stats_var.set("请查询数据以显示统计信息")
        self.show_status("数据已清空", "info")
    
    def update_data(self):
        """增量更新数据"""
        def update_thread():
            try:
                self.update_btn.config(state="disabled")
                self.show_status("正在增量更新...", "info")
                self.progress_var.set(0)
                
                # 模拟进度更新
                for i in range(0, 101, 10):
                    self.progress_var.set(i)
                    self.root.update()
                    
                    if i == 50:
                        # 执行实际更新
                        self.db.incremental_update()
                
                self.show_status("增量更新完成", "success")
                messagebox.showinfo("成功", "数据更新完成")
                
            except Exception as e:
                messagebox.showerror("错误", f"更新数据时出错: {e}")
                self.show_status("更新失败", "error")
            finally:
                self.update_btn.config(state="normal")
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
                self.download_all_btn.config(state="disabled")
                self.update_btn.config(state="disabled")
                self.show_status("正在下载所有A股数据...", "info")
                
                # 获取股票列表
                stock_list = self.db.get_all_a_stocks()
                total_stocks = len(stock_list)
                
                if total_stocks == 0:
                    messagebox.showwarning("警告", "未获取到股票列表")
                    return
                
                # 定义进度回调函数
                def progress_callback(message, progress):
                    self.show_status(message, "info")
                    self.progress_var.set(progress)
                    self.root.update()
                
                # 使用多线程下载，提高速度
                success_count, failed_stocks = self.db.download_all_a_stocks_multithread(
                    start_time="20240101",
                    max_workers=8,
                    batch_size=200,
                    progress_callback=progress_callback
                )
                
                self.show_status(f"下载完成，成功 {success_count} 只，失败 {len(failed_stocks)} 只", "success")
                messagebox.showinfo("成功", f"A股数据下载完成！成功 {success_count} 只，失败 {len(failed_stocks)} 只")
                
            except Exception as e:
                messagebox.showerror("错误", f"下载数据时出错: {e}")
                self.show_status("下载失败", "error")
            finally:
                self.download_all_btn.config(state="normal")
                self.update_btn.config(state="normal")
                self.progress_var.set(0)
        
        # 在新线程中执行下载
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
    
    def __del__(self):
        """析构函数，关闭数据库连接"""
        if self.db:
            self.db.close()

def main():
    root = tk.Tk()
    app = SimpleStockGUI(root)
    
    # 处理窗口关闭事件
    def on_closing():
        if app.db:
            app.db.close()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()