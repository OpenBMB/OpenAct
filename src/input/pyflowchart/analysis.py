def load_dataset(file_path):
    return {"data": [10, 20, 30, 40, 50]}

def calculate_statistics(data, columns=None, include_outliers=True):
    stats = {}
    
    if not isinstance(data, dict):
        data = {"column1": data}
    
    for col, values in data.items():
        if not columns or col in columns:
            if not include_outliers:
                # Simple outlier removal (values > 40)
                values = [v for v in values if v <= 40]
            
            stats[col] = {
                'mean': sum(values) / len(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            }
            
            # Calculate quartiles
            sorted_values = sorted(values)
            mid = len(sorted_values) // 2
            stats[col]['median'] = sorted_values[mid]
            
    return stats

def visualize_statistics(stats, output_path=None):
    visualization = "Visualization of statistics:\n"
    for col, col_stats in stats.items():
        visualization += f"\n{col}:\n"
        for stat_name, stat_value in col_stats.items():
            visualization += f"  {stat_name}: {stat_value}\n"
    
    if output_path:
        with open(output_path, 'w') as f:
            f.write(visualization)
    
    return visualization

def generate_report(data, output_file=None):
    stats = calculate_statistics(data)
    report = "Statistical Analysis Report\n\n"
    
    for col, col_stats in stats.items():
        report += f"{col}\n"
        for stat_name, stat_value in col_stats.items():
            report += f"{stat_name}: {stat_value}\n"
        report += "\n"
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report)
    
    return report