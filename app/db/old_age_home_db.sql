-- ============================================
--   OLD AGE HOME MANAGEMENT SYSTEM
--   PostgreSQL Database Creation Script
-- ============================================

-- Run this first in psql or pgAdmin as superuser:
-- CREATE DATABASE old_age_home_db;
-- \c old_age_home_db

-- ============================================
-- TABLE 1: ADMIN
-- ============================================
CREATE TABLE admin (
    admin_id      SERIAL          PRIMARY KEY,
    name          VARCHAR(100)    NOT NULL,
    email         VARCHAR(100)    NOT NULL UNIQUE,
    password      VARCHAR(255)    NOT NULL,
    phone         VARCHAR(15),
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE 2: RESIDENT (Old Age Person)
-- ============================================
CREATE TABLE resident (
    resident_id       SERIAL          PRIMARY KEY,
    name              VARCHAR(100)    NOT NULL,
    email             VARCHAR(100)    NOT NULL UNIQUE,
    password          VARCHAR(255)    NOT NULL,
    phone             VARCHAR(15),
    dob               DATE,
    gender            VARCHAR(10)     CHECK (gender IN ('Male', 'Female', 'Other')),
    room_number       VARCHAR(10),
    admission_date    DATE            DEFAULT CURRENT_DATE,
    emergency_contact VARCHAR(100),
    status            VARCHAR(10)     DEFAULT 'Active' CHECK (status IN ('Active', 'Inactive')),
    created_at        TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE 3: VISITOR
-- ============================================
CREATE TABLE visitor (
    visitor_id    SERIAL          PRIMARY KEY,
    name          VARCHAR(100)    NOT NULL,
    email         VARCHAR(100)    NOT NULL UNIQUE,
    password      VARCHAR(255)    NOT NULL,
    phone         VARCHAR(15),
    relation      VARCHAR(50),
    created_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE 4: MEDICINE SCHEDULE
-- (Created by resident to track their medicines)
-- ============================================
CREATE TABLE medicine_schedule (
    medicine_id     SERIAL          PRIMARY KEY,
    resident_id     INT             NOT NULL,
    medicine_name   VARCHAR(150)    NOT NULL,
    dosage          VARCHAR(100)    NOT NULL,
    frequency       VARCHAR(30)     NOT NULL
                        CHECK (frequency IN (
                            'Once a day',
                            'Twice a day',
                            'Three times a day',
                            'Weekly',
                            'As needed'
                        )),
    reminder_time   TIME            NOT NULL,
    start_date      DATE            NOT NULL,
    end_date        DATE,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_medicine_resident
        FOREIGN KEY (resident_id)
        REFERENCES resident(resident_id)
        ON DELETE CASCADE
);

-- ============================================
-- TABLE 5: MEDICINE LOG
-- (Tracks whether resident took their medicine)
-- ============================================
CREATE TABLE medicine_log (
    log_id          SERIAL          PRIMARY KEY,
    medicine_id     INT             NOT NULL,
    taken_date      DATE            NOT NULL,
    taken_time      TIME,
    is_taken        BOOLEAN         DEFAULT FALSE,
    notes           VARCHAR(255),

    CONSTRAINT fk_log_medicine
        FOREIGN KEY (medicine_id)
        REFERENCES medicine_schedule(medicine_id)
        ON DELETE CASCADE
);

-- ============================================
-- TABLE 6: VISIT REQUEST
-- (Visitor requests to meet a resident)
-- ============================================
CREATE TABLE visit_request (
    request_id          SERIAL          PRIMARY KEY,
    visitor_id          INT             NOT NULL,
    resident_id         INT             NOT NULL,
    requested_datetime  TIMESTAMP       NOT NULL,
    purpose             VARCHAR(255),
    status              VARCHAR(10)     DEFAULT 'Pending'
                            CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    approved_by         INT,
    approved_at         TIMESTAMP,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_request_visitor
        FOREIGN KEY (visitor_id)
        REFERENCES visitor(visitor_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_request_resident
        FOREIGN KEY (resident_id)
        REFERENCES resident(resident_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_request_admin
        FOREIGN KEY (approved_by)
        REFERENCES admin(admin_id)
        ON DELETE SET NULL
);


-- ============================================
-- SAMPLE DATA
-- ============================================

-- Admin
INSERT INTO admin (name, email, password, phone) VALUES
('Super Admin',  'admin@oahome.com',   'admin123', '9000000001'),
('Staff Ramesh', 'ramesh@oahome.com',  'staff123', '9000000002');

-- Residents
INSERT INTO resident (name, email, password, phone, dob, gender, room_number, admission_date, emergency_contact) VALUES
('Suresh Patil',  'suresh@resident.com',  'res123', '9111111111', '1948-03-12', 'Male',   'R-101', '2023-01-10', 'Son: Rajesh 9111111100'),
('Meena Joshi',   'meena@resident.com',   'res123', '9222222222', '1952-07-25', 'Female', 'R-102', '2023-03-05', 'Daughter: Priya 9222222200'),
('Baburao Desai', 'baburao@resident.com', 'res123', '9333333333', '1945-11-01', 'Male',   'R-103', '2022-11-15', 'Son: Vijay 9333333300');

-- Visitors
INSERT INTO visitor (name, email, password, phone, relation) VALUES
('Rajesh Patil', 'rajesh@visitor.com', 'vis123', '9444444441', 'Son'),
('Priya Joshi',  'priya@visitor.com',  'vis123', '9444444442', 'Daughter'),
('Anita Desai',  'anita@visitor.com',  'vis123', '9444444443', 'Daughter-in-law');

-- Medicine Schedules
INSERT INTO medicine_schedule (resident_id, medicine_name, dosage, frequency, reminder_time, start_date, end_date) VALUES
(1, 'Amlodipine',   '5mg',   'Once a day',   '08:00:00', '2024-01-01', '2024-12-31'),
(1, 'Metformin',    '500mg', 'Twice a day',   '08:00:00', '2024-01-01', NULL),
(2, 'Atorvastatin', '10mg',  'Once a day',   '21:00:00', '2024-02-01', NULL),
(3, 'Aspirin',      '75mg',  'Once a day',   '09:00:00', '2023-12-01', NULL),
(3, 'Pantoprazole', '40mg',  'Twice a day',  '07:30:00', '2024-01-15', '2024-06-15');

-- Medicine Logs
INSERT INTO medicine_log (medicine_id, taken_date, taken_time, is_taken, notes) VALUES
(1, '2024-06-01', '08:05:00', TRUE,  NULL),
(1, '2024-06-02', NULL,       FALSE, 'Resident was asleep'),
(1, '2024-06-03', '08:10:00', TRUE,  NULL),
(2, '2024-06-01', '08:00:00', TRUE,  NULL),
(2, '2024-06-01', '20:00:00', TRUE,  NULL),
(3, '2024-06-01', '21:15:00', TRUE,  NULL),
(4, '2024-06-01', '09:05:00', TRUE,  NULL),
(4, '2024-06-02', NULL,       FALSE, 'Forgot morning dose');

-- Visit Requests
INSERT INTO visit_request (visitor_id, resident_id, requested_datetime, purpose, status, approved_by, approved_at) VALUES
(1, 1, '2024-06-05 10:00:00', 'Weekly family visit',       'Approved', 1, '2024-06-04 15:30:00'),
(2, 2, '2024-06-06 14:00:00', 'Birthday celebration',      'Approved', 1, '2024-06-05 10:00:00'),
(3, 3, '2024-06-07 11:00:00', 'Routine check-in',          'Pending',  NULL, NULL),
(1, 1, '2024-06-10 10:00:00', 'Bringing home-cooked food', 'Rejected', 2, '2024-06-09 09:00:00');


-- ============================================
-- USEFUL QUERIES
-- ============================================

-- 1. Today's medicine reminders for all active residents
-- SELECT r.name AS resident, ms.medicine_name, ms.dosage, ms.reminder_time
-- FROM medicine_schedule ms
-- JOIN resident r ON r.resident_id = ms.resident_id
-- WHERE ms.is_active = TRUE
-- ORDER BY ms.reminder_time;

-- 2. All pending visit requests
-- SELECT vr.request_id, v.name AS visitor, r.name AS resident,
--        vr.requested_datetime, vr.purpose, vr.status
-- FROM visit_request vr
-- JOIN visitor v ON v.visitor_id = vr.visitor_id
-- JOIN resident r ON r.resident_id = vr.resident_id
-- WHERE vr.status = 'Pending'
-- ORDER BY vr.requested_datetime;

-- 3. Medicine compliance report for a resident (resident_id = 1)
-- SELECT ms.medicine_name, ml.taken_date, ml.is_taken, ml.notes
-- FROM medicine_log ml
-- JOIN medicine_schedule ms ON ms.medicine_id = ml.medicine_id
-- WHERE ms.resident_id = 1
-- ORDER BY ml.taken_date DESC;

-- 4. Upcoming approved visits
-- SELECT v.name AS visitor, r.name AS resident,
--        vr.requested_datetime, vr.purpose
-- FROM visit_request vr
-- JOIN visitor  v ON v.visitor_id  = vr.visitor_id
-- JOIN resident r ON r.resident_id = vr.resident_id
-- WHERE vr.status = 'Approved'
--   AND vr.requested_datetime >= NOW()
-- ORDER BY vr.requested_datetime;

-- 5. Count of missed medicines per resident
-- SELECT r.name AS resident, COUNT(*) AS missed_count
-- FROM medicine_log ml
-- JOIN medicine_schedule ms ON ms.medicine_id = ml.medicine_id
-- JOIN resident r ON r.resident_id = ms.resident_id
-- WHERE ml.is_taken = FALSE
-- GROUP BY r.name
-- ORDER BY missed_count DESC;