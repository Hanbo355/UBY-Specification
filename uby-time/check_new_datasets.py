import sqlite3
import os

# 检查新数据集的基本信息
new_datasets = [
    'end_ordovician_sampling_controls.sqlite',
    'end_ordovician_signal.sqlite', 
    'extinction_sensitivity.sqlite',
    'pbdb_collections_animalia_phanerozoic_uby.sqlite',
    'pbdb_extinction_dynamics.sqlite',
    'uby_forcing_events.sqlite',
    'uby_forcing_extinction_leadlag.sqlite',
    'uby_mass_extinction_lag.sqlite'
]

print('检查新数据集的结构和记录数:')
for dataset in new_datasets:
    db_path = f'data/processed/{dataset}'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 获取表名
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f'\n{dataset}:')
            print(f'  表: {tables}')
            
            # 检查主要表的记录数和结构
            for table in tables:
                if 'uby' in table.lower() or 'events' in table.lower() or len(tables) == 1:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    count = cursor.fetchone()[0]
                    print(f'  {table}: {count:,} 条记录')
                    
                    # 检查表结构
                    cursor.execute(f'PRAGMA table_info({table})')
                    columns = [col[1] for col in cursor.fetchall()]
                    if len(columns) > 5:
                        print(f'    字段: {columns[:5]}...')
                    else:
                        print(f'    字段: {columns}')
            
            conn.close()
        except Exception as e:
            print(f'  错误: {e}')
    else:
        print(f'{dataset}: 文件不存在')
