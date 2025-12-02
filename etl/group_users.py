import psycopg2
import pandas as pd
import argparse
import logging
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection(db_uri):
    """Create database connection"""
    return psycopg2.connect(db_uri)

def group_users_by_field(conn, field, output_dir):
    """Group users by specified field and save to CSV"""
    
    field_mapping = {
        'bank_name': ('user_bank_info', 'bank_name', 'group_by_bank'),
        'company_name': ('employment_info', 'company_name', 'group_by_company'),
        'pincode': ('users', 'pincode', 'group_by_pincode')
    }
    
    if field not in field_mapping:
        raise ValueError(f"Unsupported field: {field}")
    
    table, column, file_prefix = field_mapping[field]
    
    query = f"""
        SELECT {column} as group_key, 
               COUNT(DISTINCT u.id) as user_count,
               ARRAY_AGG(u.id) as user_ids
        FROM users u
        LEFT JOIN employment_info e ON u.id = e.user_id
        LEFT JOIN user_bank_info b ON u.id = b.user_id
        WHERE {column} IS NOT NULL
        GROUP BY {column}
        ORDER BY user_count DESC
    """
    
    try:
        df = pd.read_sql_query(query, conn)
        logger.info(f"Grouped by {field}: found {len(df)} groups")
        
        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{file_prefix}_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {field} grouping to {filepath}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"Error grouping by {field}: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Group users by various fields')
    parser.add_argument('--output-dir', default='output', help='Output directory for CSV files')
    parser.add_argument('--db-uri', required=True, help='Database connection URI')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Connect to database
        conn = get_db_connection(args.db_uri)
        logger.info("Connected to database successfully")
        
        # Group by different fields
        fields = ['bank_name', 'company_name', 'pincode']
        
        for field in fields:
            group_users_by_field(conn, field, args.output_dir)
        
        logger.info("ETL process completed successfully")
        
    except Exception as e:
        logger.error(f"ETL process failed: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()


# if you want to run etl code put this code.... 
    #python group_users.py --output-dir output --db-uri "postgresql://postgres:karthickraj5@localhost/user_management"