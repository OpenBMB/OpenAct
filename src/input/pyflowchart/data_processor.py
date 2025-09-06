def load_data(filepath):
    if filepath.endswith('.csv'):
        return "csv_data"
    elif filepath.endswith('.json'):
        return "json_data"
    else:
        raise ValueError(f"Unsupported file format: {filepath}")

def clean_data(data):
    cleaned_data = data + "_cleaned"
    return cleaned_data

def transform_data(data, transformations):
    transformed_data = data
    for transform_type in transformations:
        if transform_type == 'normalize':
            transformed_data += "_normalized"
        elif transform_type == 'log':
            transformed_data += "_logged"
    return transformed_data

def export_data(data, output_path, format='csv'):
    if format.lower() == 'csv':
        return f"Exported {data} to CSV at {output_path}"
    elif format.lower() == 'json':
        return f"Exported {data} to JSON at {output_path}"
    else:
        raise ValueError(f"Unsupported export format: {format}")

def process_pipeline(input_file, output_file, transformations=None, export_format='csv'):
    data = load_data(input_file)
    data_clean = clean_data(data)
    
    if transformations:
        data_transformed = transform_data(data_clean, transformations)
    else:
        data_transformed = data_clean
    
    result = export_data(data_transformed, output_file, export_format)
    return result