from src.storage.database.database_manager import DatabaseManager

class BillRepository:
    @staticmethod
    def save(bill_data):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO extracted_bills (source_file, vendor_name, total, raw_text) VALUES (?, ?, ?, ?)",
            (bill_data.source_file if hasattr(bill_data, 'source_file') else "unknown", 
             bill_data.vendor_name, bill_data.total, bill_data.raw_text)
        )
        bill_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bill_id

    @staticmethod
    def get_by_id(bill_id):
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM extracted_bills WHERE id = ?", (bill_id,))
        row = cursor.fetchone()
        conn.close()
        return row
