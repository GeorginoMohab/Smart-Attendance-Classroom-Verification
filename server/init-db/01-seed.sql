CREATE TABLE IF NOT EXISTS "Role" (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "User" (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT REFERENCES "Role"(role_id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "Department" (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS "StaffProfile" (
    staff_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES "User"(user_id),
    staff_name VARCHAR(100) NOT NULL,
    staff_type VARCHAR(50) NOT NULL,
    department_id INT REFERENCES "Department"(department_id)
);

CREATE TABLE IF NOT EXISTS "StudentProfile" (
    student_id SERIAL PRIMARY KEY,
    user_id INT UNIQUE REFERENCES "User"(user_id),
    student_code VARCHAR(50) UNIQUE NOT NULL,
    student_name VARCHAR(100) NOT NULL,
    level INT NOT NULL
);

INSERT INTO "Role" (role_id, role_name) VALUES 
(1, 'Admin'), 
(2, 'Lecturer'), 
(3, 'Student')
ON CONFLICT (role_id) DO NOTHING;

INSERT INTO "Department" (department_id, department_name) VALUES 
(1, 'Computer Science')
ON CONFLICT (department_id) DO NOTHING;

INSERT INTO "User" (user_id, email, password_hash, role_id) VALUES 
(1, 'admin@classroom.com', 'hashed_admin123', 1),
(2, 'doctor@classroom.com', 'hashed_doctor123', 2),
(3, 'student@classroom.com', 'hashed_student123', 3)
ON CONFLICT (email) DO NOTHING;

INSERT INTO "StaffProfile" (staff_id, user_id, staff_name, staff_type, department_id) VALUES 
(1, 2, 'Instructor One', 'Lecturer', 1)
ON CONFLICT (staff_id) DO NOTHING;

INSERT INTO "StudentProfile" (student_id, user_id, student_code, student_name, level) VALUES 
(1, 3, 'STD1001', 'Student One', 3)
ON CONFLICT (student_id) DO NOTHING;
