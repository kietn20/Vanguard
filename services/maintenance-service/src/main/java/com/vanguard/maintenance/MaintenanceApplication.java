package com.vanguard.maintenance;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class MaintenanceApplication {

    public static void main(String[] args) {
        // SpringApplication.run() starts the entire Spring container
        SpringApplication.run(MaintenanceApplication.class, args);
    }
}
