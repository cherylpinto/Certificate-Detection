import psycopg2
from dotenv import load_dotenv
import os
import sys
import bcrypt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.logging import get_logger
logger = get_logger("Database")

class SupabaseDB:

    """
    Database Tables and their structure:
    
    📌 `admins`

    | Column      | Data Type                   |
    | ----------- | --------------------------- |
    | admin_id    | uuid                        |
    | name        | text                        |
    | email       | text                        |
    | password    | text                        |
    | role        | text                        |
    | created_at  | timestamp without time zone |


    📌 `certificates`

    | Column               | Data Type                   |
    | ---------------------| --------------------------- |
    | cert_id              | uuid                        |
    | student_id           | uuid                        |
    | univ_id              | uuid                        |
    | roll_no              | text                        |
    | student_name_hash    | text                        |
    | dob_hash             | text                        |
    | gpa_hash             | text                        |
    | batch_year           | integer                     |
    | issued_date          | date                        |
    | file_url             | text                        |
    | image_hash           | text                        |
    | signature_embeddings | bytea                       |
    | photo_embeddings     | bytea                       |
    | logo_embeddings      | bytea                       |
    | qr_code_cipher       | text                        |
    | created_at           | timestamp without time zone |
    | clg_code             | text                        |



    📌 `students`

    | Column            | Data Type                   |
    | ----------------- | --------------------------- |
    | student_id        | uuid                        |
    | roll_no           | text                        |
    | name              | text                        |
    | dob               | date                        |
    | email             | text                        |
    | password          | text                        |
    | univ_id           | uuid                        |
    | passed_out_year   | integer                     |
    | created_at        | timestamp without time zone |



    📌 `universities`
    ______________________________________________________
    | Column                | Data Type                   |
    | --------------------- | --------------------------- |
    | univ_id               | uuid                        |
    | name                  | text                        |
    | address               | text                        |
    | private_key           | text                        |
    | public_key            | text                        |
    | signature_embeddings  | bytea                       |
    | logo_embeddings       | bytea                       |
    | stamp_embeddings      | bytea                       |
    | created_at            | timestamp without time zone |
    | university_website    | text                        |

    📌 `verification_logs`

    | Column       | Data Type                   |
    | ------------ | --------------------------- |
    | log_id       | uuid                        |
    | cert_id      | uuid                        |
    | verified_by  | uuid                        |
    | status       | boolean                     |
    | reason       | text                        |
    | verified_at  | timestamp without time zone |

    
    📌 `affiliate_colleges`
    | Column        | Data Type                   |
    | ------------- | --------------------------- |
    | clg_code      | text                        |
    | clg_name      | text                        |
    | clg_address   | text                        |
    | univ_id       | uuid                        |
    | created_at    | timestamp without time zone |
    | clg_web       | text                        |
    """

    def __init__(self):
        """Initialize connection parameters from .env file"""
        load_dotenv()
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.host = os.getenv("host")
        self.port = os.getenv("port")
        self.dbname = os.getenv("dbname")
        self.connection = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                dbname=self.dbname
            )
            self.cursor = self.connection.cursor()
            print("✅ Connection successful!")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")

    def run_query(self, query, fetch_one=False, fetch_all=False):
        """Execute SQL queries"""
        try:
            self.cursor.execute(query)
            if fetch_one:
                return self.cursor.fetchone()
            elif fetch_all:
                return self.cursor.fetchall()
            else:
                self.connection.commit()
        except Exception as e:
            print(f"⚠️ Query failed: {e}")
            return None

    def insert_admin(self, name:str, email:str, password:str, role:str):
        """Insert a new admin into the admins table"""
        try:
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            query = f"""
            INSERT INTO admins (name, email, password, role)
            VALUES ('{name}', '{email}', '{password}', '{role}');
            """
            self.run_query(query)
            logger.info("✅ Admin inserted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to insert admin: {e}")
        
    def delete_admin_by_id(self, admin_id:str):
        """Delete an admin from the admins table"""
        try:
            query = f"DELETE FROM admins WHERE admin_id = '{admin_id}';"
            self.run_query(query)
            logger.info("✅ Admin deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete admin: {e}")

    def update_admin_email(self, admin_id:str, new_email:str):
        """Update an admin's email in the admins table"""
        try:
            query = f"""
            UPDATE admins
            SET email = '{new_email}'
            WHERE admin_id = '{admin_id}';
            """
            self.run_query(query)
            logger.info("✅ Admin email updated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to update admin email: {e}")
    
    def update_admin_password(self, email:str, new_password:str):
        """Update an admin's password in the admins table"""
        try:
            salt = bcrypt.gensalt()
            new_password = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
            query = f"""
            UPDATE admins
            SET password = '{new_password}'
            WHERE email = '{email}';
            """
            self.run_query(query)
            logger.info("✅ Admin password updated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to update admin password: {e}")


    def delete_admin_by_mail(self, email:str):
        """Delete an admin from the admins table"""
        try:
            query = f"DELETE FROM admins WHERE email = '{email}';"
            self.run_query(query)
            logger.info("✅ Admin deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete admin: {e}")


    def get_admin_by_email(self, email:str):
        """Fetch an admin's details by email"""
        try:
            query = f"SELECT admin_id, email, name, role FROM admins WHERE email = '{email}';"
            result = self.run_query(query, fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch admin: {e}")
            return None

    def admin_exists(self, email:str) -> bool:
        """Check if an admin exists by email"""
        try:
            query = f"SELECT 1 FROM admins WHERE email = '{email}';"
            result = self.run_query(query, fetch_one=True)
            return result is not None
        except Exception as e:
            logger.error(f"❌ Failed to check admin existence: {e}")
            return False

    def get_all_admins(self):
        """Fetch all admins"""
        try:
            query = "SELECT admin_id, email, name, role, created_at FROM admins;"
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch admins: {e}")
            return []
    
    def get_admin_count(self) -> int:
        """Get total number of admins"""
        try:
            query = "SELECT COUNT(*) FROM admins;"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Failed to count admins: {e}")
            return 0
    
    def admin_login(self, email:str, password:str) -> bool:
        """Validate admin login credentials"""
        try:
            query = f"SELECT password FROM admins WHERE email = '{email}';"
            result = self.run_query(query, fetch_one=True)
            if result:
                stored_password = result[0]
                return bcrypt.checkpw(password.encode('utf-8'), stored_password.encode('utf-8'))
            return False
        except Exception as e:
            logger.error(f"❌ Failed to validate admin login: {e}")
            return False

    # ================================== End of Admin Management ===================================

    # ================================== Student Management ===================================

    def insert_student(self, name:str, email:str, password:str, roll_no:str, dob:str, univ_id:str, passed_out_year:int):
        """Insert a new student into the students table"""
        try:
            salt = bcrypt.gensalt()
            password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            def check_dob_format(dob_str):
                try:
                    day, month, year = map(int, dob_str.split('-'))
                    if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                        return True
                    return False
                except:
                    return False
            if not check_dob_format(dob):
                logger.error("❌ Invalid date of birth format. Please use DD-MM-YYYY.")
                return
            
            query = f"""
            INSERT INTO students (name, email, password, roll_no, dob, univ_id, passed_out_year)
            VALUES ('{name}', '{email}', '{password}', '{roll_no}', '{dob}', '{univ_id}', {passed_out_year});
            """
            self.run_query(query)
            logger.info("✅ Student inserted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to insert student: {e}")


    def get_student(self, student_id:int):
        """Fetch a student by ID"""
        try:
            query = f"SELECT student_id, name, email, roll_no, dob, univ_id, passed_out_year FROM students WHERE student_id = {student_id};"
            result = self.run_query(query, fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch student: {e}")
            return None

    def update_student(self, student_id:int, name:str, email:str, roll_no:str, dob:str, univ_id:str, passed_out_year:int):
        """Update a student's details"""
        try:
            query = f"""
            UPDATE students
            SET name = '{name}', email = '{email}', roll_no = '{roll_no}', dob = '{dob}', univ_id = '{univ_id}', passed_out_year = {passed_out_year}
            WHERE student_id = {student_id};
            """
            self.run_query(query)
            logger.info("✅ Student updated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to update student: {e}")


    def delete_student_by_id(self, student_id:int):
        """Delete a student by ID"""
        try:
            query = f"DELETE FROM students WHERE student_id = {student_id};"
            self.run_query(query)
            logger.info("✅ Student deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete student: {e}")


    def delete_student_by_mail(self, email:str):
        """Delete a student by email"""
        try:
            query = f"DELETE FROM students WHERE email = '{email}';"
            self.run_query(query)
            logger.info("✅ Student deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete student: {e}")

    
    def display_all_students_certificates_by_id(self, student_id:int):
        """Display all certificates of a student by student ID"""
        try:
            query = f"""
            SELECT c.cert_id, c.roll_no, c.student_name_hash, c.dob_hash, c.gpa_hash, c.batch_year, c.issued_date, c.file_url, c.qr_code_cipher, c.image_hash
            FROM certificates c
            WHERE c.student_id = {student_id};
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch certificates: {e}")
            return []

    def display_all_students_certificates(self):
        """Display all certificates of all students"""
        try:
            query = f"""
            SELECT c.cert_id, c.roll_no, c.student_name_hash, c.dob_hash, c.gpa_hash, c.batch_year, c.issued_date, c.file_url, c.qr_code_cipher, c.image_hash
            FROM certificates c JOIN students s ON c.student_id = s.student_id group by s.email,c.cert_id;
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch certificates: {e}")
            return []
        
    # ================================= End of Student Management ===================================

    # ================================= University Management ===================================

    def insert_university(self, name:str, address:str, private_key:str):
        """Insert a new university into the universities table"""
        try:
            
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            public_key = private_key[::-1] 
            hash_public_key = bcrypt.hashpw(public_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"""
            INSERT INTO universities (name, address, private_key, public_key)
            VALUES ('{name.lower().strip()}', '{address}', '{hash_private_key}', '{hash_public_key}');
            """
            self.run_query(query)
            logger.info("✅ University inserted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to insert university: {e}")

    def get_university(self, univ_id:int):
        """Fetch a university by ID"""
        try:
            query = f"SELECT univ_id, name, address, created_at FROM universities WHERE univ_id = {univ_id};"
            result = self.run_query(query, fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch university: {e}")
            return None
    
    def get_university_by_private_key(self, private_key:str):
        """Fetch a university by private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"SELECT univ_id, name, address, created_at FROM universities WHERE private_key = '{hash_private_key}';"
            result = self.run_query(query, fetch_one=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch university: {e}")
            return None
        
    def update_university_by_univ_id(self, univ_id:int, name:str, address:str, private_key:str):
        """Update a university's details"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            public_key = private_key[::-1] 
            hash_public_key = bcrypt.hashpw(public_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"""
            UPDATE universities
            SET name = '{name}', address = '{address}', private_key = '{hash_private_key}', public_key = '{hash_public_key}'
            WHERE univ_id = {univ_id};
            """
            self.run_query(query)
            logger.info("✅ University updated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to update university: {e}")

    def update_university_by_private_key(self, private_key:str, name:str, address:str):
        """Update a university's details by private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            public_key = private_key[::-1] 
            hash_public_key = bcrypt.hashpw(public_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"""
            UPDATE universities
            SET name = '{name}', address = '{address}', private_key = '{hash_private_key}', public_key = '{hash_public_key}'
            WHERE private_key = '{hash_private_key}';
            """
            self.run_query(query)
            logger.info("✅ University updated successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to update university: {e}")

    def delete_university_by_univ_id(self, univ_id:int):
        """Delete a university by ID"""
        try:
            query = f"DELETE FROM universities WHERE univ_id = {univ_id};"
            self.run_query(query)
            logger.info("✅ University deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete university: {e}")

    def delete_university_by_private_key(self, private_key:str):
        """Delete a university by private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"DELETE FROM universities WHERE private_key = '{hash_private_key}';"
            self.run_query(query)
            logger.info("✅ University deleted successfully!")
        except Exception as e:
            logger.error(f"❌ Failed to delete university: {e}")


    def get_university_private_key_by_univ_id(self, univ_id:int) -> str:
        """Fetch a university's private key by ID"""
        try:
            query = f"SELECT private_key FROM universities WHERE univ_id = {univ_id};"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch private key: {e}")
            return None
    
    def get_university_private_key_by_name(self, name:str) -> str:
        """Fetch a university's private key by name"""
        try:
            query = f"SELECT private_key FROM universities WHERE name = '{name.lower()}';"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch private key: {e}")
            return None
        
    def get_university_univ_id_by_name(self, name:str) -> int:
        """Fetch a university's ID by name"""
        try:
            query = f"SELECT univ_id FROM universities WHERE name = '{name.lower()}';"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch university ID: {e}")
            return None
    
    def get_university_univ_id_by_private_key(self, private_key:str) -> int:
        """Fetch a university's ID by private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"SELECT univ_id FROM universities WHERE private_key = '{hash_private_key}';"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch university ID: {e}")
            return None



    def get_university_count(self) -> int:
        """Get total number of universities"""
        try:
            query = "SELECT COUNT(*) FROM universities;"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"❌ Failed to count universities: {e}")
            return 0
    
    def get_university_students_by_univ_id(self, univ_id:int):
        """Fetch all students of a university by university ID"""
        try:
            query = f"""
            SELECT student_id, name, email, roll_no, dob, passed_out_year, created_at
            FROM students
            WHERE univ_id = {univ_id};
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch students: {e}")
            return []
        
    def get_university_students_by_private_key(self, private_key:str):
        """Fetch all students of a university by university private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"""
            SELECT s.student_id, s.name, s.email, s.roll_no, s.dob, s.passed_out_year, s.created_at
            FROM students s JOIN universities u ON s.univ_id = u.univ_id
            WHERE u.private_key = '{hash_private_key}';
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch students: {e}")
            return []

    def get_university_website_by_private_key(self, private_key:str) -> str:
        """Fetch a university's website by private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"SELECT university_website FROM universities WHERE private_key = '{hash_private_key}';"
            result = self.run_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"❌ Failed to fetch university website: {e}")
            return None

    def get_university_affiliate_colleges_by_univ_id(self, univ_id:int):
        """Fetch all affiliate colleges of a university by university ID"""
        try:
            query = f"""
            SELECT clg_code, clg_name, clg_address, clg_web, created_at
            FROM affiliate_colleges
            WHERE univ_id = {univ_id};
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch affiliate colleges: {e}")
            return []
    
    def get_university_affiliate_colleges_by_private_key(self, private_key:str):    
        """Fetch all affiliate colleges of a university by university private key"""
        try:
            hash_private_key = bcrypt.hashpw(private_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = f"""
            SELECT ac.clg_code, ac.clg_name, ac.clg_address, ac.clg_web, ac.created_at
            FROM affiliate_colleges ac JOIN universities u ON ac.univ_id = u.univ_id
            WHERE u.private_key = '{hash_private_key}';
            """
            result = self.run_query(query, fetch_all=True)
            return result
        except Exception as e:
            logger.error(f"❌ Failed to fetch affiliate colleges: {e}")
            return []
    
    # ================================ End of University Management ===================================

    # ===============================  ===================================



    def close(self):
        """Close cursor and connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔒 Connection closed.")

    
if __name__ == "__main__":
    db = SupabaseDB()
    db.connect()
    
    # Example query
    result = db.run_query("SELECT NOW();", fetch_one=True)
    print("Current Time:", result)
    
    # Insert example
    # db.run_query("INSERT INTO users (name, email) VALUES ('Praveen', 'praveen@example.com');")
    
    db.close()
