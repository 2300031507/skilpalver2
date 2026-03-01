-- ============================================================
--  SAMPLE DATA  –  matches the new multi-tenant schema
-- ============================================================

-- Universities
INSERT INTO universities (id, name, slug) VALUES
    ('UNI001', 'VIT Vellore',          'vit-vellore'),
    ('UNI002', 'IIIT Hyderabad',       'iiit-hyderabad');

-- Courses
INSERT INTO courses (id, university_id, code, name, semester, batch) VALUES
    ('C001', 'UNI001', 'CS101', 'Data Structures',           '2025-1', '2023'),
    ('C002', 'UNI001', 'CS201', 'Machine Learning',          '2025-1', '2023'),
    ('C003', 'UNI002', 'CS301', 'Algorithms',                '2025-1', '2023');

-- Students (small sample — in production this table holds 1 lakh+)
INSERT INTO students (id, university_id, external_id, first_name, last_name, email, batch, department, section) VALUES
    ('11111111-1111-1111-1111-111111111111', 'UNI001', 'S001', 'Alice', 'Smith',   'alice@vit.edu',    '2023', 'CSE', 'A'),
    ('22222222-2222-2222-2222-222222222222', 'UNI001', 'S002', 'Bob',   'Jones',   'bob@vit.edu',      '2023', 'CSE', 'A'),
    ('33333333-3333-3333-3333-333333333333', 'UNI002', 'S003', 'Carol', 'Lee',     'carol@iiith.edu',  '2023', 'CSE', 'B');

-- Enrollments
INSERT INTO enrollments (id, university_id, student_id, course_id) VALUES
    ('E001', 'UNI001', '11111111-1111-1111-1111-111111111111', 'C001'),
    ('E002', 'UNI001', '11111111-1111-1111-1111-111111111111', 'C002'),
    ('E003', 'UNI001', '22222222-2222-2222-2222-222222222222', 'C001'),
    ('E004', 'UNI002', '33333333-3333-3333-3333-333333333333', 'C003');

-- Risk predictions
INSERT INTO risk_predictions (
    id, university_id, student_id, course_id,
    risk_level, academic_risk_low, academic_risk_medium, academic_risk_high,
    dropout_probability, recovery_probability, model_version
) VALUES
    ('aaaaaaa1-1111-1111-1111-111111111111',
     'UNI001', '11111111-1111-1111-1111-111111111111', 'C001',
     'medium', 0.2, 0.5, 0.3, 0.35, 0.6, 'v1.0');

