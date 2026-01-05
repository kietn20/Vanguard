INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'HYDRAULIC_PUMP_001', 'Hydraulic Pump Model A', 'High-pressure hydraulic pump for press machines', 'HYDRAULIC', 15, 10, 450.00, 'WAREHOUSE-A-SHELF-12', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'HYDRAULIC_PUMP_001');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'BEARING_6205', 'Ball Bearing 6205', 'Standard ball bearing for rotating equipment', 'MECHANICAL', 50, 20, 12.50, 'WAREHOUSE-A-SHELF-03', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'BEARING_6205');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'SERVO_MOTOR_500W', '500W Servo Motor', 'Precision servo motor for CNC machines', 'ELECTRICAL', 8, 5, 780.00, 'WAREHOUSE-B-SHELF-07', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'SERVO_MOTOR_500W');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'PRESSURE_SENSOR_PSI', 'Pressure Sensor 0-5000 PSI', 'High-accuracy pressure sensor', 'SENSORS', 25, 15, 125.00, 'WAREHOUSE-A-SHELF-18', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'PRESSURE_SENSOR_PSI');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'WELDING_TIP_T15', 'Welding Tip Type 15', 'Consumable welding tip for robotic welders', 'WELDING', 100, 50, 8.75, 'WAREHOUSE-C-SHELF-02', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'WELDING_TIP_T15');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'CNC_TOOL_BIT_HSS', 'HSS End Mill 12mm', 'High-speed steel end mill for CNC machining', 'CUTTING_TOOLS', 35, 25, 22.50, 'WAREHOUSE-B-SHELF-14', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'CNC_TOOL_BIT_HSS');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'CONVEYOR_BELT_10M', '10m Conveyor Belt', 'Replacement belt for assembly line conveyors', 'MECHANICAL', 3, 5, 1200.00, 'WAREHOUSE-D-STORAGE', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'CONVEYOR_BELT_10M');

INSERT INTO parts (part_number, name, description, category, quantity, minimum_quantity, unit_price, location, created_at, updated_at)
SELECT 'PNEUMATIC_VALVE_24V', '24V Pneumatic Valve', '3-way pneumatic control valve', 'PNEUMATIC', 18, 10, 65.00, 'WAREHOUSE-A-SHELF-09', NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM parts WHERE part_number = 'PNEUMATIC_VALVE_24V');
