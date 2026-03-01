-- ============================================================
--  UNIVERSITIES  –  multi-tenant root
-- ============================================================
CREATE TABLE universities (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(256) NOT NULL,
    slug VARCHAR(64) UNIQUE NOT NULL,          -- e.g. "vit-vellore"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
--  STUDENTS  –  scaled for 1 lakh+ per university
-- ============================================================
CREATE TABLE students (
    id VARCHAR(36) PRIMARY KEY,
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id),
    external_id VARCHAR(64) NOT NULL,          -- register number / roll number
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    email VARCHAR(128) NOT NULL,
    batch VARCHAR(16),                         -- e.g. "2023", "2024"
    department VARCHAR(128),                   -- e.g. "CSE", "ECE"
    section VARCHAR(16),                       -- e.g. "A", "B"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (university_id, external_id)
);

-- Partition-friendly indexes for large student tables
CREATE INDEX idx_students_university ON students (university_id);
CREATE INDEX idx_students_batch_dept ON students (university_id, batch, department);
CREATE INDEX idx_students_email ON students (email);

-- ============================================================
--  COURSES  –  per-university course catalog
-- ============================================================
CREATE TABLE courses (
    id VARCHAR(36) PRIMARY KEY,
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id),
    code VARCHAR(32) NOT NULL,                 -- e.g. "CS101"
    name VARCHAR(256) NOT NULL,
    semester VARCHAR(16),
    batch VARCHAR(16),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (university_id, code, semester, batch)
);
CREATE INDEX idx_courses_university ON courses (university_id);

-- ============================================================
--  ENROLLMENTS  –  many-to-many students ↔ courses
-- ============================================================
CREATE TABLE enrollments (
    id VARCHAR(36) PRIMARY KEY,
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id),
    student_id VARCHAR(36) NOT NULL REFERENCES students(id),
    course_id VARCHAR(36) NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (student_id, course_id)
);
CREATE INDEX idx_enrollments_course ON enrollments (course_id);
CREATE INDEX idx_enrollments_uni_student ON enrollments (university_id, student_id);

-- ============================================================
--  RISK PREDICTIONS  –  partitioned by university for speed
-- ============================================================
CREATE TABLE risk_predictions (
    id VARCHAR(36) PRIMARY KEY,
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id),
    student_id VARCHAR(36) REFERENCES students(id),
    course_id VARCHAR(36) REFERENCES courses(id),
    risk_level VARCHAR(16) NOT NULL,           -- low / medium / high / critical
    academic_risk_low NUMERIC,
    academic_risk_medium NUMERIC,
    academic_risk_high NUMERIC,
    dropout_probability NUMERIC,
    recovery_probability NUMERIC,
    model_version VARCHAR(32),                 -- track which model produced this
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_risk_student_course ON risk_predictions (university_id, student_id, course_id);
CREATE INDEX idx_risk_level ON risk_predictions (university_id, risk_level);
CREATE INDEX idx_risk_created ON risk_predictions (created_at DESC);

-- ============================================================
--  NOTIFICATIONS  –  teacher / student alerts
-- ============================================================
CREATE TABLE notifications (
    id VARCHAR(36) PRIMARY KEY,
    university_id VARCHAR(36) NOT NULL REFERENCES universities(id),
    student_id VARCHAR(36) REFERENCES students(id),
    recipient_type VARCHAR(16) NOT NULL,       -- "student" | "teacher"
    recipient_id VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,             -- info / warning / critical
    message TEXT NOT NULL,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_notifications_recipient ON notifications (university_id, recipient_type, recipient_id, read);
CREATE INDEX idx_notifications_created ON notifications (created_at DESC);

-- ============================================================
--  PARTITIONING HINT (PostgreSQL 12+)
--  For 1 lakh+ students, partition risk_predictions by university
-- ============================================================
-- CREATE TABLE risk_predictions (...) PARTITION BY LIST (university_id);
-- CREATE TABLE risk_predictions_uni001 PARTITION OF risk_predictions FOR VALUES IN ('UNI001');
-- CREATE TABLE risk_predictions_uni002 PARTITION OF risk_predictions FOR VALUES IN ('UNI002');

